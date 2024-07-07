from flask import request, jsonify
from models import db, Category, Post, Reaction, Comment, User, UserCategory

def init_routes(app):
    @app.route('/create_category', methods=['POST'])
    def create_category():
        data = request.get_json()
        new_category = Category(category_name=data['name'])
        db.session.add(new_category)
        db.session.commit()
        return jsonify({"message": "Category created successfully", "category_id": new_category.id})

    @app.route('/create_post', methods=['POST'])
    def create_post():
        data = request.get_json()
        new_post = Post(
            title=data['title'],
            image=data['image'],
            content=data['content'],
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
                "image": post.image,
                "content": post.content,
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
            is_new_user = True
        else:
            user.nickname = nickname
            db.session.commit()
            is_new_user = False
        
        return jsonify({"message": "User logged in successfully", "user_id": user.id, "is_new_user": is_new_user})

    @app.route('/save_interests', methods=['POST'])
    def save_interests():
        data = request.get_json()
        user_id = data['user_id']
        interests = data['interests']

        # 사용자의 기존 관심 카테고리를 삭제합니다.
        UserCategory.query.filter_by(user_id=user_id).delete()

        # 새로운 관심 카테고리를 저장합니다.
        for interest in interests:
            category = Category.query.filter_by(category_name=interest).first()
            if category:
                new_user_category = UserCategory(user_id=user_id, category_id=category.id)
                db.session.add(new_user_category)

        db.session.commit()
        return jsonify({"message": "Interests saved successfully"})

    @app.route('/edit_post/<int:post_id>', methods=['PUT'])
    def edit_post(post_id):
        data = request.get_json()
        post = Post.query.get(post_id)
        if post is None:
            return jsonify({"error": "Post not found"}), 404
        
        post.title = data.get('title', post.title)
        post.image = data.get('image', post.image)
        post.content = data.get('content', post.content)
        post.category_id = data.get('category_id', post.category_id)
        db.session.commit()
        return jsonify({"message": "Post updated successfully", "post_id": post.id})