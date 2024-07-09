from flask import request, jsonify
from models import db, Category, Post, Reaction, Comment, User, UserCategory, Report
import boto3
from config import Config
from datetime import datetime, timezone


# S3 버킷 설정
S3_BUCKET = Config.S3_BUCKET
S3_KEY = Config.S3_KEY
S3_SECRET = Config.S3_SECRET
S3_LOCATION = Config.S3_LOCATION

s3 = boto3.client(
    's3',
    aws_access_key_id=S3_KEY,
    aws_secret_access_key=S3_SECRET
)

def upload_file_to_s3(file, bucket_name, acl="public-read"):
    try:
        s3.upload_fileobj(
            file,
            bucket_name,
            file.filename,
            ExtraArgs={
                "ACL": acl,
                "ContentType": file.content_type
            }
        )
        print(f"File uploaded to S3: {file.filename}")
        return f"{S3_LOCATION}{file.filename}"
    except Exception as e:
        print(f"Something Happened: {e}")
        return None

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
        data = request.form
        title = data['title']
        content = data['content']
        category_id = data['category_id']
        image_url = None

        if 'image' in request.files:
            image = request.files['image']
            image_url = upload_file_to_s3(image, S3_BUCKET)
        elif 'image_url' in data:
            image_url = data['image_url']

        new_post = Post(
            title=title,
            image=image_url,
            content=content,
            category_id=category_id
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
                "category_id": post.category_id,
                "today_views": post.today_views,
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
            reaction_type=data['content']  # 'like', 'dislike' 등
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
            comment_text=data['content']
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
    
    @app.route('/get_interests/<int:user_id>', methods=['GET'])
    def get_interests(user_id):
        user_categories = UserCategory.query.filter_by(user_id=user_id).all()
        results = [
            {
                "id": user_category.category.id,
                "category_name": user_category.category.category_name
            } for user_category in user_categories]

        return jsonify(results)

    from datetime import datetime

    @app.route('/edit_post/<int:post_id>', methods=['PUT'])
    def edit_post(post_id):
        data = request.form
        post = Post.query.get(post_id)
        if post is None:
            return jsonify({"error": "Post not found"}), 404

        post.title = data.get('title', post.title)
        post.content = data.get('content', post.content)

        print(f"Received data: {data}")

        if 'image' in request.files:
            image = request.files['image']
            print(f"Received image: {image.filename}")
            image_url = upload_file_to_s3(image, S3_BUCKET)
            if image_url:
                post.image = image_url
            else:
                return jsonify({"error": "Failed to upload image"}), 500
        elif 'image_url' in data:
            post.image = data['image_url']

        post.total_views = post.total_views or 0
        post.today_views = post.today_views or 0

        # 명시적으로 updated_at 필드를 현재 GMT 시간으로 설정합니다.
        post.updated_at = datetime.now(timezone.utc)

        try:
            db.session.commit()
        except Exception as e:
            print(f"Error committing to database: {e}")
            return jsonify({"error": "Failed to update post in database"}), 500

        response = {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "image": post.image,
            "category_id": post.category_id,
            "total_views": post.total_views,
            "today_views": post.today_views,
            "created_at": post.created_at,
            "updated_at": post.updated_at
        }

        return jsonify(response)


    @app.route('/liked_posts/<int:user_id>', methods=['GET'])
    def liked_posts(user_id):
        liked_post_ids = db.session.query(Reaction.post_id).filter(
            Reaction.user_id == user_id, Reaction.reaction_type == 'like'
        ).all()
        liked_post_ids = [post_id[0] for post_id in liked_post_ids]
        
        liked_posts = Post.query.filter(Post.id.in_(liked_post_ids)).all()
        results = [
            {
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "image": post.image,
                "category_id": post.category_id,
                "created_at": post.created_at,
                "updated_at": post.updated_at,
                "today_views": post.today_views,
            } for post in liked_posts
        ]

        return jsonify(results)
    
    @app.route('/comments/<int:post_id>', methods=['GET'])
    def get_comments(post_id):
        comments = Comment.query.filter_by(post_id=post_id).all()
        results = [
            {
                "id": comment.id,
                "post_id": comment.post_id,
                "user_id": comment.user_id,
                "comment_text": comment.comment_text,
                "created_at": comment.created_at,
                "updated_at": comment.updated_at
            } for comment in comments]
        return jsonify(results)
    
    @app.route('/reactions/<int:post_id>/<int:user_id>', methods=['GET'])
    def get_reactions(post_id, user_id):
        likes_count = Reaction.query.filter_by(post_id=post_id, reaction_type='like').count()
        dislikes_count = Reaction.query.filter_by(post_id=post_id, reaction_type='dislike').count()
        
        user_reaction = Reaction.query.filter_by(post_id=post_id, user_id=user_id).first()
        user_reaction_type = user_reaction.reaction_type if user_reaction else None

        result = {
            "post_id": post_id,
            "likes": likes_count,
            "dislikes": dislikes_count,
            "user_reaction": user_reaction_type
        }

        return jsonify(result)
    
    @app.route('/remove_reaction', methods=['POST'])
    def remove_reaction():
        data = request.get_json()
        post_id = data['post_id']
        user_id = data['user_id']
        reaction_type = data['content']  # 'like', 'dislike' 등

        reaction = Reaction.query.filter_by(post_id=post_id, user_id=user_id, reaction_type=reaction_type).first()
        
        if reaction:
            db.session.delete(reaction)
            db.session.commit()
            return jsonify({"message": "Reaction removed successfully"})
        else:
            return jsonify({"message": "Reaction not found"}), 404

    @app.route('/post/<int:post_id>/view', methods=['GET'])
    def increment_post_views(post_id):
        post = Post.query.get(post_id)
        if post is None:
            return jsonify({"error": "Post not found"}), 404

        # total_views와 today_views를 증가시킵니다.
        post.total_views += 1
        post.today_views += 1

        db.session.commit()

        return '', 204  # No Content 응답

    @app.route('/posts/<int:post_id>', methods=['GET'])
    def get_post(post_id):
        post = Post.query.get(post_id)
        if post is None:
            return jsonify({"error": "Post not found"}), 404

        result = {
            "id": post.id,
            "title": post.title,
            "image": post.image,
            "content": post.content,
            "category_id": post.category_id,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "total_views": post.total_views,
            "today_views": post.today_views
        }

        return jsonify(result)
    
    @app.route('/report_post', methods=['POST'])
    def report_post():
        data = request.get_json()
        new_report = Report(
            post_id=data['post_id'],
            user_id=data['user_id'],
            report_reason=data['report_reason']
        )
        db.session.add(new_report)
        db.session.commit()
        return jsonify({"message": "Report submitted successfully"})

    @app.route('/reported_posts', methods=['GET'])
    def get_reported_posts():
        reports = Report.query.all()
        results = [
            {
                "report_id": report.id,
                "post_id": report.post_id,
                "user_id": report.user_id,
                "report_reason": report.report_reason,
                "report_date": report.report_date
            } for report in reports]

        return jsonify(results)
    
    @app.route('/delete_comment', methods=['DELETE'])
    def delete_comment():
        data = request.get_json()
        comment_id = data['comment_id']
        comment = Comment.query.get(comment_id)
        if comment is None:
            return jsonify({"error": "Comment not found"}), 404

        db.session.delete(comment)
        db.session.commit()
        return jsonify({"message": "Comment deleted successfully"})