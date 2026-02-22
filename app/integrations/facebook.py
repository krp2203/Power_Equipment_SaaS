"""
Facebook Graph API Integration Service

Handles posting to Facebook pages using the Graph API.
"""
import requests
from typing import Optional, Dict, Any
from flask import current_app

class FacebookService:
    """Service for interacting with Facebook Graph API"""
    
    GRAPH_API_VERSION = 'v21.0'
    BASE_URL = f'https://graph.facebook.com/{GRAPH_API_VERSION}'
    
    def __init__(self, page_id: str, access_token: str):
        """
        Initialize Facebook service with page credentials.
        
        Args:
            page_id: Facebook Page ID
            access_token: Page Access Token
        """
        self.page_id = page_id
        self.access_token = access_token
    
    def verify_credentials(self) -> tuple[bool, Optional[str]]:
        """
        Verify that the page ID and access token are valid.
        
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            url = f'{self.BASE_URL}/{self.page_id}'
            params = {
                'fields': 'name,id',
                'access_token': self.access_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                page_name = data.get('name', 'Unknown')
                current_app.logger.info(f"Facebook credentials verified for page: {page_name}")
                return True, None
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                return False, f"Invalid credentials: {error_msg}"
                
        except requests.RequestException as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Verification error: {str(e)}"
    
    def post_text(self, message: str) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Post a text-only message to the Facebook page.
        
        Args:
            message: Text content to post
            
        Returns:
            Tuple of (success: bool, post_id: Optional[str], error: Optional[str])
        """
        try:
            url = f'{self.BASE_URL}/{self.page_id}/feed'
            data = {
                'message': message,
                'access_token': self.access_token
            }
            
            response = requests.post(url, data=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                post_id = result.get('id')
                current_app.logger.info(f"Successfully posted to Facebook. Post ID: {post_id}")
                return True, post_id, None
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                current_app.logger.error(f"Facebook post failed: {error_msg}")
                return False, None, error_msg
                
        except Exception as e:
            current_app.logger.error(f"Exception posting to Facebook: {str(e)}")
            return False, None, str(e)
    
    def post_photo(self, message: str, image_url: str) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Post a photo with caption to the Facebook page.
        
        Args:
            message: Caption/text for the photo
            image_url: Public HTTPS URL of the image
            
        Returns:
            Tuple of (success: bool, post_id: Optional[str], error: Optional[str])
        """
        try:
            url = f'{self.BASE_URL}/{self.page_id}/photos'
            data = {
                'message': message,
                'url': image_url,
                'access_token': self.access_token
            }
            
            response = requests.post(url, data=data, timeout=20)
            
            if response.status_code == 200:
                result = response.json()
                post_id = result.get('id')
                current_app.logger.info(f"Successfully posted photo to Facebook. Post ID: {post_id}")
                return True, post_id, None
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                current_app.logger.error(f"Facebook photo post failed: {error_msg}")
                return False, None, error_msg
                
        except Exception as e:
            current_app.logger.error(f"Exception posting photo to Facebook: {str(e)}")
            return False, None, str(e)
    
    def post_video(self, message: str, video_url: str, title: Optional[str] = None) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Post a video with caption to the Facebook page.
        
        Args:
            message: Caption/description for the video
            video_url: Public HTTPS URL of the video file
            title: Optional title for the video
            
        Returns:
            Tuple of (success: bool, post_id: Optional[str], error: Optional[str])
        """
        try:
            url = f'{self.BASE_URL}/{self.page_id}/videos'
            data = {
                'description': message,
                'file_url': video_url,
                'access_token': self.access_token
            }
            
            if title:
                data['title'] = title
            
            # Video uploads can take longer, increase timeout to 10 minutes
            response = requests.post(url, data=data, timeout=600)
            
            if response.status_code == 200:
                result = response.json()
                post_id = result.get('id')
                current_app.logger.info(f"Successfully posted video to Facebook. Post ID: {post_id}")
                return True, post_id, None
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                current_app.logger.error(f"Facebook video post failed: {error_msg}")
                return False, None, error_msg
                
        except Exception as e:
            current_app.logger.error(f"Exception posting video to Facebook: {str(e)}")
            return False, None, str(e)
    
    def post_unit(self, unit_data: Dict[str, Any]) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Post an inventory unit to Facebook with formatted message.
        
        Args:
            unit_data: Dictionary containing unit information
                - name: Unit name/title
                - description: Unit description
                - price: Unit price
                - image_url: Public URL to unit image
                - dealer_url: URL to dealer's website
                
        Returns:
            Tuple of (success: bool, post_id: Optional[str], error: Optional[str])
        """
        # Format the message
        message = f"🚜 {unit_data['name']}\n\n"
        
        if unit_data.get('description'):
            message += f"{unit_data['description']}\n\n"
        
        if unit_data.get('price') and unit_data['price'] > 0:
            message += f"💰 Price: ${unit_data['price']:,.2f}\n\n"
        else:
            message += "💰 Call for Price\n\n"
        
        if unit_data.get('dealer_url'):
            message += f"🔗 View details: {unit_data['dealer_url']}"
        
        # Post with or without image
        if unit_data.get('image_url'):
            return self.post_photo(message, unit_data['image_url'])
        else:
            return self.post_text(message)


def get_facebook_service(organization) -> Optional[FacebookService]:
    """
    Factory function to create FacebookService from an organization.
    
    Args:
        organization: Organization model instance
        
    Returns:
        FacebookService instance or None if credentials not configured
    """
    if not organization.facebook_page_id or not organization.facebook_access_token:
        return None
    
    return FacebookService(
        page_id=organization.facebook_page_id,
        access_token=organization.facebook_access_token
    )
