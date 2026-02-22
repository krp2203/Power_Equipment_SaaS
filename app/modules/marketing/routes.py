from flask import render_template, redirect, url_for, flash, request, g, send_file, current_app, session, jsonify
from flask_login import login_required, current_user
import zipfile
import io
import json
import os
from . import marketing_bp
from .forms import MarketingPostForm
from app.integrations.facebook import get_facebook_service
from app.core.extensions import csrf, db
from app.core.models import FacebookPost
# from . import chunk_upload  <-- causing circular import if chunk_upload imports blueprint
import app.modules.marketing.chunk_upload as chunk_upload

@marketing_bp.route('/marketing', methods=['GET', 'POST'])
@login_required
def index():
    # Check if exempt decorator works inside function? No, must be outside.
    # But I can't import csrf at top level easily due to circular imports?
    # app/core/extensions.py has csrf.
    # Let's import at top of file.
    from werkzeug.utils import secure_filename
    import json
    import traceback

    import sys

    try:
        org = g.current_org

        # Check if Facebook module is authorized for this organization
        if not org.modules.get('facebook'):
            flash('The Marketing module is not enabled for your account. Please contact support to activate this feature.', 'warning')
            return redirect(url_for('main.index'))

        form = MarketingPostForm()
        
        # Load Manufacturer Specials
        specials = {}
        try:
            specials_path = os.path.join(current_app.root_path, 'core', 'data', 'manufacturer_specials.json')
            if os.path.exists(specials_path):
                with open(specials_path, 'r') as f:
                    specials = json.load(f)
        except Exception as e:
            current_app.logger.error(f"Error loading specials: {str(e)}")

        if form.validate_on_submit():
            print("DEBUG: Form validated", file=sys.stderr)
            # Check if Facebook is configured
            fb_service = get_facebook_service(org)
            if not fb_service:
                flash('Facebook is not configured. Please add your Page ID and Access Token in Settings.', 'warning')
                return redirect(url_for('marketing.index'))
            
            # Prepare post content
            title = form.title.data
            content = form.content.data
            message = f"{title}\n\n{content}"
            
            # Handle media upload if provided (image or video)
            media_url = None
            is_video = False

            # Check if PDF image URL was provided (from PDF upload)
            pdf_image_url = request.form.get('pdf_image_url')
            if pdf_image_url:
                media_url = pdf_image_url
                is_video = False
                print(f"DEBUG: Using PDF image URL: {media_url}", file=sys.stderr)
            elif form.image.data:
                try:
                    print("DEBUG: Processing file upload", file=sys.stderr)
                    f = form.image.data
                    filename = secure_filename(f.filename)
                    print(f"DEBUG: Filename: {filename}", file=sys.stderr)
                    
                    # Detect file type
                    ext = os.path.splitext(filename)[1].lower()
                    video_extensions = ['.mp4', '.mov', '.avi', '.wmv', '.flv', '.mkv']
                    is_video = ext in video_extensions
                    print(f"DEBUG: Is video: {is_video}", file=sys.stderr)
                    
                    # Save to static/uploads/marketing/{org_id}/
                    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'marketing', str(org.id))
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Make unique filename
                    import uuid
                    unique_filename = f"{uuid.uuid4().hex}{ext}"
                    file_path = os.path.join(upload_dir, unique_filename)
                    print(f"DEBUG: Saving to {file_path}", file=sys.stderr)
                    f.save(file_path)
                    print("DEBUG: File saved", file=sys.stderr)
                    
                    # Construct public HTTPS URL
                    # Use the dealer's subdomain for proper HTTPS access
                    if org.slug:
                        media_url = f"https://{org.slug}.bentcrankshaft.com/static/uploads/marketing/{org.id}/{unique_filename}"
                    else:
                        # Fallback to current host
                        media_url = f"{request.scheme}://{request.host}/static/uploads/marketing/{org.id}/{unique_filename}"
                    print(f"DEBUG: Media URL: {media_url}", file=sys.stderr)
                        
                except Exception as e:
                    print(f"DEBUG: Error uploading file: {str(e)}", file=sys.stderr)
                    traceback.print_exc(file=sys.stderr)
                    flash(f'Error uploading file: {str(e)}', 'danger')
                    return redirect(url_for('marketing.index'))
            
            # Post to Facebook
            if media_url and is_video:
                # Video uploads are slow, process in background
                from app.tasks.marketing import post_video_task

                # Create FacebookPost record to track status
                fb_post = FacebookPost(
                    organization_id=org.id,
                    user_id=current_user.id,
                    title=title,
                    message=message,
                    media_type='video',
                    media_url=media_url,
                    status='pending'
                )
                db.session.add(fb_post)
                db.session.commit()

                post_video_task.delay(org.id, message, media_url, title, fb_post.id)
                flash(f'Video "{title}" is being processed and uploaded to Facebook in the background. Check your Facebook page shortly.', 'info')
                
            elif media_url: # Photo
                 # Photos are fast enough handling synchronously for immediate feedback
                 # (Or should we make this async too? For now keep sync as it wasn't broken)
                 success, post_id, error = fb_service.post_photo(message, media_url)
                 if success:
                     flash(f'Successfully posted photo to Facebook! Post ID: {post_id}', 'success')
                 else:
                     flash(f'Failed to post photo: {error}', 'danger')
            else: # Text
                 success, post_id, error = fb_service.post_text(message)
                 if success:
                     flash(f'Successfully posted text to Facebook! Post ID: {post_id}', 'success')
                 else:
                     flash(f'Failed to post text: {error}', 'danger')
            
            return redirect(url_for('marketing.index'))

        # Get recent posts for the sidebar widget (last 10)
        recent_posts = FacebookPost.query.filter_by(organization_id=org.id).order_by(FacebookPost.created_at.desc()).limit(10).all()

        # Check if Facebook is connected
        fb_connected = bool(org.facebook_page_id and org.facebook_access_token)

        return render_template('marketing/index.html', form=form, specials=specials, recent_posts=recent_posts, fb_connected=fb_connected)

    except Exception as e:
        print(f"CRASH in marketing.index: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        flash(f'Internal Error: {str(e)}', 'danger')
        return redirect(url_for('marketing.dashboard'))

@marketing_bp.route('/marketing/parse-pdf', methods=['POST'])
@login_required
@csrf.exempt
def parse_pdf():
    """Parse uploaded PDF and return suggested post content"""
    try:
        if 'pdf' not in request.files:
            return jsonify({'error': 'No PDF file provided'}), 400

        pdf_file = request.files['pdf']
        if pdf_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not pdf_file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'File must be a PDF'}), 400

        org = g.current_org
        if not org:
            return jsonify({'error': 'Organization not found'}), 400

        # Check if Facebook module is authorized
        if not org.modules.get('facebook'):
            return jsonify({'error': 'Marketing module not enabled'}), 403

        # Save PDF temporarily
        from werkzeug.utils import secure_filename
        import tempfile
        import uuid

        temp_dir = tempfile.gettempdir()
        temp_pdf_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{secure_filename(pdf_file.filename)}")
        pdf_file.save(temp_pdf_path)

        # Parse the PDF
        from app.modules.marketing.pdf_parser_v2 import parse_marketing_pdf
        result = parse_marketing_pdf(temp_pdf_path)

        # Move the generated image to the uploads folder
        if result.get('image_path'):
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'marketing', str(org.id))
            os.makedirs(upload_dir, exist_ok=True)

            unique_filename = f"{uuid.uuid4().hex[:16]}_{secure_filename(pdf_file.filename)}.jpg"
            final_image_path = os.path.join(upload_dir, unique_filename)

            # Move the image
            import shutil
            shutil.move(result['image_path'], final_image_path)

            # Construct public URL
            if org.slug:
                image_url = f"https://{org.slug}.bentcrankshaft.com/static/uploads/marketing/{org.id}/{unique_filename}"
            else:
                image_url = f"{request.scheme}://{request.host}/static/uploads/marketing/{org.id}/{unique_filename}"

            result['image_url'] = image_url

        # Clean up temp PDF
        try:
            os.remove(temp_pdf_path)
        except:
            pass

        return jsonify(result), 200

    except Exception as e:
        current_app.logger.exception(f"Error parsing PDF: {e}")
        return jsonify({'error': str(e)}), 500

@marketing_bp.route('/marketing/init-chunk-upload', methods=['POST'])
@login_required
@csrf.exempt
def init_chunk_upload():
    """Initialize chunked upload session"""
    return chunk_upload.init_chunk_upload()

@marketing_bp.route('/marketing/upload-chunk', methods=['POST'])
@login_required
@csrf.exempt
def upload_chunk():
    """Upload individual chunk"""
    return chunk_upload.upload_chunk()

@marketing_bp.route('/marketing/complete-chunk-upload', methods=['POST'])
@login_required
@csrf.exempt
def complete_chunk_upload():
    """Complete chunked upload and post to Facebook"""
    try:
        upload_id = request.json.get('uploadId')
        title = request.json.get('title')
        message_content = request.json.get('content')

        org = g.current_org
        if not org:
            return jsonify({'error': 'Organization not found'}), 400

        # Assemble chunks
        unique_filename, file_path = chunk_upload.assemble_chunks(upload_id, org.id)

        # Construct public URL
        if org.slug:
            media_url = f"https://{org.slug}.bentcrankshaft.com/static/uploads/marketing/{org.id}/{unique_filename}"
        else:
            media_url = f"{request.scheme}://{request.host}/static/uploads/marketing/{org.id}/{unique_filename}"

        # Create FacebookPost record to track status
        fb_post = FacebookPost(
            organization_id=org.id,
            user_id=current_user.id,
            title=title,
            message=message_content,
            media_type='video',
            media_url=media_url,
            status='pending'
        )
        db.session.add(fb_post)
        db.session.commit()

        # Queue video upload task with post ID
        from app.tasks.marketing import post_video_task
        message = f"{title}\n\n{message_content}"
        post_video_task.delay(org.id, message, media_url, title, fb_post.id)

        return jsonify({
            'success': True,
            'message': f'Video "{title}" is being processed and uploaded to Facebook in the background.'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@marketing_bp.route('/marketing/download-bridge', methods=['POST'])
@login_required
def download_bridge():
    """Generates a custom ZIP with config.json and the master bridge EXE."""
    org = g.current_org
    if not org:
        flash("Organization not found.", "danger")
        return redirect(url_for('marketing.dashboard'))

    # 1. Generate Config
    # Force the server URL to be the dealer's specific subdomain to avoid cross-domain/405 issues
    base_domain = "pes.bentcrankshaft.com"
    scheme = request.scheme # 'https' or 'http'
    
    # If the current host isn't already the dealer subdomain, construct it
    if org.slug and org.id != 1:
        server_url = f"{scheme}://{org.slug}.{base_domain}"
    else:
        server_url = request.host_url.rstrip('/')

    config_data = {
        "pos_bridge_key": org.pos_bridge_key,
        "bridge_key": org.pos_bridge_key,
        "slug": org.slug,
        "dealer_slug": org.slug,
        "name": org.name,
        "dealer_name": org.name,
        "server_url": server_url,
        "url": server_url
    }
    
    # 2. Setup ZIP in memory
    memory_file = io.BytesIO()
    
    # Path to master EXE
    exe_path = os.path.join(current_app.root_path, 'static/uploads/downloads/PES_Bridge.exe')
    
    if not os.path.exists(exe_path):
        # Fallback check
        alt_path = os.path.join(current_app.root_path, 'static/downloads/PES_Bridge.exe')
        if os.path.exists(alt_path):
            exe_path = alt_path
        else:
            flash(f"Master Bridge file not found. Please contact support.", "danger")
            return redirect(url_for('marketing.dashboard'))

    try:
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add config.json
            zf.writestr('config.json', json.dumps(config_data, indent=4))
            
            # Add EXE
            zf.write(exe_path, 'PES_Bridge.exe')
            
            # Add Run Hidden Script (VBS) with 15-minute loop
            vbs_content = 'Set WshShell = CreateObject("WScript.Shell")\n'
            vbs_content += 'strPath = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\\"))\n'
            vbs_content += 'WshShell.CurrentDirectory = strPath\n'
            vbs_content += 'strExe = Chr(34) & strPath & "PES_Bridge.exe" & Chr(34)\n'
            vbs_content += 'Do\n'
            vbs_content += '    WshShell.Run strExe, 0, True\n'
            vbs_content += '    WScript.Sleep 900000 \' Wait 15 minutes\n'
            vbs_content += 'Loop'
            zf.writestr('run_bridge_hidden.vbs', vbs_content)
            
            # Add a Readme
            readme = "PES BRIDGE INSTRUCTIONS\n"
            readme += "=======================\n\n"
            readme += "1. Extract this ZIP file completely (Right-click > Extract All).\n"
            readme += "2. **FIRST RUN**: Double-click 'PES_Bridge.exe' once. If Windows asks \n"
            readme += "   for permission, click 'Run anyway'. Verify it syncs successfully.\n\n"
            readme += "3. **BACKGROUND MODE**: Once the first run is done, use 'run_bridge_hidden.vbs'.\n"
            readme += "   This will run the bridge silently in the background every 15 minutes.\n\n"
            readme += "AUTOMATIC STARTUP:\n"
            readme += "------------------\n"
            readme += "To have the bridge start automatically when your computer turns on:\n"
            readme += "1. Right-click 'run_bridge_hidden.vbs' and select 'Create Shortcut'.\n"
            readme += "2. Copy/Move that SHORTCUT into your Windows Startup folder.\n"
            readme += "   (DO NOT move the script itself, only the shortcut.)"
            zf.writestr('README.txt', readme)
            
        memory_file.seek(0)
        
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'PES_Bridge_{org.slug}.zip'
        )
    except Exception as e:
        flash(f"Error generating download: {str(e)}", "danger")
        return redirect(url_for('marketing.dashboard'))
@marketing_bp.route('/marketing/history', methods=['GET'])
@login_required
def history():
    """Display post history with status tracking"""
    org = g.current_org

    # Check if Facebook module is authorized
    if not org.modules.get('facebook'):
        flash('The Marketing module is not enabled for your account. Please contact support to activate this feature.', 'warning')
        return redirect(url_for('main.index'))

    posts = FacebookPost.query.filter_by(organization_id=org.id).order_by(FacebookPost.created_at.desc()).limit(50).all()
    return render_template('marketing/history.html', posts=posts)

@marketing_bp.route('/marketing/dashboard', methods=['GET'])
@login_required
def dashboard():
    # --- Dual Dashboard Logic ---
    from app.core.models import Organization, PartInventory, Unit
    from datetime import datetime, timedelta
    
    # 1. SaaS Command Center (Master Org)
    if g.current_org_id == 1:
        # Fetch Stats
        total_dealers = Organization.query.count()
        active_dealers = Organization.query.filter_by(is_active=True).count()
        
        # Check for Offline Bridges (> 1 hour since heartbeat)
        cutoff = datetime.utcnow() - timedelta(hours=1)
        offline_bridges = Organization.query.filter(
            Organization.id != 1, # Ignore Master
            Organization.is_active == True,
            (Organization.last_bridge_heartbeat < cutoff) | (Organization.last_bridge_heartbeat == None)
        ).all()
        
        # Fetch All Tenants for Site Manager View
        tenants = Organization.query.order_by(Organization.id).all()
        
        return render_template('main/saas_dashboard.html', 
                             total_dealers=total_dealers,
                             active_dealers=active_dealers, 
                             offline_bridges=offline_bridges,
                             tenants=tenants)

    # 2. Marketing Control Center (Dealer Org)
    else:
        org = g.current_org
        
        # Auto-redirect to onboarding wizard for new dealers
        if not org.onboarding_complete:
            return redirect(url_for('settings.onboarding'))
        
        # Bridge Status
        bridge_online = False
        last_seen = org.last_bridge_heartbeat
        if last_seen and (datetime.utcnow() - last_seen) < timedelta(minutes=15):
             bridge_online = True
             
        # Inventory Stats
        parts_count = PartInventory.query.filter_by(organization_id=org.id).count()
        units_count = Unit.query.filter_by(organization_id=org.id, display_on_web=True).count()
        
        return render_template('main/dealer_dashboard.html',
                             bridge_online=bridge_online,
                             last_seen=last_seen,
                             parts_count=parts_count,
                             units_count=units_count)
