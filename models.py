from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default='user')
    supervisors = db.relationship('Supervisor', secondary='user_supervisor', back_populates='users')

class Supervisor(db.Model):
    __tablename__ = 'supervisor'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)

    users = db.relationship('User', secondary='user_supervisor', back_populates='supervisors')

    def __repr__(self):
        return f"<Supervisor {self.name}>"

class UserSupervisor(db.Model):
    __tablename__ = 'user_supervisor'
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'), primary_key=True)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    customer_name = db.Column(db.String(150), nullable=False)
    payment_term = db.Column(db.Integer, nullable=True)
    balance = db.Column(db.Float, nullable=True)
    supervisor = db.Column(db.String(150), nullable=True)
    invoice_status = db.Column(db.String(50), nullable=True)  
    comment = db.Column(db.Text, nullable=True) 
    paid_amount = db.Column(db.String(150), nullable=True)     
    expected_paid_day = db.Column(db.Date, nullable=True)  
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  
    updated_by = db.Column(db.String(150), nullable=True)  


class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    payment_status = db.Column(db.String(50), nullable=False)  
    comments = db.Column(db.Text, nullable=True)
    follow_up_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  

class PaidFeedback(db.Model):
    __tablename__ = 'paid_feedback'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    comments = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)