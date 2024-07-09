from flask import Flask
from config import Config
from models import db, Post
from routes import init_routes
from flask_cors import CORS
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

# Flask 앱을 초기화합니다.
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# 데이터베이스를 초기화합니다.
db.init_app(app)

# 기존 테이블을 유지하고 Flask가 테이블을 생성하지 않도록 수정
# with app.app_context():
#     db.create_all()

# 라우트를 초기화합니다.
init_routes(app)

# today_views를 리셋하는 작업을 정의합니다.
def reset_today_views():
    with app.app_context():
        posts = Post.query.all()
        for post in posts:
            post.today_views = 0
        db.session.commit()
        print("Reset today_views")

# 스케줄러를 설정하고 작업을 추가합니다.
scheduler = BackgroundScheduler()
scheduler.add_job(func=reset_today_views, trigger="cron", hour=0, minute=0)
scheduler.start()

# 스케줄러를 종료할 때를 처리하기 위해 atexit을 사용
atexit.register(lambda: scheduler.shutdown())

# Flask 애플리케이션을 실행합니다.
if __name__ == '__main__':
    app.run(debug=True)