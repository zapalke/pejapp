from bottle import Bottle, template, request, redirect
from database import SessionLocal
from models import Post
from forms import PostForm
from bottle_login import login_required, current_user

post = Bottle()


@post.route("/post/new", method=["GET", "POST"])
@login_required
def post_create():
    db = SessionLocal()
    form = PostForm(request.forms)
    if request.method == "POST" and form.validate():
        new_post = Post(content=form.content.data, author_id=current_user.id)
        db.add(new_post)
        db.commit()
        db.close()
        return redirect("/profile/" + current_user.username)
    db.close()
    return template("create_post", form=form)


@post.route("/post/<id>", method=["GET"])
def post_detail(id):
    db = SessionLocal()
    post = db.query(Post).get(id)
    db.close()
    return template("post_detail", post=post)


@post.route("/post/<id>/edit", method=["GET", "POST"])
@login_required
def post_update(id):
    db = SessionLocal()
    post = db.query(Post).get(id)
    if post.author_id != current_user.id:
        db.close()
        return "Unauthorized"

    form = PostForm(request.forms, obj=post)
    if request.method == "POST" and form.validate():
        form.populate_obj(post)
        db.commit()
        db.close()
        return redirect("/profile/" + current_user.username)

    db.close()
    return template("create_post", form=form)


@post.route("/post/<id>/delete")
@login_required
def post_delete(id):
    db = SessionLocal()
    post = db.query(Post).get(id)
    if post.author_id == current_user.id:
        db.delete(post)
        db.commit()
    db.close()
    return redirect("/profile/" + current_user.username)
