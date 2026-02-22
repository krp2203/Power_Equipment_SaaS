import requests
from flask import url_for, current_app
from typing import List, Dict, Any, Optional

class FacebookOAuth:
    """
    Handles the Facebook Login for Business OAuth flow.
    Acts as a 'Tech Provider' to manage dealer pages.
    """
    
    auth_url = "https://www.facebook.com/v21.0/dialog/oauth"
    token_url = "https://graph.facebook.com/v21.0/oauth/access_token"
    graph_url = "https://graph.facebook.com/v21.0"
    
    @property
    def client_id(self):
        return current_app.config['FACEBOOK_APP_ID']
        
    @property
    def client_secret(self):
        return current_app.config['FACEBOOK_APP_SECRET']
        
    def get_connect_url(self, callback_url: str, state: str = 'security_token_placeholder') -> str:
        """
        Generates the URL to redirect the dealer to Facebook.
        Requests permissions: pages_show_list, pages_manage_posts, pages_read_engagement.
        """
        params = {
            'client_id': self.client_id,
            'redirect_uri': callback_url,
            'scope': 'pages_show_list,pages_manage_posts,pages_read_engagement',
            'response_type': 'code',
            'state': state
        }
        
        from urllib.parse import urlencode
        return f"{self.auth_url}?{urlencode(params)}"
        
    def exchange_code_for_token(self, code: str, callback_url: str) -> Optional[str]:
        """
        Exchanges the temporary auth code for a short-lived User Access Token.
        """
        params = {
            'client_id': self.client_id,
            'redirect_uri': callback_url,
            'client_secret': self.client_secret,
            'code': code
        }
        
        try:
            resp = requests.get(self.token_url, params=params)
            data = resp.json()
            if 'error' in data:
                current_app.logger.error(f"Facebook Auth Error: {data['error']}")
                return None
            token = data.get('access_token')
            current_app.logger.error(f"DEBUG_OAUTH: Received short_token: {token[:10]}...")
            return token
        except Exception as e:
            current_app.logger.error(f"Facebook Token Exchange Failed: {str(e)}")
            return None

    def get_long_lived_user_token(self, short_lived_token: str) -> Optional[str]:
        """
        Exchanges a short-lived user token (1 hour) for a long-lived one (60 days).
        Critical for keeping the connection alive without frequent relogins.
        """
        params = {
            'grant_type': 'fb_exchange_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'fb_exchange_token': short_lived_token
        }
        
        try:
            resp = requests.get(self.token_url, params=params)
            data = resp.json()
            token = data.get('access_token')
            current_app.logger.error(f"DEBUG_OAUTH: Received long_token: {token[:10]}..." if token else "DEBUG_OAUTH: No long_token in response")
            return token
        except Exception as e:
            current_app.logger.error(f"Long-lived Token Exchange Failed: {str(e)}")
            return None

    def get_managed_pages(self, user_token: str) -> List[Dict[str, Any]]:
        """
        Fetches a list of Facebook Pages the user manages.
        Returns [{'name': 'Page Name', 'id': '123', 'access_token': 'PAGE_TOKEN', ...}]
        """
        try:
            url = f"{self.graph_url}/me/accounts"
            params = {
                'access_token': user_token,
                'fields': 'name,id,access_token,category',
                'limit': 100
            }
            
            all_pages = []
            # Fetch Pages
            while True:
                resp = requests.get(url, params=params)
                data = resp.json()
                
                if 'data' in data:
                    all_pages.extend(data['data'])
                
                if 'paging' in data and 'next' in data['paging']:
                    url = data['paging']['next']
                    params = {} 
                else:
                    break
                    
            # FALLBACK: If no pages found via /me/accounts, try fetching from debug_token granular scopes
            if not all_pages:
                current_app.logger.info("Facebook OAuth: No pages in /me/accounts, trying fallback granular scopes")
                app_token = f"{self.client_id}|{self.client_secret}"
                debug_url = f"{self.graph_url}/debug_token"
                debug_resp = requests.get(debug_url, params={'input_token': user_token, 'access_token': app_token})
                debug_data = debug_resp.json().get('data', {})
                
                target_ids = []
                for gs in debug_data.get('granular_scopes', []):
                    if gs.get('scope') == 'pages_show_list':
                        target_ids.extend(gs.get('target_ids', []))
                
                for page_id in set(target_ids):
                    page_url = f"{self.graph_url}/{page_id}"
                    page_params = {
                        'access_token': user_token,
                        'fields': 'name,id,access_token,category'
                    }
                    p_resp = requests.get(page_url, params=page_params)
                    p_data = p_resp.json()
                    if 'id' in p_data and 'access_token' in p_data:
                        all_pages.append(p_data)

            return all_pages
        except Exception as e:
            import traceback
            current_app.logger.error(f"Failed to fetch pages: {str(e)}\n{traceback.format_exc()}")
            return []
