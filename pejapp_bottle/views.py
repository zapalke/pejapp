from bottle import Bottle, request, redirect, jinja2_template as template
from models import session, User

app = Bottle()  # Musimy tu mieć instancję Bottle


@app.route("/users")
def users():
    users_list = session.query(User).all()
    return template("users", users=users_list)


@app.route("/edit_user/<id>", method="GET")
def edit_user_form(id):
    user = session.query(User).filter_by(id=id).first()
    if not user:
        return "Użytkownik nie istnieje", 404
    return template("edit_user", user=user)


@app.route("/edit_user/<id>", method="POST")
def edit_user(id):
    user = session.query(User).filter_by(id=id).first()
    if user:
        user.name = request.forms.get("name")
        user.email = request.forms.get("email")
        session.commit()
    return redirect("/users")


@app.route("/delete_user/<id>")
def delete_user(id):
    user = session.query(User).filter_by(id=id).first()
    if user:
        session.delete(user)
        session.commit()
    return redirect("/users")


@app.route("/register", method="GET")
def register_form():
    return template("register")


@app.route("/register", method="POST")
def register():
    name = request.forms.get("name")
    email = request.forms.get("email")
    password = request.forms.get("password")

    if session.query(User).filter_by(email=email).first():
        return "Email już istnieje!"

    user = User(name=name, email=email)
    user.set_password(password)
    session.add(user)
    session.commit()

    return redirect("/login")


from bottle import request, response


@app.route("/login", method="GET")
def login_form():
    return template("login")


@app.route("/login", method="POST")
def login():
    email = request.forms.get("email")
    password = request.forms.get("password")

    user = session.query(User).filter_by(email=email).first()

    if user and user.check_password(password):
        response.set_cookie("user_id", str(user.id), secret="mysecret")
        return redirect("/dashboard")
    else:
        return "Błędny email lub hasło"


@app.route("/logout")
def logout():
    response.delete_cookie("user_id")
    return redirect("/login")


def get_current_user():
    user_id = request.get_cookie("user_id", secret="mysecret")
    if user_id:
        return session.query(User).filter_by(id=user_id).first()
    return None


@app.route("/dashboard")
def dashboard():
    user = get_current_user()
    if not user:
        return redirect("/login")
    return template("dashboard", user=user)
