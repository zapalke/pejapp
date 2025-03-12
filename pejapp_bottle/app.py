from bottle import (
    Bottle,
    request,
    redirect,
    static_file,
    jinja2_template as template,
    TEMPLATE_PATH as BOTTLE_TEMPLATE_PATH,
)
from jinja2 import Environment, FileSystemLoader
import sqlite3
import os
from beaker.middleware import SessionMiddleware
import datetime
import math

# ==== App configuration ====
DATABASE = os.path.join(os.getcwd(), "database.db")
SECRET_KEY = "secret_key"
STATIC_PATH = os.path.join(os.getcwd(), "static")
TEMPLATE_PATH = os.path.join(os.getcwd(), "templates")
BOTTLE_TEMPLATE_PATH.append(TEMPLATE_PATH)

# Template engine configuration
env = Environment(loader=FileSystemLoader(TEMPLATE_PATH))
# Możesz dodać dodatkowe filtry, np. truncatewords, jeśli potrzebujesz

# Beaker session options
session_opts = {
    "session.type": "file",
    "session.data_dir": "./session_data",
    "session.auto": True,
    "session.cookie_expires": 3600,
    "session.encrypt_key": SECRET_KEY,
    "session.validate_key": SECRET_KEY,
}

# Initialize Bottle app and session middleware
bottle_app = Bottle()


# ==== Database functions ====
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db = get_db()
    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT NOT NULL,
        date_posted TEXT NOT NULL,
        last_modified TEXT NOT NULL,
        author_id INTEGER NOT NULL,
        modified_flag INTEGER DEFAULT 0,
        original_content TEXT,
        FOREIGN KEY(author_id) REFERENCES users(id)
    );
    """
    db.executescript(schema)
    db.commit()


# ==== Pagination functions ====
class Paginator:
    def __init__(self, items, page, per_page):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total_items = len(items)
        self.total_pages = math.ceil(self.total_items / per_page) if per_page > 0 else 1

    @property
    def number(self):
        return self.page

    @property
    def paginator(self):
        class DummyPaginator:
            def __init__(self, total_pages):
                self.page_range = list(range(1, total_pages + 1))

        return DummyPaginator(self.total_pages)

    @property
    def has_previous(self):
        return self.page > 1

    @property
    def previous_page_number(self):
        return self.page - 1 if self.has_previous else None

    @property
    def has_next(self):
        return self.page < self.total_pages

    @property
    def next_page_number(self):
        return self.page + 1 if self.has_next else None

    @property
    def page_items(self):
        start = (self.page - 1) * self.per_page
        end = start + self.per_page
        return self.items[start:end]


def paginate_items(items, page, per_page):
    return Paginator(items, page, per_page)


# ==== User functions ====
def create_user(username, email, password):
    db = get_db()
    db.execute(
        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
        (username, email, password),
    )
    db.commit()


def get_user_by_username(username):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return user


def verify_user(username, password):
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?", (username, password)
    ).fetchone()
    return user


# ==== Posts functions ====
def create_post(title, content, user_id):
    db = get_db()
    now = datetime.datetime.now().isoformat()
    db.execute(
        "INSERT INTO posts (title, content, date_posted, last_modified, author_id) VALUES (?, ?, ?, ?, ?)",
        (title, content, now, now, user_id),
    )
    db.commit()


def get_all_posts():
    db = get_db()
    posts = db.execute("SELECT * FROM posts ORDER BY date_posted DESC").fetchall()
    return posts


def get_posts_by_user(user_id):
    db = get_db()
    posts = db.execute(
        "SELECT * FROM posts WHERE author_id = ? ORDER BY date_posted DESC", (user_id,)
    ).fetchall()
    return posts


# ==== Template filters ====
env.filters["strftime"] = lambda value, fmt="%Y-%m-%d %H:%M:%S": (
    value.strftime(fmt) if hasattr(value, "strftime") else value
)


# ==== Helper functions ====
def get_current_user():
    session = request.environ.get("beaker.session")
    return session.get("user", {"is_authenticated": False})


# ==== Views and routes ====


@bottle_app.route("/")
def home():
    all_posts = get_all_posts()
    page = int(request.query.get("page", "1"))
    per_page = 10  # Możesz dostosować liczbę postów na stronę
    posts_paginated = paginate_items(all_posts, page, per_page)
    user = get_current_user()
    return template("pejapp/home", posts=posts_paginated, user=user, _env=env)


@bottle_app.route("/register", method=["GET", "POST"])
def register():
    user = get_current_user()
    if request.method == "POST":
        username = request.forms.get("username")
        email = request.forms.get("email")
        password = request.forms.get("password")
        confirm_password = request.forms.get("confirm_password")

        if password != confirm_password:
            return template(
                "pejapp/register", error="Hasła nie są identyczne", user=user, _env=env
            )

        if get_user_by_username(username):
            return template(
                "pejapp/register",
                error="Użytkownik o podanej nazwie już istnieje",
                user=user,
                _env=env,
            )

        create_user(username, email, password)
        redirect("/login")

    return template("pejapp/register", user=user, _env=env)


@bottle_app.route("/login", method=["GET", "POST"])
def login():
    user = get_current_user()
    if request.method == "POST":
        username = request.forms.get("username")
        password = request.forms.get("password")
        user_record = verify_user(username, password)
        if user_record:
            session = request.environ.get("beaker.session")
            user_obj = dict(user_record)
            user_obj["is_authenticated"] = True
            session["user"] = user_obj
            session.save()
            redirect("/")
        else:
            return template(
                "pejapp/login", error="Niepoprawne dane logowania", user=user, _env=env
            )
    return template("pejapp/login", user=user, _env=env)


@bottle_app.route("/logout")
def logout():
    session = request.environ.get("beaker.session")
    session.delete()
    redirect("/")


@bottle_app.route("/create_post", method=["GET", "POST"])
def create_post_route():
    user = get_current_user()
    if not user.get("is_authenticated"):
        redirect("/login")
    if request.method == "POST":
        title = request.forms.get("title")
        content = request.forms.get("content")
        user_id = user["id"]
        create_post(title, content, user_id)
        redirect("/")
    return template("pejapp/create_post", user=user, _env=env)


@bottle_app.route("/user/<username>")
def user_profile(username):
    profile_user = get_user_by_username(username)
    if not profile_user:
        return "Użytkownik nie istnieje"
    posts = get_posts_by_user(profile_user["id"])
    current = get_current_user()
    is_owner = current.get("is_authenticated") and (current.get("username") == username)
    return template(
        "pejapp/user_profile",
        user=profile_user,
        posts=posts,
        is_owner=is_owner,
        current_user=current,
        _env=env,
    )


@bottle_app.route("/search", method=["GET"])
def search():
    query = request.query.get("q")
    db = get_db()
