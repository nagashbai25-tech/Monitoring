import os
from datetime import datetime

from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from prometheus_client import Gauge
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("POSTGRES_URL")
db = SQLAlchemy(app)

# Метрики для Prometheus: добавляет эндпоинт /metrics и считает для каждого запроса
# счётчик flask_http_request_total и гистограмму flask_http_request_duration_seconds.
metrics = PrometheusMetrics(app, group_by="endpoint")
metrics.info("miniblog_app_info", "Информация о приложении", version="1.0")


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.relationship("Comment", backref="post", cascade="all, delete-orphan")


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)


with app.app_context():
    db.create_all()


def _count(model):
    """Число строк для метрики. Если базы нет, отдаём NaN, чтобы не ронять /metrics."""
    try:
        with app.app_context():
            return model.query.count()
    except Exception:
        return float("nan")


# Бизнес-метрики: считаются в момент скрейпа прямо из базы.
Gauge("miniblog_posts", "Количество постов в блоге").set_function(lambda: _count(Post))
Gauge("miniblog_comments", "Количество комментариев").set_function(lambda: _count(Comment))


@app.route("/")
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template("index.html", posts=posts)


@app.route("/new", methods=["GET", "POST"])
def new_post():
    if request.method == "POST":
        post = Post(title=request.form["title"], body=request.form["body"])
        db.session.add(post)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("new_post.html")


@app.route("/post/<int:post_id>")
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("post.html", post=post)


@app.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == "POST":
        post.title = request.form["title"]
        post.body = request.form["body"]
        db.session.commit()
        return redirect(url_for("view_post", post_id=post.id))
    return render_template("edit_post.html", post=post)


@app.route("/post/<int:post_id>/delete", methods=["POST"])
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/post/<int:post_id>/comment", methods=["POST"])
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    comment = Comment(author=request.form["author"], body=request.form["body"], post_id=post.id)
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for("view_post", post_id=post.id))


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    # Локальный запуск без Docker. В контейнере приложение запускает gunicorn.
    app.run(host="0.0.0.0", port=5000, debug=os.getenv("FLASK_DEBUG") == "1")
