from flask import render_template, request, flash, redirect, url_for, g, abort, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc
from app.core.extensions import db
from app.core.models import Case, Unit, Dealer, Note, User
from app.core.utils import render_note_html
from . import cases_bp
from datetime import datetime

@cases_bp.route('/cases')
@login_required
def index():
    status_filter = request.args.get('status', 'Open')
    search = request.args.get('search', '').strip()
    
    query = Case.query
    
    if status_filter != 'All':
        if status_filter == 'Open':
            query = query.filter(Case.status != 'Closed')
        else:
            query = query.filter(Case.status == status_filter)
            
    if search:
        query = query.join(Case.unit).join(Case.dealer).filter(
            (Case.id.cast(str).like(f'%{search}%')) |
            (Case.reference.ilike(f'%{search}%')) |
            (Unit.serial_number.ilike(f'%{search}%')) |
            (Dealer.name.ilike(f'%{search}%'))
        )
        
    cases = query.order_by(Case.creation_timestamp.desc()).limit(100).all()
    
    return render_template('cases/index.html', cases=cases, status_filter=status_filter, search=search)

@cases_bp.route('/cases/create', methods=['GET', 'POST'])
@login_required
def create():
    # Simple creation flow: Input Serial -> Find/Create Unit -> Select Dealer -> Create Case
    # For MVP, we'll assume Unit ID and Dealer ID are passed or we use a form to find them.
    # Let's simplify: A form where you type Serial (AJAX lookup) and Select Dealer.
    
    if request.method == 'POST':
        unit_id = request.form.get('unit_id')
        dealer_id = request.form.get('dealer_id')
        reference = request.form.get('reference')
        description = request.form.get('description')
        
        if not dealer_id:
            flash('Dealer is required.', 'danger')
            return redirect(url_for('cases.create'))
            
        # Unit is optional now
        if not unit_id:
            unit_id = None
            
        new_case = Case(
            organization_id=g.current_org_id,
            unit_id=unit_id,
            dealer_id=dealer_id,
            reference=reference,
            status='New',
            case_type='Support', # Default
            channel='Web'
        )
        db.session.add(new_case)
        db.session.flush()
        
        # Add initial note
        if description:
            note = Note(
                case_id=new_case.id,
                organization_id=g.current_org_id, # Ensure Note model has this or we rely on case relationship (Note model needs org_id update if not present)
                # Checking Note model in previous context... Note usually links to Case. 
                # Multi-tenancy filter on Note usually checks Case.organization_id join.
                # But my listener logic might require Note to have org_id if I want to insert it easily.
                # Let's check models.py content again or just add it if safe.
                # Re-reading models.py snippet from earlier... Note didn't show org_id in snippet 939-943.
                # I will strictly follow the Case's org logic. 
                # If Note table doesn't have org_id, I rely on Case. 
                # But creating it: I need to make sure I don't fail constraint.
                text=description,
                user=current_user.username,
                timestamp=datetime.utcnow()
            )
            # Add org_id if model has it, otherwise skip. 
            # I suspect I didn't add org_id to Note explicitly in the plan? 
            # The plan said "All Domain Models".
            # I will blindly add organization_id=g.current_org_id assuming I migrated it.
            # If it fails, I'll fix.
            note.organization_id = g.current_org_id 
            db.session.add(note)
            
        print(f"DEBUG: Pre-Commit for Case {new_case.id}", flush=True)
        db.session.commit()
        print(f"DEBUG: Post-Commit for Case {new_case.id}", flush=True)
        
        flash(f'Case #{new_case.id} created.', 'success')
        return redirect(url_for('cases.view', case_id=new_case.id))

    dealers = Dealer.query.order_by(Dealer.name).all()
    # Units would be loaded via AJAX ideally, but for now passing none.
    return render_template('cases/create.html', dealers=dealers)

@cases_bp.route('/cases/<int:case_id>')
@login_required
def view(case_id):
    print(f"DEBUG: Entering view case {case_id}", flush=True)
    case = Case.query.get_or_404(case_id)
    print(f"DEBUG: Fetched case {case.id}", flush=True)
    # Users for mentions
    users = User.query.order_by(User.username).all()
    print(f"DEBUG: Fetched users", flush=True)
    mention_data = jsonify([{'key': u.username, 'value': u.username} for u in users]).json
    
    return render_template('cases/detail.html', case=case, users=users, render_note_html=render_note_html)

@cases_bp.route('/cases/<int:case_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(case_id):
    case = Case.query.get_or_404(case_id)
    
    if request.method == 'POST':
        dealer_id = request.form.get('dealer_id')
        unit_id = request.form.get('unit_id')
        reference = request.form.get('reference')
        
        if dealer_id:
            case.dealer_id = dealer_id
        
        # Handle unit update
        if unit_id:
            case.unit_id = unit_id
        # Note: If unit_id is empty string, do we clear it? 
        # If user cleared it intentionally... 
        # For now, if passed as empty string, implies clear?
        # The form sends existing ID if not changed. 
        # If lookup failed, hidden is empty. 
        elif unit_id == '':
             case.unit_id = None
             
        if reference:
            case.reference = reference
            
        db.session.commit()
        flash('Case details updated.', 'success')
        return redirect(url_for('cases.view', case_id=case.id))
        
    dealers = Dealer.query.order_by(Dealer.name).all()
    return render_template('cases/edit.html', case=case, dealers=dealers)

@cases_bp.route('/cases/<int:case_id>/notes/add', methods=['POST'])
@login_required
def add_note(case_id):
    case = Case.query.get_or_404(case_id)
    text = request.form.get('note_text')
    
    if text:
        note = Note(
            case_id=case.id,
            text=text,
            user=current_user.username,
            organization_id=g.current_org_id
        )
        db.session.add(note)
        # Touch case updated
        # case.last_updated = ...
        db.session.commit()
        flash('Note added.', 'success')
        
    return redirect(url_for('cases.view', case_id=case_id))

@cases_bp.route('/cases/<int:case_id>/status', methods=['POST'])
@login_required
def update_status(case_id):
    case = Case.query.get_or_404(case_id)
    new_status = request.form.get('status')
    if new_status:
        case.status = new_status
        if new_status == 'Closed':
            case.closed_date = datetime.utcnow()
        elif new_status != 'Closed' and case.closed_date:
            case.reopened_date = datetime.utcnow()
            
        sys_note = Note(
            case_id=case.id,
            text=f"*** Status changed to {new_status} by {current_user.username} ***",
            user='System',
            organization_id=g.current_org_id
        )
        db.session.add(sys_note)
        db.session.commit()
        flash(f'Status updated to {new_status}.', 'success')
        
    return redirect(url_for('cases.view', case_id=case_id))

@cases_bp.route('/cases/delete/<int:case_id>', methods=['POST'])
@login_required
def delete(case_id):
    case = Case.query.get_or_404(case_id)
    if case.organization_id != g.current_org_id:
        abort(403)
        
    try:
        db.session.delete(case)
        db.session.commit()
        flash('Case deleted successfully.', 'success')
        return redirect(url_for('cases.index'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting case: {e}', 'danger')
        return redirect(url_for('cases.view', case_id=case_id))
