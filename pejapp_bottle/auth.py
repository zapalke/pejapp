from bottle import Bottle, template, request, redirect
from database import SessionLocal
from models import User
from forms import RegistrationForm, LoginForm
from bottle_login import LoginPlugin

auth = Bottle()
auth.config["SECRET_KEY"] = "super_secret_key"
login_plugin = LoginPlugin()
auth.install(login_plugin)


@auth.route("/register", method=["GET", "POST"])
def register():
    db = SessionLocal()
    form = RegistrationForm(request.forms)
    if request.method == "POST" and form.validate():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.add(user)
        db.commit()
        db.close()
        return redirect("/login")
    db.close()
    return template("register", form=form)


@auth.route("/login", method=["GET", "POST"])
def login():
    db = SessionLocal()
    form = LoginForm(request.forms)
    if request.method == "POST" and form.validate():
        user = db.query(User).filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_plugin.login_user(user)  # Logowanie użytkownika
            db.close()
            return redirect("/")
    db.close()
    return template("login", form=form)


@auth.route("/logout")
def logout():
    login_plugin.logout_user()  # Wylogowanie użytkownika
    return redirect("/")
