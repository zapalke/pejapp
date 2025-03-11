from bottle import Bottle, template, request
from database import SessionLocal
from models import Post

views = Bottle()


@views.route("/")
def home():
    db = SessionLocal()
    page = int(request.query.get("page", 1))
    per_page = 5
    posts = (
        db.query(Post)
        .order_by(Post.date_posted.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    db.close()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return template("post_list", posts=posts)

    return template("home", posts=posts)
