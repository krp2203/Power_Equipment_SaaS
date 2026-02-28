from flask import jsonify, g, request
from . import api_bp
from app.core.extensions import db

@api_bp.route('/v1/advertisements', methods=['GET'])
def get_advertisements():
    """Public API endpoint for fetching advertisements for carousel"""
    try:
        import sys
        from app.core.models import Organization, MediaContent

        # Get organization from request context or query parameter
        org = g.current_org
        slug = request.args.get('slug') or request.headers.get('X-Dealer-Slug')

        print(f"[ADS-START] g.current_org={org}, slug={slug}", file=sys.stderr)

        # If we have a slug, always use it (even if g.current_org is set to Master fallback)
        org_id = None
        if slug:
            print(f"[ADS-LOOKUP] Looking up org by slug={slug}", file=sys.stderr)
            org = Organization.query.filter_by(slug=slug).first()
            print(f"[ADS-FOUND] Found org: {org}", file=sys.stderr)
            if org:
                org_id = org.id
        elif org and org.id != 1:
            org_id = org.id
        else:
            # If no slug and no valid org context, return empty
            print(f"[ADS-NOORG] No slug and no valid org context, returning empty list", file=sys.stderr)
            return jsonify([]), 200

        if not org_id:
            print(f"[ADS-NOORG] No organization ID found, returning empty list", file=sys.stderr)
            return jsonify([]), 200

        print(f"[ADS-QUERY] Getting ads for org_id={org_id}", file=sys.stderr)

        # Fetch active media marked for banner display using raw SQL to bypass any session issues
        try:
            from sqlalchemy import text
            sql = text("""
                SELECT id, title, description, media_url, thumbnail_url, link_url, media_type
                FROM media_content
                WHERE organization_id = :org_id
                AND post_to_banner = true
                AND status = 'posted'
            """)
            print(f"[ADS-RAW SQL] Executing raw SQL for org_id={org_id}", file=sys.stderr)
            result = db.session.execute(sql, {"org_id": org_id})
            advertisements = result.fetchall()
            print(f"[ADS-RAW-FOUND-{len(advertisements)}] Found {len(advertisements)} advertisements", file=sys.stderr)
        except Exception as qe:
            print(f"[ADS-QUERYERROR] Query failed: {qe}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            advertisements = []

        # Convert to JSON format for carousel
        result = []
        for row in advertisements:
            # Handle both ORM objects and raw SQL tuples
            if hasattr(row, 'id'):
                # ORM object
                ad_id, ad_title, ad_desc, ad_media, ad_thumb, ad_link, ad_type = row.id, row.title, row.description, row.media_url, row.thumbnail_url, row.link_url, row.media_type
            else:
                # Raw SQL tuple
                ad_id, ad_title, ad_desc, ad_media, ad_thumb, ad_link, ad_type = row

            # Smart "either/or" logic: If we're in test environment (.local), rewrite URLs to match
            # Production (.com) keeps original URLs as-is

            # Determine if we're in test environment:
            # 1. Check X-Environment header (set by frontend in test)
            # 2. Check if X-Forwarded-Host contains .local (nginx in test)
            is_test_env = (
                request.headers.get('X-Environment') == 'local' or
                '.local' in (request.headers.get('X-Forwarded-Host') or '')
            )

            if is_test_env and slug:
                # Test environment - use slug to construct proper .local domain
                request_host = f"{slug}.bentcrankshaft.local"

                # Rewrite media URL if it's a full URL
                if ad_media and isinstance(ad_media, str) and ad_media.startswith('http'):
                    path_start = ad_media.find('/static/')
                    if path_start > 0:
                        path = ad_media[path_start:]
                        ad_media = f"{request.scheme}://{request_host}{path}"

                # Rewrite thumbnail URL if it's a full URL
                if ad_thumb and isinstance(ad_thumb, str) and ad_thumb.startswith('http'):
                    path_start = ad_thumb.find('/static/')
                    if path_start > 0:
                        path = ad_thumb[path_start:]
                        ad_thumb = f"{request.scheme}://{request_host}{path}"

            result.append({
                'id': ad_id,
                'title': ad_title,
                'description': ad_desc or '',
                'image': ad_media,  # Use original image (high quality)
                'thumbnail': ad_thumb or ad_media,  # Fallback to original if no thumb
                'link_url': ad_link or '',
                'media_type': ad_type  # Include media type so frontend knows if it's a video
            })

        print(f"[ADS-RETURN] Returning {len(result)} ads in JSON", file=sys.stderr)
        return jsonify(result), 200

    except Exception as e:
        import sys
        print(f"[ADS-ERROR] {str(e)}", file=sys.stderr)
        return jsonify([]), 200

@api_bp.route('/v1/site-info', methods=['GET'])
def get_site_info():
    """
    Public (Tenant-Scoped) endpoint for Next.js frontend to bootstrap.
    Returns: Branding, Identity, and Safe Integration Flags.
    """
    from app.core.models import Organization

    # Try to get org from slug parameter first (for explicit lookups)
    slug = request.args.get('slug') or request.headers.get('X-Dealer-Slug')
    if slug:
        org = Organization.query.filter_by(slug=slug).first()
    else:
        # Fall back to context-based lookup (Host header routing)
        org = getattr(g, 'current_org', None)

    if not org:
        return jsonify({"error": "Tenant not found"}), 404

    # Marketing Flags (Safe subsets)
    modules = org.modules or {}

    # Convert theme config keys to camelCase for frontend
    theme_config = org.theme_config or {}
    converted_theme = {}
    for key, value in theme_config.items():
        # Convert snake_case to camelCase
        camel_key = ''.join(word if i == 0 else word.capitalize() for i, word in enumerate(key.split('_')))

        # Convert relative URLs to absolute URLs for images (logoUrl, brand_logos)
        if camel_key in ('logoUrl', 'brandLogos') and value:
            # Use current request host - all dealers use their own subdomain
            # No special cases needed anymore since bentcrankshaft.com redirects to demo.bentcrankshaft.com
            use_host = request.host

            if camel_key == 'logoUrl' and isinstance(value, str):
                if value.startswith('/'):
                    value = f"{request.scheme}://{use_host}{value}"
            elif camel_key == 'brandLogos' and isinstance(value, dict):
                # Convert each brand logo URL
                converted_logos = {}
                for idx, logo_url in value.items():
                    if logo_url and logo_url.startswith('/'):
                        converted_logos[idx] = f"{request.scheme}://{use_host}{logo_url}"
                    else:
                        converted_logos[idx] = logo_url
                value = converted_logos

        converted_theme[camel_key] = value

    response = {
        "identity": {
            "name": org.name,
            "slug": org.slug,
        },
        "is_active": org.is_active,  # Include active status for suspension check
        "theme": converted_theme,
        "integrations": {
            "ari": {
                "enabled": modules.get('ari', False),
                "dealer_id": org.ari_dealer_id
            },
            "facebook": {
                "enabled": modules.get('facebook', False),
                "page_id": org.facebook_page_id,
                # NEVER return the access_token publically
            },
            "pos": {
                "enabled": (org.pos_provider and org.pos_provider != 'none'),
                "provider": org.pos_provider
                # NEVER return the bridge_key publically
            }
        }
    }

    return jsonify(response)

@api_bp.route('/v1/inventory', methods=['GET'])
def get_inventory():
    from app.core.models import Unit, UnitImage
    
    if not g.current_org:
        return jsonify([])
        
    # Filters
    manufacturer = request.args.get('manufacturer')
    unit_type = request.args.get('type')
    sort = request.args.get('sort', 'id')
    order = request.args.get('order', 'desc')
    
    query = Unit.query.filter_by(organization_id=g.current_org.id, is_inventory=True, display_on_web=True)
    
    if manufacturer:
        query = query.filter(Unit.manufacturer == manufacturer)
    if unit_type:
        query = query.filter(Unit.type == unit_type)
        
    # Sorting
    if sort == 'price':
        query = query.order_by(Unit.price.asc() if order == 'asc' else Unit.price.desc())
    elif sort == 'manufacturer':
        query = query.order_by(Unit.manufacturer.asc() if order == 'asc' else Unit.manufacturer.desc())
    elif sort == 'type':
        query = query.order_by(Unit.type.asc() if order == 'asc' else Unit.type.desc())
    elif sort == 'year':
        query = query.order_by(Unit.year.asc() if order == 'asc' else Unit.year.desc())
    else:
        query = query.order_by(Unit.id.desc())
        
    units = query.all()
    
    results = []
    for unit in units:
        # get primary image
        primary_img = UnitImage.query.filter_by(unit_id=unit.id, is_primary=True).first()
        image_url = primary_img.image_url if primary_img else None
        
        # If no primary, grab first
        if not image_url and unit.images:
            image_url = unit.images[0].image_url

        results.append({
            "id": unit.id,
            "name": f"{unit.manufacturer or ''} {unit.model_number or ''}".strip(),
            "manufacturer": unit.manufacturer,
            "model": unit.model_number,
            "type": unit.type,
            "price": float(unit.price) if unit.price else 0.0,
            "stock": 1,
            "status": unit.status,
            "image": image_url,
            "description": unit.description,
            "condition": unit.condition or "New",
            "year": unit.year
        })
        
    return jsonify(results)

@api_bp.route('/v1/inventory/filters', methods=['GET'])
def get_inventory_filters():
    from app.core.models import Unit
    
    if not g.current_org:
        return jsonify({"manufacturers": [], "types": []})
        
    # Get unique manufacturers and types that are currently in inventory
    manufacturers = db.session.query(Unit.manufacturer).filter_by(
        organization_id=g.current_org.id, 
        is_inventory=True, 
        display_on_web=True
    ).distinct().all()
    
    types = db.session.query(Unit.type).filter_by(
        organization_id=g.current_org.id, 
        is_inventory=True, 
        display_on_web=True
    ).distinct().all()
    
    return jsonify({
        "manufacturers": sorted([m[0] for m in manufacturers if m[0]]),
        "types": sorted([t[0] for t in types if t[0]])
    })

@api_bp.route('/v1/parts', methods=['GET'])
def get_parts():
    from app.core.models import PartInventory
    
    if not g.current_org:
        return jsonify([])
        
    parts = PartInventory.query.filter_by(organization_id=g.current_org.id).order_by(PartInventory.updated_at.desc()).all()
    
    results = []
    for part in parts:
        results.append({
            "id": part.id,
            "part_number": part.part_number,
            "manufacturer": part.manufacturer,
            "description": part.description,
            "stock": part.stock_on_hand,
            "image": part.image_url
        })
        
    return jsonify(results)

@api_bp.route('/v1/service-status', methods=['GET'])
def get_service_status():
    """
    Public endpoint to check the status of a repair by serial number.
    Returns the most recent active case status for the given serial.
    """
    from app.core.models import Unit, Case
    
    serial = request.args.get('serial', '').strip()
    if not serial:
        return jsonify({"error": "Serial number required"}), 400
        
    if not g.current_org:
        return jsonify({"error": "Tenant context missing"}), 404
        
    # Find the unit in this organization
    unit = Unit.query.filter_by(organization_id=g.current_org.id, serial_number=serial).first()
    if not unit:
        return jsonify({"error": "No equipment found with that serial number."}), 404
        
    # Get the latest case for this unit
    latest_case = Case.query.filter_by(unit_id=unit.id).order_by(Case.creation_timestamp.desc()).first()
    
    if not latest_case:
        return jsonify({
            "found": True,
            "manufacturer": unit.manufacturer,
            "model": unit.model_number,
            "status": "No Active Repair",
            "message": "We have your equipment on file, but there are no open service cases."
        })
        
    return jsonify({
        "found": True,
        "manufacturer": unit.manufacturer,
        "model": unit.model_number,
        "case_id": latest_case.id,
        "status": latest_case.status,
        "last_updated": latest_case.follow_up_date.isoformat() if latest_case.follow_up_date else latest_case.creation_timestamp.isoformat(),
        "type": latest_case.case_type
    })

@api_bp.route('/v1/ari/token', methods=['GET'])
def get_ari_token():
    # Mock ARI token
    return jsonify({
        "token": "mock_ari_token_12345",
        "expires_in": 3600
    })

@api_bp.route('/v1/inventory/<int:id>', methods=['GET'])
def get_unit(id):
    from app.core.models import Unit, UnitImage
    
    if not g.current_org:
        return jsonify({"error": "Tenant context missing"}), 404
        
    unit = Unit.query.filter_by(id=id, organization_id=g.current_org.id, is_inventory=True, display_on_web=True).first_or_404()
    
    # get primary image
    primary_img = UnitImage.query.filter_by(unit_id=unit.id, is_primary=True).first()
    image_url = primary_img.image_url if primary_img else None
    
    # If no primary, grab first
    if not image_url and unit.images:
        image_url = unit.images[0].image_url
        
    return jsonify({
        "id": unit.id,
        "name": f"{unit.manufacturer or ''} {unit.model_number or ''}".strip(),
        "price": float(unit.price) if unit.price else 0.0,
        "stock": 1, 
        "status": unit.status,
        "image": image_url,
        "description": unit.description,
        "manufacturer": unit.manufacturer,
        "model_number": unit.model_number,
        "serial_number": unit.serial_number,
        "year": unit.year,
        "condition": unit.condition,
        "unit_hours": unit.unit_hours
    })
