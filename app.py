import os
from flask import Flask
from routes.index_routes import register_index_routes
from routes.stock_routes import register_stock_routes
from routes.stock2_routes import register_stock2_routes
from routes.stock3_routes import register_stock3_routes

app = Flask(__name__, static_folder='static')

# 创建templates目录
os.makedirs('templates', exist_ok=True)

# 注册路由
register_index_routes(app)
register_stock_routes(app)
register_stock2_routes(app)
register_stock3_routes(app)

if __name__ == '__main__':
    app.run(debug=True)