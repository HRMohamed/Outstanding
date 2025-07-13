from flask import Flask, render_template, redirect, url_for, request, flash,current_app,session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models import Feedback, db, User, Invoice,PaidFeedback,Supervisor
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pandas as pd
from flask import jsonify
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_wtf import FlaskForm
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import or_



app = Flask(__name__)
app.config['SECRET_KEY'] = '1234'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]  
)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id)) 


class ResetPasswordForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Reset Password')

@app.route('/Forget_password', methods=['GET', 'POST'])
@limiter.limit("3 per minute")  
def Forget_password():
    form = ResetPasswordForm()
    if form.validate_on_submit(): 
        username = form.username.data
        user = User.query.filter_by(username=username).first()
        if user:
            new_password = form.new_password.data
            hashed_password = generate_password_hash(new_password)
            user.password = hashed_password
            db.session.commit()
            flash('Password reset successful', 'success')
            return redirect(url_for('login'))

        flash('Username does not exist', 'danger')

    return render_template('Forget_password.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(f'Trying to log in with username: {username}')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))

        flash('Login failed. Check your username and password', 'danger')

    return render_template('login.html')

@app.route('/manage_users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('dashboard'))

    users = User.query.all()
    supervisors = Supervisor.query.all()  # Retrieve all supervisors

    if request.method == 'POST':
        for user in users:
            # Update role
            role_field = f"role_{user.id}"
            new_role = request.form.get(role_field)
            if new_role and new_role != user.role:
                user.role = new_role

            # Update supervisors
            supervisor_field = f"supervisor_{user.id}[]"
            new_supervisors_ids = request.form.getlist(supervisor_field)  # Get list of selected supervisor IDs
            user.supervisors = Supervisor.query.filter(Supervisor.id.in_(new_supervisors_ids)).all()

        db.session.commit()  # Commit changes after all updates
        flash('User details updated successfully!', 'success')
        return redirect(url_for('manage_users'))

    return render_template('manage_users.html', users=users, supervisor_names=supervisors)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST' and 'preview' in request.form:
        file = request.files.get('file')
        if not file:
            flash('No file uploaded. Please select a file.', 'danger')
            return redirect(url_for('upload'))

        if not file.filename.endswith(('.xls', '.xlsx')):
            flash('Invalid file type. Please upload an Excel file.', 'danger')
            return redirect(url_for('upload'))

        try:
            data = pd.read_excel(file, sheet_name="Sheet1", header=0)
            data.columns = [col.strip() for col in data.columns]
            
            required_columns = ['Customer Name', 'Payment Term', 'Balance', 'Supervisor / Direct Manager']
            if not all(col in data.columns for col in required_columns):
                flash('Some required columns are missing. Please check your file.', 'danger')
                return redirect(url_for('upload'))

            data = data.applymap(lambda x: x.strip() if isinstance(x, str) else x)

            valid_data = []
            invalid_data = []

            for index, row in data.iterrows():
                if pd.isna(row['Customer Name']):
                    invalid_data.append(row)
                else:
                    valid_data.append(row)

            session['valid_uploaded_data'] = pd.DataFrame(valid_data).to_dict(orient='records')
            session['invalid_uploaded_data'] = pd.DataFrame(invalid_data).to_dict(orient='records')

            return render_template(
                'upload_preview.html',
                valid_columns=data.columns,
                valid_data=pd.DataFrame(valid_data).head(10).to_dict(orient='records'),
                invalid_data=pd.DataFrame(invalid_data).head(10).to_dict(orient='records')
            )
        except Exception as e:
            flash(f'Error processing file: {e}', 'danger')
            return redirect(url_for('upload'))

    elif request.method == 'POST' and 'submit' in request.form:
        try:
            # Clear existing invoice data from the database
            Invoice.query.delete()
            db.session.commit()

            uploaded_data = session.get('valid_uploaded_data')
            if not uploaded_data:
                flash('No data to process. Please upload a file.', 'danger')
                return redirect(url_for('upload'))

            # Extract unique supervisors
            unique_supervisors = set()

            for row in uploaded_data:
                try:
                    invoice = Invoice(
                        user_id=current_user.id,
                        customer_name=row.get('Customer Name'),
                        payment_term=row.get('Payment Term'),
                        balance=float(str(row.get('Balance')).replace(',', '')) if row.get('Balance') else None,
                        supervisor=row.get('Supervisor / Direct Manager'),
                    )
                    db.session.add(invoice)

                    # Add supervisor to the set for uniqueness
                    unique_supervisors.add(row.get('Supervisor / Direct Manager'))

                except Exception as row_error:
                    print(f"Error saving row: {row_error}")

            # Now, add unique supervisors to the Supervisor table
            for supervisor_name in unique_supervisors:
                if isinstance(supervisor_name, str) and supervisor_name.strip():  # Ensure the name is a string and not empty
                    existing_supervisor = Supervisor.query.filter_by(name=supervisor_name).first()
                    if not existing_supervisor:  # Only add if it doesn't already exist
                        new_supervisor = Supervisor(name=supervisor_name)
                        db.session.add(new_supervisor)

            db.session.commit()
            flash('Data uploaded successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Error saving data: {e}', 'danger')
            return redirect(url_for('upload'))

    return render_template('upload.html')

def filter_invoices(query, customer_name, payment_term_filter, sort_by):
    if customer_name:
        query = query.filter(Invoice.customer_name.ilike(f"%{customer_name}%"))
    if payment_term_filter:
        query = query.filter(Invoice.payment_term == payment_term_filter)

    valid_sorts = ['id', 'customer_name', 'expected_paid_day', 'balance']
    if sort_by in valid_sorts:
        query = query.order_by(getattr(Invoice, sort_by))

    return query

@app.route('/dashboard')
@login_required
def dashboard():
    customer_name = request.args.get('customer_name', '').strip()
    payment_term_filter = request.args.get('payment_term', '').strip()
    sort_by = request.args.get('sort', 'id')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    if current_user.role == 'admin':
        query = Invoice.query
    else:
        supervisor_names = [sup.name for sup in current_user.supervisors]
        query = Invoice.query.filter(Invoice.supervisor.in_(supervisor_names))

    query = filter_invoices(query, customer_name, payment_term_filter, sort_by)

    invoices = query.paginate(page=page, per_page=per_page)

    unique_payment_terms = (
        db.session.query(Invoice.payment_term)
        .filter(Invoice.payment_term.isnot(None))
        .distinct()
        .order_by(Invoice.payment_term)
        .all()
    )

    return render_template(
        'dashboard.html',
        invoices=invoices,
        unique_payment_terms=unique_payment_terms,
        customer_name=customer_name,
        payment_term_filter=payment_term_filter,
        sort_by=sort_by
    )

@app.route('/update_invoices', methods=['GET', 'POST'])
@login_required
def update_invoices():
    if request.method == 'POST':
        invoice_id = request.form.get('invoice_id')
        new_status = request.form.get('invoice_status')
        paid_amount = request.form.get('paid_amount')
        payment_date = request.form.get('expected_paid_day')
        expected_date = request.form.get('expected_paid_day')

        if invoice_id and new_status:
            invoice = Invoice.query.get(invoice_id)
            if invoice and invoice.supervisor in [sup.name for sup in current_user.supervisors]:
                invoice.invoice_status = new_status
                if new_status == 'Paid':
                    invoice.balance = 0
                    invoice.comment = f"Paid on {payment_date}"
                elif new_status == 'Partial Payment' and paid_amount:
                    invoice.balance -= float(paid_amount)
                invoice.expected_paid_day = expected_date
                db.session.commit()
                flash(f'Invoice {invoice_id} updated successfully!', 'success')
            else:
                flash('Unauthorized to edit this invoice.', 'danger')


    supervisor_names = [sup.name for sup in current_user.supervisors]
    invoices = Invoice.query.filter(
        (Invoice.invoice_status != 'Paid') | (Invoice.invoice_status.is_(None)),  
        Invoice.supervisor.in_(supervisor_names)
    ).all()

    return render_template('update_invoices.html', invoices=invoices)



@app.route('/api/companies', methods=['GET'])
def get_companies():
    search_term = request.args.get('term', '').lower()
    companies = set(invoice.customer_name for invoice in Invoice.query.all())
    filtered_companies = [company for company in companies if company.lower().startswith(search_term)]
    return jsonify(filtered_companies)

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        
        if existing_user:
            flash('Username already exists. Please choose a different username.', 'danger')
            return redirect(url_for('add_user'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, role='user') 
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'User {username} added successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('add_user.html')


@app.route('/')
def index():
    return redirect(url_for('login'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        admin_user = User.query.filter_by(username="admin").first()
        if not admin_user:
            hashed_password = generate_password_hash("admin")
            admin_user = User(username="admin", password=hashed_password, role="admin")
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created: Username='admin', Password='admin'")

    app.run(debug=True)
