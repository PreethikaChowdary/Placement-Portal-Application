from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

db = SQLAlchemy(app)

# ─── Models ────────────────────────────────────────────────────────────────────

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    hr_contact = db.Column(db.String(15))
    website = db.Column(db.String(200))
    approved = db.Column(db.Boolean, default=False)
    blacklisted = db.Column(db.Boolean, default=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    contact = db.Column(db.String(15))
    education = db.Column(db.String(500))
    skills = db.Column(db.String(500))
    resume = db.Column(db.String(200))
    blacklisted = db.Column(db.Boolean, default=False)

class PlacementDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    job_title = db.Column(db.String(200), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    required_skills = db.Column(db.String(500))
    experience = db.Column(db.String(100))
    salary_range = db.Column(db.String(100))
    eligibility = db.Column(db.String(500))
    deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Applied')

# ─── Init DB ───────────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(username='admin', password=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ─── Public Routes ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        email = request.form.get('email')
        password = request.form.get('password')
        if role == 'admin':
            admin = Admin.query.filter_by(username=email).first()
            if admin and check_password_hash(admin.password, password):
                session['user_id'] = admin.id
                session['role'] = 'admin'
                return redirect(url_for('admin_dashboard'))
            flash('Invalid credentials.')
        elif role == 'company':
            company = Company.query.filter_by(email=email).first()
            if company and check_password_hash(company.password, password):
                if company.blacklisted:
                    flash('Your account has been blacklisted.')
                elif not company.approved:
                    flash('Your account is pending admin approval.')
                else:
                    session['user_id'] = company.id
                    session['role'] = 'company'
                    return redirect(url_for('company_dashboard'))
            else:
                flash('Invalid credentials.')
        elif role == 'student':
            student = Student.query.filter_by(email=email).first()
            if student and check_password_hash(student.password, password):
                if student.blacklisted:
                    flash('Your account has been blacklisted.')
                else:
                    session['user_id'] = student.id
                    session['role'] = 'student'
                    return redirect(url_for('student_dashboard'))
            else:
                flash('Invalid credentials.')
        else:
            flash('Invalid credentials.')
    return render_template('login.html')

@app.route('/register/<role>', methods=['GET', 'POST'])
def register(role):
    if request.method == 'POST':
        if role == 'company':
            if Company.query.filter_by(email=request.form.get('email')).first():
                flash('Email already registered.')
                return render_template('register.html', role=role)
            company = Company(
                name=request.form.get('name'),
                email=request.form.get('email'),
                password=generate_password_hash(request.form.get('password')),
                hr_contact=request.form.get('contact'),
                website=request.form.get('website')
            )
            db.session.add(company)
            db.session.commit()
            flash('Registration successful. Wait for admin approval.')
            return redirect(url_for('login'))
        elif role == 'student':
            if Student.query.filter_by(email=request.form.get('email')).first():
                flash('Email already registered.')
                return render_template('register.html', role=role)
            student = Student(
                name=request.form.get('name'),
                email=request.form.get('email'),
                password=generate_password_hash(request.form.get('password')),
                contact=request.form.get('contact'),
                education=request.form.get('education'),
                skills=request.form.get('skills')
            )
            if 'resume' in request.files:
                file = request.files['resume']
                if file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    student.resume = filename
            db.session.add(student)
            db.session.commit()
            flash('Registration successful. You can now login.')
            return redirect(url_for('login'))
    return render_template('register.html', role=role)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ─── Admin Routes ──────────────────────────────────────────────────────────────

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    students = Student.query.all()
    companies = Company.query.all()
    drives = PlacementDrive.query.all()
    applications = Application.query.all()
    return render_template('admin_dashboard.html',
                           students=students, companies=companies,
                           drives=drives, applications=applications)

@app.route('/admin/search', methods=['POST'])
def admin_search():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    search_type = request.form.get('search_type')
    search_query = request.form.get('search_query', '')
    if search_type == 'student':
        results = Student.query.filter(
            (Student.name.contains(search_query)) |
            (Student.email.contains(search_query)) |
            (Student.contact.contains(search_query))
        ).all()
    else:
        results = Company.query.filter(Company.name.contains(search_query)).all()
    students = Student.query.all()
    companies = Company.query.all()
    drives = PlacementDrive.query.all()
    applications = Application.query.all()
    return render_template('admin_dashboard.html',
                           students=students, companies=companies,
                           drives=drives, applications=applications,
                           search_results=results,
                           search_type=search_type,
                           search_query=search_query)

@app.route('/admin/approve/company/<int:id>')
def approve_company(id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    company = Company.query.get_or_404(id)
    company.approved = True
    db.session.commit()
    flash('Company approved.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/company/<int:id>')
def reject_company(id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    company = Company.query.get_or_404(id)
    db.session.delete(company)
    db.session.commit()
    flash('Company rejected and removed.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/blacklist/company/<int:id>')
def blacklist_company(id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    company = Company.query.get_or_404(id)
    company.blacklisted = True
    db.session.commit()
    flash('Company blacklisted.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/company/<int:id>')
def delete_company(id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    company = Company.query.get_or_404(id)
    db.session.delete(company)
    db.session.commit()
    flash('Company deleted.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit/company/<int:id>', methods=['GET', 'POST'])
def admin_edit_company(id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    company = Company.query.get_or_404(id)
    if request.method == 'POST':
        company.name = request.form.get('name', '').strip()
        company.hr_contact = request.form.get('contact', '').strip()
        company.website = request.form.get('website', '').strip()
        db.session.commit()
        flash('Company updated.')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_edit_company.html', company=company)

@app.route('/admin/blacklist/student/<int:id>')
def blacklist_student(id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    student = Student.query.get_or_404(id)
    student.blacklisted = True
    db.session.commit()
    flash('Student blacklisted.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/student/<int:id>')
def delete_student(id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit/student/<int:id>', methods=['GET', 'POST'])
def admin_edit_student(id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    student = Student.query.get_or_404(id)
    if request.method == 'POST':
        student.name = request.form.get('name', '').strip()
        student.contact = request.form.get('contact', '').strip()
        student.education = request.form.get('education', '').strip()
        student.skills = request.form.get('skills', '').strip()
        db.session.commit()
        flash('Student updated.')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_edit_student.html', student=student)

@app.route('/admin/approve/drive/<int:id>')
def approve_drive(id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    drive = PlacementDrive.query.get_or_404(id)
    drive.status = 'Approved'
    db.session.commit()
    flash('Drive approved.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/drive/<int:id>')
def reject_drive(id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    drive = PlacementDrive.query.get_or_404(id)
    drive.status = 'Rejected'
    db.session.commit()
    flash('Drive rejected.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/drive/<int:id>')
def admin_delete_drive(id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    drive = PlacementDrive.query.get_or_404(id)
    Application.query.filter_by(drive_id=drive.id).delete()
    db.session.delete(drive)
    db.session.commit()
    flash('Drive deleted.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/charts')
def admin_charts():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_drives = PlacementDrive.query.count()
    total_applications = Application.query.count()
    approved_companies = Company.query.filter_by(approved=True).count()
    pending_companies = Company.query.filter_by(approved=False).count()
    approved_drives = PlacementDrive.query.filter_by(status='Approved').count()
    pending_drives = PlacementDrive.query.filter_by(status='Pending').count()
    rejected_drives = PlacementDrive.query.filter_by(status='Rejected').count()
    closed_drives = PlacementDrive.query.filter_by(status='Closed').count()
    applied = Application.query.filter_by(status='Applied').count()
    shortlisted = Application.query.filter_by(status='Shortlisted').count()
    selected = Application.query.filter_by(status='Selected').count()
    rejected_apps = Application.query.filter_by(status='Rejected').count()
    return render_template('admin_charts.html',
        total_students=total_students, total_companies=total_companies,
        total_drives=total_drives, total_applications=total_applications,
        approved_companies=approved_companies, pending_companies=pending_companies,
        approved_drives=approved_drives, pending_drives=pending_drives,
        rejected_drives=rejected_drives, closed_drives=closed_drives,
        applied=applied, shortlisted=shortlisted,
        selected=selected, rejected_apps=rejected_apps)

# ─── Company Routes ────────────────────────────────────────────────────────────

@app.route('/company/dashboard')
def company_dashboard():
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    company_id = session.get('user_id')
    drives = PlacementDrive.query.filter_by(company_id=company_id).all()
    for drive in drives:
        drive.app_count = Application.query.filter_by(drive_id=drive.id).count()
    return render_template('company_dashboard.html', drives=drives)

@app.route('/company/create_drive', methods=['GET', 'POST'])
def create_drive():
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        skills = request.form.get('skills', '').strip()
        experience = request.form.get('experience', '').strip()
        salary = request.form.get('salary', '').strip()
        eligibility = request.form.get('eligibility', '').strip()
        deadline_str = request.form.get('deadline', '').strip()
        if not all([title, description, skills, experience, salary, eligibility, deadline_str]):
            flash('All fields are required.')
            return render_template('create_drive.html')
        drive = PlacementDrive(
            company_id=session.get('user_id'),
            job_title=title, job_description=description,
            required_skills=skills, experience=experience,
            salary_range=salary, eligibility=eligibility,
            deadline=datetime.strptime(deadline_str, '%Y-%m-%d')
        )
        db.session.add(drive)
        db.session.commit()
        flash('Drive created. Waiting for admin approval.')
        return redirect(url_for('company_dashboard'))
    return render_template('create_drive.html')

@app.route('/company/edit_drive/<int:id>', methods=['GET', 'POST'])
def edit_drive(id):
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    drive = PlacementDrive.query.get_or_404(id)
    if drive.company_id != session.get('user_id'):
        flash('Unauthorised.')
        return redirect(url_for('company_dashboard'))
    if request.method == 'POST':
        drive.job_title = request.form.get('title', '').strip()
        drive.job_description = request.form.get('description', '').strip()
        drive.required_skills = request.form.get('skills', '').strip()
        drive.experience = request.form.get('experience', '').strip()
        drive.salary_range = request.form.get('salary', '').strip()
        drive.eligibility = request.form.get('eligibility', '').strip()
        deadline_str = request.form.get('deadline', '').strip()
        if deadline_str:
            drive.deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
        drive.status = 'Pending'
        db.session.commit()
        flash('Drive updated. Re-submitted for admin approval.')
        return redirect(url_for('company_dashboard'))
    return render_template('edit_drive.html', drive=drive)

@app.route('/company/close_drive/<int:id>')
def close_drive(id):
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    drive = PlacementDrive.query.get_or_404(id)
    if drive.company_id != session.get('user_id'):
        flash('Unauthorised.')
        return redirect(url_for('company_dashboard'))
    drive.status = 'Closed'
    db.session.commit()
    flash('Drive closed.')
    return redirect(url_for('company_dashboard'))

@app.route('/company/delete_drive/<int:id>')
def delete_drive(id):
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    drive = PlacementDrive.query.get_or_404(id)
    if drive.company_id != session.get('user_id'):
        flash('Unauthorised.')
        return redirect(url_for('company_dashboard'))
    Application.query.filter_by(drive_id=drive.id).delete()
    db.session.delete(drive)
    db.session.commit()
    flash('Drive deleted.')
    return redirect(url_for('company_dashboard'))

@app.route('/company/view_applications/<int:drive_id>')
def view_applications(drive_id):
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != session.get('user_id'):
        flash('Unauthorised.')
        return redirect(url_for('company_dashboard'))
    applications = Application.query.filter_by(drive_id=drive_id).all()
    items = []
    for app in applications:
        student = Student.query.get(app.student_id)
        items.append({'app': app, 'student': student})
    return render_template('view_applications.html', applications=items, drive=drive)

@app.route('/company/update_status/<int:app_id>/<status>')
def update_application_status(app_id, status):
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    allowed_statuses = ['Shortlisted', 'Selected', 'Rejected']
    if status not in allowed_statuses:
        flash('Invalid status.')
        return redirect(url_for('company_dashboard'))
    application = Application.query.get_or_404(app_id)
    application.status = status
    db.session.commit()
    flash(f'Application marked as {status}.')
    return redirect(url_for('view_applications', drive_id=application.drive_id))

@app.route('/company/charts')
def company_charts():
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    company_id = session.get('user_id')
    drives = PlacementDrive.query.filter_by(company_id=company_id).all()
    drive_labels = [d.job_title[:20] for d in drives]
    drive_counts = [Application.query.filter_by(drive_id=d.id).count() for d in drives]
    shortlisted = [Application.query.filter_by(drive_id=d.id, status='Shortlisted').count() for d in drives]
    selected = [Application.query.filter_by(drive_id=d.id, status='Selected').count() for d in drives]
    rejected = [Application.query.filter_by(drive_id=d.id, status='Rejected').count() for d in drives]
    return render_template('company_charts.html',
        drive_labels=drive_labels, drive_counts=drive_counts,
        shortlisted=shortlisted, selected=selected, rejected=rejected)

# ─── Student Routes ────────────────────────────────────────────────────────────

@app.route('/student/dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    drives = PlacementDrive.query.filter_by(status='Approved').all()
    student_id = session.get('user_id')
    applications = Application.query.filter_by(student_id=student_id).all()
    return render_template('student_dashboard.html', drives=drives, applications=applications)

@app.route('/student/profile', methods=['GET', 'POST'])
def student_profile():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    student = Student.query.get_or_404(session.get('user_id'))
    if request.method == 'POST':
        student.name = request.form.get('name', '').strip()
        student.contact = request.form.get('contact', '').strip()
        student.education = request.form.get('education', '').strip()
        student.skills = request.form.get('skills', '').strip()
        if 'resume' in request.files:
            file = request.files['resume']
            if file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                student.resume = filename
            elif file.filename and not allowed_file(file.filename):
                flash('Invalid file type. Only PDF, DOC, DOCX allowed.')
                return render_template('student_profile.html', student=student)
        db.session.commit()
        flash('Profile updated successfully.')
        return redirect(url_for('student_dashboard'))
    return render_template('student_profile.html', student=student)

@app.route('/student/apply/<int:drive_id>')
def apply_drive(drive_id):
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    student_id = session.get('user_id')
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.status != 'Approved':
        flash('This drive is not available.')
        return redirect(url_for('student_dashboard'))
    existing = Application.query.filter_by(student_id=student_id, drive_id=drive_id).first()
    if existing:
        flash('You have already applied for this drive.')
        return redirect(url_for('student_dashboard'))
    application = Application(student_id=student_id, drive_id=drive_id)
    db.session.add(application)
    db.session.commit()
    flash(f'Successfully applied for "{drive.job_title}". You will be notified when your status changes.')
    return redirect(url_for('student_dashboard'))

@app.route('/student/notifications')
def student_notifications():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    student_id = session.get('user_id')
    notifications = db.session.query(Application, PlacementDrive)\
        .join(PlacementDrive, Application.drive_id == PlacementDrive.id)\
        .filter(Application.student_id == student_id)\
        .filter(Application.status != 'Applied')\
        .all()
    return render_template('notifications.html', notifications=notifications)

@app.route('/student/charts')
def student_charts():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    student_id = session.get('user_id')
    applied = Application.query.filter_by(student_id=student_id, status='Applied').count()
    shortlisted = Application.query.filter_by(student_id=student_id, status='Shortlisted').count()
    selected = Application.query.filter_by(student_id=student_id, status='Selected').count()
    rejected = Application.query.filter_by(student_id=student_id, status='Rejected').count()
    return render_template('student_charts.html',
        applied=applied, shortlisted=shortlisted,
        selected=selected, rejected=rejected)

# ─── API Test Page ─────────────────────────────────────────────────────────────

@app.route('/api-test')
def api_test():
    return render_template('api_test.html')

# ─── API Endpoints ─────────────────────────────────────────────────────────────

@app.route('/api/students', methods=['GET'])
def api_get_students():
    students = Student.query.all()
    return jsonify([{'id': s.id, 'name': s.name, 'email': s.email,
                     'contact': s.contact, 'skills': s.skills,
                     'education': s.education} for s in students])

@app.route('/api/students/<int:id>', methods=['GET'])
def api_get_student(id):
    s = Student.query.get_or_404(id)
    return jsonify({'id': s.id, 'name': s.name, 'email': s.email,
                    'contact': s.contact, 'skills': s.skills,
                    'education': s.education, 'resume': s.resume})

@app.route('/api/students', methods=['POST'])
def api_create_student():
    data = request.get_json()
    student = Student(
        name=data.get('name'), email=data.get('email'),
        password=generate_password_hash(data.get('password')),
        contact=data.get('contact'), education=data.get('education'),
        skills=data.get('skills')
    )
    db.session.add(student)
    db.session.commit()
    return jsonify({'message': 'Student created', 'id': student.id}), 201

@app.route('/api/students/<int:id>', methods=['PUT'])
def api_update_student(id):
    student = Student.query.get_or_404(id)
    data = request.get_json()
    student.name = data.get('name', student.name)
    student.contact = data.get('contact', student.contact)
    student.education = data.get('education', student.education)
    student.skills = data.get('skills', student.skills)
    db.session.commit()
    return jsonify({'message': 'Student updated'})

@app.route('/api/students/<int:id>', methods=['DELETE'])
def api_delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    return jsonify({'message': 'Student deleted'})

@app.route('/api/companies', methods=['GET'])
def api_get_companies():
    companies = Company.query.all()
    return jsonify([{'id': c.id, 'name': c.name, 'email': c.email,
                     'website': c.website, 'approved': c.approved} for c in companies])

@app.route('/api/drives', methods=['GET'])
def api_get_drives():
    drives = PlacementDrive.query.all()
    return jsonify([{'id': d.id, 'company_id': d.company_id, 'job_title': d.job_title,
                     'required_skills': d.required_skills, 'salary_range': d.salary_range,
                     'status': d.status,
                     'deadline': d.deadline.strftime('%Y-%m-%d')} for d in drives])

@app.route('/api/drives/<int:id>', methods=['GET'])
def api_get_drive(id):
    d = PlacementDrive.query.get_or_404(id)
    return jsonify({'id': d.id, 'company_id': d.company_id, 'job_title': d.job_title,
                    'job_description': d.job_description, 'required_skills': d.required_skills,
                    'experience': d.experience, 'salary_range': d.salary_range,
                    'eligibility': d.eligibility, 'status': d.status,
                    'deadline': d.deadline.strftime('%Y-%m-%d')})

@app.route('/api/applications', methods=['GET'])
def api_get_applications():
    applications = Application.query.all()
    return jsonify([{'id': a.id, 'student_id': a.student_id, 'drive_id': a.drive_id,
                     'status': a.status,
                     'application_date': a.application_date.strftime('%Y-%m-%d')} for a in applications])

@app.route('/api/applications/drive/<int:drive_id>', methods=['GET'])
def api_get_applications_by_drive(drive_id):
    applications = Application.query.filter_by(drive_id=drive_id).all()
    return jsonify([{'id': a.id, 'student_id': a.student_id, 'status': a.status,
                     'application_date': a.application_date.strftime('%Y-%m-%d')} for a in applications])

@app.route('/api/statistics', methods=['GET'])
def api_statistics():
    return jsonify({
        'total_students': Student.query.count(),
        'total_companies': Company.query.count(),
        'total_drives': PlacementDrive.query.count(),
        'total_applications': Application.query.count(),
        'approved_companies': Company.query.filter_by(approved=True).count(),
        'approved_drives': PlacementDrive.query.filter_by(status='Approved').count()
    })

if __name__ == '__main__':
    app.run(debug=False)




