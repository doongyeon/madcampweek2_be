from apscheduler.schedulers.background import BackgroundScheduler
from models import db, Post
from datetime import datetime
import atexit

def reset_today_views():
    from app import app
    with app.app_context():
        posts = Post.query.all()
        for post in posts:
            post.today_views = 0
        db.session.commit()
        print("Reset today_views")

scheduler = BackgroundScheduler()
scheduler.add_job(func=reset_today_views, trigger="cron", hour=0, minute=0)
scheduler.start()

# 스케줄러를 종료할 때를 처리하기 위해 atexit을 사용
atexit.register(lambda: scheduler.shutdown())
