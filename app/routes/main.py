from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from app.models.customer import Customer
from app.models.property import Property
from app.models.report import Report
from app import db

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """ダッシュボード画面を表示"""
    # 統計情報の取得
    stats = {
        'customer_count': Customer.query.count(),
        'property_count': Property.query.count(),
        'report_count': Report.query.count(),
        'pending_count': Report.query.filter_by(status='pending').count()
    }
    
    # 最近の報告書を取得（最新5件）
    recent_reports = Report.query.order_by(Report.created_at.desc()).limit(5).all()
    
    # 最近のお客様を取得（最新5件）
    recent_customers = Customer.query.order_by(Customer.created_at.desc()).limit(5).all()
    
    # 最近の物件を取得（最新5件）
    recent_properties = Property.query.order_by(Property.created_at.desc()).limit(5).all()
    
    return render_template('index.html', 
                          stats=stats,
                          recent_reports=recent_reports,
                          recent_customers=recent_customers,
                          recent_properties=recent_properties) 