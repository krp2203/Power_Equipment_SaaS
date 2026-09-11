"""Blueprint-level access guards for optional dealer modules."""

from flask import g, flash, redirect, url_for
from flask_login import current_user


def require_pos_module():
    """`before_request` guard for the Point of Sale, Service Tickets and
    Purchasing blueprints.

    A dealer is a plain marketing site until the master operator switches on the
    Point of Sale system (``organization.modules['pos']``) from the Site Manager.
    Until then these sections are hidden in the nav *and* unreachable by URL.
    """
    # Let the view's own @login_required handle unauthenticated visitors.
    if not current_user.is_authenticated:
        return None

    org = getattr(g, 'current_org', None)
    if org is None:
        return None

    if not (org.modules or {}).get('pos'):
        flash("The Point of Sale system isn't enabled for this account.", "warning")
        return redirect(url_for('marketing.dashboard'))

    return None
