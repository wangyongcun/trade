import os
from flask import render_template

from db_utils import get_stock_list

def register_index_routes(app):
    @app.route('/')
    def index():
        stock_list = get_stock_list()
        
        return render_template('index.html', stocks=stock_list)