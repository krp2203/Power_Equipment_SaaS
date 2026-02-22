from flask import Blueprint, request, jsonify, g
from datetime import datetime
from app.core.extensions import db
from app.core.models import Organization, PartInventory
from app.core.multitenancy import global_tenant_bypass
from functools import wraps
from . import api_bp

def bridge_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        bridge_key = request.headers.get('X-Bridge-Key')
        print(f"DEBUG: Bridge auth attempt - Key received: {bridge_key[:20] if bridge_key else 'None'}...")
        print(f"DEBUG: Current g.current_org_id before bypass: {g.get('current_org_id')}")
        
        if not bridge_key:
            print("DEBUG: No bridge key in headers")
            return jsonify({"error": "Missing X-Bridge-Key header"}), 401
            
        # Use context manager to bypass tenant filtering during key lookup
        with global_tenant_bypass():
            print("DEBUG: Inside global_tenant_bypass, querying for org...")
            org = Organization.query.filter_by(pos_bridge_key=bridge_key).first()
            print(f"DEBUG: Query result: {org.name if org else 'None'}")
        
        if not org:
            print(f"DEBUG: No organization found with bridge key: {bridge_key[:20]}...")
            return jsonify({"error": "Invalid Bridge Key"}), 403
            
        # Set the authenticated organization as the current tenant for the remainder of the request
        g.bridge_org = org
        g.current_org = org
        g.current_org_id = org.id
        print(f"DEBUG: Bridge auth successful for org: {org.name} (ID: {org.id})")
        
        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/bridge/heartbeat', methods=['POST'])
@bridge_key_required
def bridge_heartbeat():
    """
    Bridge Check-in. Updates last_bridge_heartbeat.
    Input: Empty POST or optional metadata (version, etc.)
    """
    org = g.bridge_org
    org.last_bridge_heartbeat = datetime.utcnow()
    db.session.commit()
    return jsonify({"status": "ok", "timestamp": org.last_bridge_heartbeat.isoformat()})

@api_bp.route('/bridge/parts-update', methods=['POST'])
@bridge_key_required
def bridge_parts_update():
    """
    Sync Owned Inventory.
    Input: JSON list [{ "part_number": "...", "qty": 1, "desc": "...", "bin": "..." }]
    """
    org = g.bridge_org
    data = request.get_json()
    
    if not isinstance(data, list):
        return jsonify({"error": "Expected a JSON list of parts"}), 400
        
    updated_count = 0
    
    # Optional: Clear existing inventory if this is a 'full sync'
    # For now, we'll assume upsert behavior
    
    for item in data:
        part_number = item.get('part_number')
        manufacturer = item.get('manufacturer')
        qty = item.get('qty', 0)
        desc = item.get('desc')
        bin_loc = item.get('bin')
        
        if not part_number:
            continue
            
        # Search for existing part with matching part_number AND manufacturer
        part = PartInventory.query.filter_by(
            organization_id=org.id, 
            part_number=part_number,
            manufacturer=manufacturer
        ).first()
        
        if part:
            part.stock_on_hand = qty
            part.description = desc or part.description
            part.bin_location = bin_loc or part.bin_location
            part.updated_at = datetime.utcnow()
        else:
            new_part = PartInventory(
                organization_id=org.id,
                part_number=part_number,
                manufacturer=manufacturer,
                stock_on_hand=qty,
                description=desc,
                bin_location=bin_loc
            )
            db.session.add(new_part)
            
        updated_count += 1
        
    org.last_bridge_heartbeat = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        "status": "ok", 
        "updated_records": updated_count,
        "org": org.name
    })
