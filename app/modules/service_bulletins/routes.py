from flask import render_template, request, redirect, url_for, flash, current_app, send_from_directory, g, abort
from flask_login import login_required, current_user
from app.modules.service_bulletins import service_bulletins_bp
import os
from werkzeug.utils import secure_filename
from datetime import datetime

from app.core.models import db, ServiceBulletin, ServiceBulletinModel, ServiceBulletinCompletion, User
from .parser import parse_bulletin_pdf
from .utils import is_serial_in_range
from . import api_routes # Register API routes
import re

@service_bulletins_bp.route('/service_bulletins')
@login_required
def index():
    serial_number = request.args.get('serial')
    bulletins_query = ServiceBulletin.query.order_by(ServiceBulletin.sb_number.desc())
    bulletins = bulletins_query.all()
    
    applicable_ids = set()
    completion_map = {}
    
    if serial_number:
        serial_number = serial_number.strip().upper()
        # 1. Find Applicable Bulletins
        for sb in bulletins:
            for model in sb.affected_models:
                if is_serial_in_range(serial_number, model.serial_start, model.serial_end):
                    applicable_ids.add(sb.id)
                    break 

        # 2. Find Existing Completions
        completions = ServiceBulletinCompletion.query.filter_by(
            organization_id=g.current_org_id, 
            serial_number=serial_number
        ).all()
        
        for c in completions:
            completion_map[c.bulletin_id] = c

    return render_template('service_bulletins/index.html', 
                           bulletins=bulletins,
                           serial_number=serial_number,
                           applicable_ids=applicable_ids,
                           completion_map=completion_map)

@service_bulletins_bp.route('/service_bulletins/check', methods=['GET', 'POST'])
@login_required
def check():
    # Keep route but redirect to new consolidated index
    serial_number = request.args.get('serial') or request.form.get('serial_number')
    if serial_number:
         return redirect(url_for('service_bulletins.index', serial=serial_number))
    return redirect(url_for('service_bulletins.index'))



@service_bulletins_bp.route('/service_bulletins/complete/<int:sb_id>', methods=['GET', 'POST'])
@login_required
def complete(sb_id):
    current_app.logger.info(f"Accessing complete route for SB {sb_id}")
    sb = ServiceBulletin.query.get_or_404(sb_id)
    
    if request.method == 'POST':
        serials_raw = request.form.get('serial_numbers') or request.form.get('serial_number')
        notes = request.form.get('notes')
        model_name = request.form.get('model_name')
        next_page = request.args.get('next')

        current_app.logger.info(f"POST request to complete SB {sb_id}. Serials: {serials_raw}, Model: {model_name}")

        if not serials_raw:
            flash('At least one serial number is required.', 'danger')
            return redirect(url_for('service_bulletins.complete', sb_id=sb_id))

        # Support bulk: split by comma or newline
        import re
        serial_list = [s.strip().upper() for s in re.split(r'[,\n\r]+', serials_raw) if s.strip()]
        
        current_app.logger.info(f"Processed serial list: {serial_list}")

        count = 0
        already_done = []
        
        try:
            for serial in serial_list:
                current_app.logger.debug(f"Checking existence for serial {serial}")
                exists = ServiceBulletinCompletion.query.filter_by(
                    organization_id=g.current_org_id,
                    bulletin_id=sb_id,
                    serial_number=serial
                ).first()
                
                if exists:
                    current_app.logger.info(f"Bulletin already completed for serial {serial}")
                    already_done.append(serial)
                    continue
                    
                current_app.logger.info(f"Creating completion for serial {serial}")
                completion = ServiceBulletinCompletion(
                    organization_id=g.current_org_id,
                    bulletin_id=sb_id,
                    serial_number=serial,
                    model_name=model_name,
                    user_id=current_user.id,
                    completion_date=datetime.now(),
                    notes=notes,
                    status='Completed'
                )
                db.session.add(completion)
                count += 1
                
            current_app.logger.info(f"Committing {count} completions to database")
            db.session.commit()
            current_app.logger.info("Database commit successful")
        except Exception as e:
            current_app.logger.error(f"Error during completion recording: {e}", exc_info=True)
            db.session.rollback()
            flash(f"Error recording completion: {e}", 'danger')
            return redirect(url_for('service_bulletins.complete', sb_id=sb_id))
        
        current_app.logger.info("Entering post-commit block")
        if count > 0:
            current_app.logger.info(f"Flashing success for {count} completions")
            flash(f'Successfully recorded {count} completion(s).', 'success')
            current_app.logger.info("Success flash call done")
        if already_done:
            current_app.logger.info(f"Flashing warning for {len(already_done)} existing")
            flash(f'Bulletins already completed for: {", ".join(already_done)}', 'warning')
            current_app.logger.info("Warning flash call done")

        if next_page:
            current_app.logger.info(f"Redirecting to next_page: {next_page}")
            return redirect(next_page)
        
        current_app.logger.info(f"Redirecting to view for SB {sb_id}")
        return redirect(url_for('service_bulletins.view', sb_id=sb_id))

    return render_template('service_bulletins/complete_form.html', sb=sb)


@service_bulletins_bp.route('/service_bulletins/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
            
        file = request.files['pdf_file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        if file and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'bulletins', str(g.current_org_id))
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            # Default values if parsing fails or is disabled
            sb_data = {
                'sb_number': "PENDING-" + datetime.now().strftime('%M%S'),
                'issue_date': datetime.now().date(),
                'title': filename,
                'description': '',
                'warranty_code': '',
                'labor_hours': '',
                'required_parts': '[]',
                'models': []
            }

            # Attempt Auto-Parse
            parsing_error = None
            if 'auto_parse' in request.form:
                try:
                    parsed_data = parse_bulletin_pdf(file_path)
                    # Merge parsed data, preferring parsed over default
                    for key, val in parsed_data.items():
                        if val: sb_data[key] = val
                except Exception as e:
                    parsing_error = f"Parsing failed: {e}. File saved, please edit details manually."
                    print(f"PDF Parse Error: {e}", flush=True)

            # Create Record
            try:
                new_sb = ServiceBulletin(
                    organization_id=g.current_org_id,
                    sb_number=sb_data['sb_number'],
                    issue_date=sb_data['issue_date'],
                    title=sb_data['title'],
                    description=sb_data['description'],
                    pdf_filename=filename,
                    pdf_original_name=file.filename,
                    warranty_code=sb_data['warranty_code'],
                    labor_hours=sb_data['labor_hours'],
                    required_parts=sb_data['required_parts']
                )
                db.session.add(new_sb)
                db.session.flush() # Get ID

                # Add Models
                for model in sb_data['models']:
                    new_model = ServiceBulletinModel(
                        organization_id=g.current_org_id,
                        bulletin_id=new_sb.id,
                        model_name=model['model'],
                        serial_start=model['serial_start'],
                        serial_end=model['serial_end']
                    )
                    db.session.add(new_model)

                db.session.commit()
                
                msg = 'Bulletin uploaded successfully.'
                if parsing_error: msg += f" {parsing_error}"
                flash(msg, 'success' if not parsing_error else 'warning')
                
                return redirect(url_for('service_bulletins.view', sb_id=new_sb.id))
                
            except Exception as e:
                db.session.rollback()
                flash(f"Database Error: {e}", 'danger')
                return redirect(request.url)
            
    return render_template('service_bulletins/upload.html')

@service_bulletins_bp.route('/service_bulletins/<int:sb_id>')
@login_required
def view(sb_id):
    sb = ServiceBulletin.query.get_or_404(sb_id)
    completions = ServiceBulletinCompletion.query.filter_by(
        organization_id=g.current_org_id, 
        bulletin_id=sb.id
    ).order_by(ServiceBulletinCompletion.completion_date.desc()).all()
    
    return render_template('service_bulletins/detail.html', sb=sb, completions=completions)

@service_bulletins_bp.route('/service_bulletins/delete/<int:sb_id>', methods=['POST'])
@login_required
def delete(sb_id):
    current_app.logger.info(f"Deleting bulletin {sb_id}")
    sb = ServiceBulletin.query.get_or_404(sb_id)
    if sb.organization_id != g.current_org_id:
        current_app.logger.warning(f"Unauthorized delete attempt for SB {sb_id} by user {current_user.id}")
        abort(403)
        
    try:
        # Delete file
        if sb.pdf_filename:
             file_path = os.path.join(current_app.root_path, 'static', 'uploads', 'bulletins', str(g.current_org_id), sb.pdf_filename)
             current_app.logger.info(f"Removing file: {file_path}")
             if os.path.exists(file_path):
                 os.remove(file_path)

        current_app.logger.info("Deleting record from database")
        db.session.delete(sb)
        db.session.commit()
        current_app.logger.info("Database commit successful")
        flash('Service Bulletin deleted successfully.', 'success')
    except Exception as e:
        current_app.logger.error(f"Error deleting bulletin {sb_id}: {e}", exc_info=True)
        db.session.rollback()
        flash(f'Error deleting bulletin: {e}', 'danger')

    current_app.logger.info("Redirecting to index")
    return redirect(url_for('service_bulletins.index'))
