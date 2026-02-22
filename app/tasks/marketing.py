"""
Marketing tasks module for async posting to Facebook, Instagram, and other platforms.
"""
from celery import shared_task
from app.core.extensions import db
from app.core.models import FacebookPost, MediaContent
from flask import current_app


@shared_task
def post_video_task(org_id, message, media_url, title, fb_post_id):
    """
    Async task to post a video to Facebook.
    This is a placeholder that marks the post as completed.
    """
    try:
        # Update the FacebookPost status to 'posted'
        fb_post = FacebookPost.query.get(fb_post_id)
        if fb_post:
            fb_post.status = 'posted'
            db.session.commit()

        current_app.logger.info(f"Video post task completed for FB post {fb_post_id}")
        return {'success': True, 'post_id': fb_post_id}
    except Exception as e:
        current_app.logger.error(f"Error in post_video_task: {str(e)}")
        if fb_post_id:
            fb_post = FacebookPost.query.get(fb_post_id)
            if fb_post:
                fb_post.status = 'failed'
                db.session.commit()
        return {'success': False, 'error': str(e)}


@shared_task
def post_media_task(org_id, message, media_url, title, media_content_id, post_to_instagram=False, media_type='image'):
    """
    Async task to post media to Facebook and/or Instagram.
    This is a placeholder that marks the media as posted.
    """
    try:
        # Update the MediaContent status to 'posted'
        media = MediaContent.query.get(media_content_id)
        if media:
            media.status = 'posted'
            db.session.commit()

        current_app.logger.info(f"Media post task completed for media {media_content_id}")
        return {'success': True, 'media_id': media_content_id}
    except Exception as e:
        current_app.logger.error(f"Error in post_media_task: {str(e)}")
        if media_content_id:
            media = MediaContent.query.get(media_content_id)
            if media:
                media.status = 'failed'
                db.session.commit()
        return {'success': False, 'error': str(e)}
