from flask import render_template
from app.api import bp

@bp.route('/analysis')
def analysis():
    """数据分析页面路由"""
    return render_template('analysis.html')