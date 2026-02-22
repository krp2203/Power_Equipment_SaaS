from flask import jsonify, g, request
from . import api_bp

@api_bp.route('/v1/site-info', methods=['GET'])
def get_site_info():
    """
    Public (Tenant-Scoped) endpoint for Next.js frontend to bootstrap.
    Returns: Branding, Identity, and Safe Integration Flags.
    """
    org = getattr(g, 'current_org', None)
    if not org:
        return jsonify({"error": "Tenant not found"}), 404
    
    # Marketing Flags (Safe subsets)
    modules = org.modules or {}
    
    response = {
        "identity": {
            "name": org.name,
            "slug": org.slug,
        },
        "is_active": org.is_active,  # Include active status for suspension check
        "theme": org.theme_config or {},
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
    
    # Fetch units marked as inventory and displayable
    # Filter by current organization is automatic via tenancy, but explicit check is good
    if not g.current_org:
        return jsonify([])
        
    units = Unit.query.filter_by(organization_id=g.current_org.id, is_inventory=True, display_on_web=True).all()
    
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
            "price": float(unit.price) if unit.price else 0.0,
            "stock": 1, # Whole goods are usually 1 unique item
            "status": unit.status,
            "image": image_url,
            "description": unit.description,
            "condition": unit.condition or "New"
        })
        
    return jsonify(results)

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
