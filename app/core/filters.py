import re
import html
from decimal import Decimal

def html_to_plaintext(html_content):
    """Strips HTML tags to produce plain text."""
    if not html_content:
        return ""
    # Replace <br> and block tags with newlines
    text = re.sub(r'<br\s*/?>', '\n', html_content, flags=re.IGNORECASE)
    text = re.sub(r'</(p|div|h[1-6])>', '\n', text, flags=re.IGNORECASE)
    # Strip all other tags and decode entities
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text) # Decode entities like &nbsp;
    return text.strip()

def currency_filter(value):
    """Formats a numeric value as currency (e.g., $1,234.56)."""
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return value

def hex_to_rgb(hex_color):
    """Converts hex color (e.g. #aabbcc) to comma separated rgb (170, 187, 204) for Bootstrap vars."""
    if not hex_color or not hex_color.startswith('#') or len(hex_color) != 7:
        return "" # Default safe fallback
    try:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        return f"{r}, {g}, {b}"
    except ValueError:
        return ""

from datetime import datetime, timezone

def time_ago_filter(dt):
    """Formats a datetime as a 'time ago' string (e.g., '10 minutes ago')."""
    if not dt:
        return "Never"
    
    # Ensure we are comparing UTC to UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    diff = now - dt
    
    seconds = diff.total_seconds()
    if seconds < 0:
        return "Just now"
    
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    
    minutes = seconds / 60
    if minutes < 60:
        return f"{int(minutes)} minute{'s' if int(minutes) != 1 else ''} ago"
    
    hours = minutes / 60
    if hours < 24:
        return f"{int(hours)} hour{'s' if int(hours) != 1 else ''} ago"
    
    days = hours / 24
    if days < 30:
        return f"{int(days)} day{'s' if int(days) != 1 else ''} ago"
    
    return dt.strftime('%Y-%m-%d')

def is_light_color(hex_color):
    """Returns True if the hex color is considered 'light' (high perceived luminance)."""
    if not hex_color or not hex_color.startswith('#') or len(hex_color) != 7:
        return False
    try:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        
        # Perceived luminance formula
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return luminance > 0.7  # Threshold for "lightness"
    except ValueError:
        return False

def escapejs_filter(value):
    """Escapes strings for use in JavaScript."""
    if not value:
        return ""
    return value.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')

def register_filters(app):
    app.jinja_env.filters['html_to_plaintext'] = html_to_plaintext
    app.jinja_env.filters['plaintext'] = html_to_plaintext # Alias
    app.jinja_env.filters['currency'] = currency_filter
    app.jinja_env.filters['hex_to_rgb'] = hex_to_rgb
    app.jinja_env.filters['is_light'] = is_light_color
    app.jinja_env.filters['time_ago'] = time_ago_filter
    app.jinja_env.filters['escapejs'] = escapejs_filter
