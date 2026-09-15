"""
Marketing tasks module for async posting to Facebook, Instagram, and other platforms.
"""
from celery import shared_task
from datetime import datetime
from app.core.extensions import db
from app.core.models import FacebookPost, MediaContent, Organization, ScheduledPost
from app.integrations.facebook import get_facebook_service
from flask import current_app


def make_absolute_url(url, org_slug):
    if url and isinstance(url, str) and url.startswith('/'):
        # Default to production domain for social media access
        base = f"{org_slug}.bentcrankshaft.com" if org_slug and org_slug != 'demo' else "demo.bentcrankshaft.com"
        return f"https://{base}{url}"
    return url


def get_or_create_scheduled_post(media_content, destination, scheduled_time):
    """
    Finds (or creates) the tracking row for one destination of a MediaContent
    upload. Facebook already got this row - Instagram is unbuilt (post_media_task
    never actually calls an Instagram API) so it's not created for that
    destination. Returns the row so post_media_task can update its status
    when the actual post attempt finishes, instead of the upload route
    guessing "posted" before anything has happened.
    """
    existing = ScheduledPost.query.filter_by(
        media_content_id=media_content.id, destination=destination
    ).first()
    if existing:
        return existing
    sp = ScheduledPost(
        organization_id=media_content.organization_id,
        media_content_id=media_content.id,
        destination=destination,
        scheduled_time=scheduled_time,
        status='pending',
    )
    db.session.add(sp)
    db.session.flush()
    return sp

@shared_task
def post_video_task(org_id, message, media_url, title, fb_post_id):
    try:
        # Get organization and Facebook service
        org = Organization.query.get(org_id)
        if not org:
            raise ValueError(f"Organization {org_id} not found")

        fb_service = get_facebook_service(org)
        if not fb_service:
            raise ValueError(f"Facebook not configured for organization {org_id}")

        # Ensure absolute URL for Facebook
        media_url = make_absolute_url(media_url, org.slug)

        # Post video to Facebook
        success, post_id, error = fb_service.post_video(message, media_url, title)

        # Update the FacebookPost status
        fb_post = FacebookPost.query.get(fb_post_id)
        if fb_post:
            if success:
                fb_post.status = 'posted'
                fb_post.facebook_post_id = post_id
                current_app.logger.info(f"Successfully posted video to Facebook. Post ID: {post_id}")
            else:
                fb_post.status = 'failed'
                current_app.logger.error(f"Failed to post video: {error}")
            db.session.commit()

        return {'success': success, 'post_id': post_id, 'error': error}
    except Exception as e:
        current_app.logger.error(f"Error in post_video_task: {str(e)}")
        if fb_post_id:
            try:
                fb_post = FacebookPost.query.get(fb_post_id)
                if fb_post:
                    fb_post.status = 'failed'
                    db.session.commit()
            except:
                pass
        return {'success': False, 'error': str(e)}


@shared_task
def post_media_task(org_id, message, media_url, title, media_content_id, post_to_instagram=False,
                     media_type='image', scheduled_post_id=None):
    """
    Async task to post media to Facebook. `post_to_instagram` is accepted for
    forward-compat but currently does nothing - there's no Instagram API
    integration built yet (see app/integrations/facebook.py), so the
    Instagram checkbox is disabled in the upload UI rather than implying
    this posts there too.
    """
    def _update_tracking(status, post_id=None, error=None):
        """Only flips status once the API call has actually returned -
        never optimistically beforehand (that's what made a stuck worker
        indistinguishable from a successful post in the data)."""
        media = MediaContent.query.get(media_content_id)
        if media:
            media.status = status
        if scheduled_post_id:
            sp = db.session.get(ScheduledPost, scheduled_post_id)
            if sp:
                sp.status = status
                sp.posted_time = datetime.utcnow()
                sp.facebook_post_id = post_id
                sp.error_message = error
        db.session.commit()

    try:
        # Get organization and Facebook service
        org = Organization.query.get(org_id)
        if not org:
            raise ValueError(f"Organization {org_id} not found")

        fb_service = get_facebook_service(org)
        if not fb_service:
            raise ValueError(f"Facebook not configured for organization {org_id}")

        # Post to Facebook based on media type
        success = False
        post_id = None
        error = None

        # Ensure absolute URL for Facebook/Instagram
        media_url = make_absolute_url(media_url, org.slug)

        if media_type == 'video':
            success, post_id, error = fb_service.post_video(message, media_url, title)
        else:  # image
            success, post_id, error = fb_service.post_photo(message, media_url)

        if success:
            current_app.logger.info(f"Successfully posted media {media_content_id} to Facebook. Post ID: {post_id}")
        else:
            current_app.logger.error(f"Failed to post media {media_content_id}: {error}")
        _update_tracking('posted' if success else 'failed', post_id=post_id, error=error)

        return {'success': success, 'media_id': media_content_id, 'post_id': post_id, 'error': error}
    except Exception as e:
        current_app.logger.error(f"Error in post_media_task: {str(e)}")
        if media_content_id:
            try:
                _update_tracking('failed', error=str(e))
            except Exception:
                pass
        return {'success': False, 'error': str(e)}

@shared_task
def process_scheduled_posts():
    """
    Periodic task to check for scheduled posts that are due and post them.
    This should be called every minute via Celery Beat.
    """
    try:
        current_app.logger.info("Processing scheduled posts...")

        # Find all scheduled posts where scheduled_post_time <= now
        now = datetime.utcnow()
        due_posts = MediaContent.query.filter(
            MediaContent.status == 'scheduled',
            MediaContent.scheduled_post_time <= now
        ).all()

        current_app.logger.info(f"Found {len(due_posts)} posts due for posting")

        posted_count = 0
        for media in due_posts:
            try:
                # Check if organization exists and has Facebook configured
                org = Organization.query.get(media.organization_id)
                if not org:
                    current_app.logger.warning(f"Organization {media.organization_id} not found for media {media.id}")
                    continue

                fb_configured = bool(org.facebook_page_id and org.facebook_access_token)

                # Build message
                message = f"{media.title}"
                if media.description:
                    message += f"\n\n{media.description}"

                # Post to Facebook if enabled
                queued_social = False
                if media.post_to_facebook and fb_configured:
                    current_app.logger.info(f"Posting media {media.id} to Facebook...")
                    sp = get_or_create_scheduled_post(media, 'facebook', now)
                    post_media_task.delay(
                        org.id,
                        message,
                        media.media_url,
                        media.title,
                        media.id,
                        post_to_instagram=media.post_to_instagram,
                        media_type=media.media_type,
                        scheduled_post_id=sp.id,
                    )
                    posted_count += 1
                    queued_social = True

                # 'posting' if a Facebook post attempt was just queued (the task
                # flips it to 'posted'/'failed' once the API call returns) -
                # otherwise (banner-only, or FB not configured) there's nothing
                # async left to do, so it's genuinely posted now.
                media.status = 'posting' if queued_social else 'posted'
                db.session.commit()
                current_app.logger.info(f"Media {media.id}: {'queued for Facebook posting' if queued_social else 'marked posted (no social destination)'}")

            except Exception as e:
                current_app.logger.error(f"Error processing scheduled post {media.id}: {str(e)}")
                try:
                    media.status = 'failed'
                    db.session.commit()
                except:
                    pass

        current_app.logger.info(f"Processed {posted_count} scheduled posts")
        return {'processed': posted_count}

    except Exception as e:
        current_app.logger.error(f"Error in process_scheduled_posts: {str(e)}")
        return {'success': False, 'error': str(e)}
