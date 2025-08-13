import os
from flask import render_template

def register_index_routes(app):
    @app.route('/')
    def index():
        # 获取所有股票文件
        stock_files = [f for f in os.listdir('stock-data') if f.endswith('.xlsx')]
        stock_list = [{'code': f.split('_')[0], 'name': f.split('_')[1].replace('.xlsx', '')} for f in stock_files]
        
        return render_template('index.html', stocks=stock_list)