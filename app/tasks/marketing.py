"""
Marketing tasks module for async posting to Facebook, Instagram, and other platforms.
"""
from celery import shared_task
from datetime import datetime
from app.core.extensions import db
from app.core.models import FacebookPost, MediaContent, Organization
from app.integrations.facebook import get_facebook_service
from flask import current_app


@shared_task
def post_video_task(org_id, message, media_url, title, fb_post_id):
    """
    Async task to post a video to Facebook.
    """
    try:
        # Get organization and Facebook service
        org = Organization.query.get(org_id)
        if not org:
            raise ValueError(f"Organization {org_id} not found")

        fb_service = get_facebook_service(org)
        if not fb_service:
            raise ValueError(f"Facebook not configured for organization {org_id}")

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
def post_media_task(org_id, message, media_url, title, media_content_id, post_to_instagram=False, media_type='image'):
    """
    Async task to post media to Facebook and/or Instagram.
    """
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

        if media_type == 'video':
            success, post_id, error = fb_service.post_video(message, media_url, title)
        else:  # image
            success, post_id, error = fb_service.post_photo(message, media_url)

        # Update the MediaContent status
        media = MediaContent.query.get(media_content_id)
        if media:
            if success:
                media.status = 'posted'
                current_app.logger.info(f"Successfully posted media {media_content_id} to Facebook. Post ID: {post_id}")
            else:
                media.status = 'failed'
                current_app.logger.error(f"Failed to post media {media_content_id}: {error}")
            db.session.commit()

        return {'success': success, 'media_id': media_content_id, 'post_id': post_id, 'error': error}
    except Exception as e:
        current_app.logger.error(f"Error in post_media_task: {str(e)}")
        if media_content_id:
            try:
                media = MediaContent.query.get(media_content_id)
                if media:
                    media.status = 'failed'
                    db.session.commit()
            except:
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
                if media.post_to_facebook and fb_configured:
                    current_app.logger.info(f"Posting media {media.id} to Facebook...")
                    post_media_task.delay(
                        org.id,
                        message,
                        media.media_url,
                        media.title,
                        media.id,
                        post_to_instagram=media.post_to_instagram,
                        media_type=media.media_type
                    )
                    posted_count += 1

                # Update status to posted (or pending if still posting)
                media.status = 'posted'
                db.session.commit()
                current_app.logger.info(f"Marked media {media.id} as posted and queued for social posting")

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
