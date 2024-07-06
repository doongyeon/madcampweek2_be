from flask import request, jsonify
from models import db, Category, Post, Reaction, Comment, User

def init_routes(app):
    @app.route('/create_category', methods=['POST'])
    def create_category():
        data = request.get_json()
        new_category = Category(name=data['name'])
        db.session.add(new_category)
        db.session.commit()
        return jsonify({"message": "Category created successfully", "category_id": new_category.id})

    @app.route('/create_post', methods=['POST'])
    def create_post():
        data = request.get_json()
        new_post = Post(
            title=data['title'],
            image_url=data['image_url'],
            category_id=data['category_id']
        )
        db.session.add(new_post)
        db.session.commit()
        return jsonify({"message": "Post created successfully", "post_id": new_post.id})

    @app.route('/posts', methods=['GET'])
    def get_posts():
        posts = Post.query.all()
        results = [
            {
                "id": post.id,
                "title": post.title,
                "image_url": post.image_url,
                "category": post.category_id,
                "created_at": post.created_at,
                "updated_at": post.updated_at
            } for post in posts]

        return jsonify(results)

    @app.route('/react_post', methods=['POST'])
    def react_post():
        data = request.get_json()
        new_reaction = Reaction(
            post_id=data['post_id'],
            user_id=data['user_id'],
            content=data['content']  # 좋아요, 싫어요 등
        )
        db.session.add(new_reaction)
        db.session.commit()
        return jsonify({"message": "Reaction added successfully"})

    @app.route('/comment_post', methods=['POST'])
    def comment_post():
        data = request.get_json()
        new_comment = Comment(
            post_id=data['post_id'],
            user_id=data['user_id'],
            content=data['content']
        )
        db.session.add(new_comment)
        db.session.commit()
        return jsonify({"message": "Comment added successfully"})

    @app.route('/kakao_login', methods=['POST'])
    def kakao_login():
        data = request.get_json()
        kakao_id = data['kakao_id']
        nickname = data['nickname']
        
        user = User.query.filter_by(kakao_id=kakao_id).first()
        if user is None:
            user = User(kakao_id=kakao_id, nickname=nickname)
            db.session.add(user)
            db.session.commit()
        else:
            user.nickname = nickname
            db.session.commit()
        
        return jsonify({"message": "User logged in successfully", "user_id": user.id})
