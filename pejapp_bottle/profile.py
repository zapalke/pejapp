from bottle import Bottle, template, request, redirect
from database import SessionLocal
from models import User, Post
from forms import ProfileUpdateForm
from bottle_login import login_required, current_user

profile = Bottle()


@profile.route("/profile/<username>", method=["GET", "POST"])
@login_required
def user_profile(username):
    db = SessionLocal()
    user = db.query(User).filter_by(username=username).first()
    if not user:
        db.close()
        return "User not found"

    form = ProfileUpdateForm(request.forms, obj=user)
    if request.method == "POST" and form.validate() and user == current_user:
        form.populate_obj(user)
        db.commit()
        db.close()
        return redirect(f"/profile/{username}")

    posts = (
        db.query(Post)
        .filter_by(author_id=user.id)
        .order_by(Post.date_posted.desc())
        .all()
    )
    db.close()
    return template("profile", user=user, form=form, posts=posts)
