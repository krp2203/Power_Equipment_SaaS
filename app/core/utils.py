import re
from flask import url_for

def render_note_html(note_text, all_users):
    """
    Renders note text to HTML, handling @mentions.
    """
    if not note_text:
        return ""

    # Escape HTML first for security (if not already handled by Jinja autoescape context)
    # But since we are returning safe HTML, we should assume input is raw text.
    # We will do simple replacements.

    # 1. Handle @mentions
    try:
        if all_users:
            for user in all_users:
                if not user.username: continue
                pattern = f"@{re.escape(user.username)}(?![a-zA-Z0-9])"
                replacement = f'<span class="badge bg-info text-dark">@{user.username}</span>'
                note_text = re.sub(pattern, replacement, note_text)
    except Exception as e:
        print(f"Error in render_note_html: {e}", flush=True)
        # Return original text on error (fallback)
        pass

    # 2. Convert newlines to <br>
    note_text = note_text.replace('\n', '<br>')

    return note_text
