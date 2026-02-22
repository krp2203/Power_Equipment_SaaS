from flask import jsonify, request, g
from flask_login import login_required
from app.modules.service_bulletins import service_bulletins_bp
from app.core.models import ServiceBulletinModel
from .utils import is_serial_in_range

@service_bulletins_bp.route('/api/bulletins/<int:sb_id>/check_serial')
@login_required
def check_serial_api(sb_id):
    serial = request.args.get('serial', '').strip().upper()
    if not serial:
        return jsonify({'error': 'Serial number required'}), 400
        
    # Find matching model for this SB
    models = ServiceBulletinModel.query.filter_by(bulletin_id=sb_id).all()
    
    for model in models:
        if is_serial_in_range(serial, model.serial_start, model.serial_end):
            return jsonify({
                'match': True,
                'model_name': model.model_name,
                'range': f"{model.serial_start} - {model.serial_end}"
            })
            
    return jsonify({'match': False})
