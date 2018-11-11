from flask import Flask, request, abort, jsonify
import flask_sqlalchemy
import os
import configuration
import datetime

app = Flask(__name__)
app.config.from_object("configuration.Config")
db = flask_sqlalchemy.SQLAlchemy(app)


class BlogPost(db.Model):
    __tablename__ = "blogposts"

    post_id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String)
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime)
    edit_timestamp = db.Column(db.DateTime)

    def as_dict(self):
        return {
            "id": self.post_id,
            "author": self.author,
            "content": self.content,
            "timestamp": self.timestamp
        }


@app.route("/api/blog", methods=["GET", "POST", "PUT", "DELETE"])
def api_blog():
    if request.method == "POST":
        # New post
        # Get the correct password from the config; I don't care enough to bcrypt this
        correct_password = app.config.get("POST_PASSWORD")
        if correct_password is None:
            abort(500)
            return
        # Check password
        if request.form.get("password", "") != correct_password:
            abort(403)
            return
        # Get the current time
        timestamp = datetime.datetime.now()
        # Get the post content
        content = request.form.get("content")
        if content is None:
            abort(400)
            return
        # Create the new post
        post = db.BlogPost(author="Steffo",
                           content=content,
                           timestamp=timestamp)
        db.session.add(post)
        db.session.commit()
        return jsonify(post.as_dict())
    elif request.method == "GET":
        # Get post(s)
        # Get the correct password from the config
        correct_password = app.config.get("POST_PASSWORD")
        if correct_password is None:
            abort(500)
            return
        # Check password
        authenticated = (request.args.get("password", "") != correct_password)
        # Get n posts from a certain timestamp and the number of previous posts
        now = datetime.datetime.now()
        time = request.args.get("time")
        limit = request.args.get("limit", 50)
        # Make the request
        query = db.BlogPost.query()
        if not authenticated:
            # Hide hidden posts if not authenticated
            query = query.filter(db.BlogPost.timestamp <= now)
        if time is not None:
            # Hide all posts after the specified time
            query = query.filter(db.BlogPost.timestamp <= time)
        query = query.order_by(db.BlogPost.timestamp.desc())
        query = query.limit(limit)
        query = query.all()
        return jsonify([post.as_dict() for post in query])
    elif request.method == "PUT":
        # Edit post
        # Get the correct password from the config
        correct_password = app.config.get("POST_PASSWORD")
        if correct_password is None:
            abort(500)
            return
        # Check password
        if request.form.get("password", "") != correct_password:
            abort(403)
            return
        # Try to find the post to be edited
        post_id = request.form.get("post_id")
        if post_id is None:
            abort(400)
            return
        post = db.BlogPost.query().filter_by(post_id=post_id).one_or_404()
        # Get the new post contents
        content = request.form.get("content")
        if content is None:
            abort(400)
            return
        # Update the post
        post.content = content
        post.edit_timestamp = datetime.datetime.now()
        # Commit the updates
        db.session.commit()
        return jsonify(post.as_dict())
    elif request.method == "DELETE":
        # Delete post
        # Get the correct password from the config
        correct_password = app.config.get("POST_PASSWORD")
        if correct_password is None:
            abort(500)
            return
        # Check password
        if request.form.get("password", "") != correct_password:
            abort(403)
            return
        # Try to find the post to be deleted
        post_id = request.form.get("post_id")
        if post_id is None:
            abort(400)
            return
        post = BlogPost.query().filter_by(post_id=post_id).one_or_404()
        # Delete the post
        db.session.delete(post)
        db.session.commit()
        return ("", 204)


@app.after_request
def after_every_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
return response


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True, port=1234)