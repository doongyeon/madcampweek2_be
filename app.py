from flask import Flask
from config import Config
from models import db
from routes import init_routes
from flask_cors import CORS
import scheduler

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

db.init_app(app)

# 기존 테이블을 유지하고 Flask가 테이블을 생성하지 않도록 수정
# with app.app_context():
#     db.create_all()

init_routes(app)

if __name__ == '__main__':
    app.run(debug=True)
