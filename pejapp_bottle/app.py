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
env = Environment(loader=FileSystemLoader(TEMPLATE_PATH), auto_reload=True)

# Template filters
env.filters["strftime"] = lambda value, fmt="%Y-%m-%d %H:%M:%S": (
    value.strftime(fmt) if hasattr(value, "strftime") else value
)


def truncatewords(value, num=20):
    try:
        num = int(num)
    except (ValueError, TypeError):
        return value
    words = value.split()
    if len(words) > num:
        return " ".join(words[:num]) + "..."
    return value


env.filters["truncatewords"] = truncatewords

# Powiąż nasze środowisko Jinja2 z globalnym słownikiem szablonów Bottle
from bottle import TEMPLATES

TEMPLATES["jinja2"] = env

# ==== Beaker session options ====
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
        password TEXT NOT NULL,
        bio TEXT
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

    def __iter__(self):
        return iter(self.page_items)

    @property
    def page_items(self):
        start = (self.page - 1) * self.per_page
        end = start + self.per_page
        return self.items[start:end]

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


def paginate_items(items, page, per_page):
    return Paginator(items, page, per_page)


# ==== Helper functions dla truncacji tekstu ====
def truncate_text(text, limit=20):
    if len(text) > limit:
        return text[:limit] + "..."
    return text


def convert_post_row(row, text_limit=20):
    d = dict(row)
    # Przypisujemy dane autora do zagnieżdżonego słownika i usuwamy je z głównego słownika
    d["author"] = {"username": d.pop("username"), "email": d.pop("email")}
    d["content"] = truncate_text(d.get("content", ""), text_limit)
    return d


def convert_post_rows(rows, text_limit=20):
    return [convert_post_row(row, text_limit) for row in rows]


def convert_post_row_full(row):
    d = dict(row)
    username = d.pop("username")
    email = d.pop("email") if "email" in d else ""
    d["author"] = {"username": username, "email": email}
    return d


def convert_post_rows_full(rows):
    return [convert_post_row_full(row) for row in rows]


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
    query = """
        SELECT posts.*, users.username, users.email
        FROM posts
        JOIN users ON posts.author_id = users.id
        ORDER BY date_posted DESC
    """
    rows = db.execute(query).fetchall()
    # Na stronie głównej chcemy pełne treści, więc nie skracamy
    return convert_post_rows_full(rows)


def get_posts_by_user(user_id):
    db = get_db()
    query = """
        SELECT posts.*, users.username, users.email
        FROM posts
        JOIN users ON posts.author_id = users.id
        WHERE posts.author_id = ?
        ORDER BY date_posted DESC
    """
    rows = db.execute(query, (user_id,)).fetchall()
    # Dla profilu użytkownika również pełna treść
    return convert_post_rows_full(rows)


# ==== Helper functions ====
def get_current_user():
    session = request.environ.get("beaker.session")
    return session.get("user", {"is_authenticated": False})


# ==== Views and routes ====


@bottle_app.route("/")
def home():
    all_posts = get_all_posts()
    page = int(request.query.get("page", "1"))
    per_page = 5
    posts_paginated = paginate_items(all_posts, page, per_page)
    user = get_current_user()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return template("pejapp/post_list", posts=posts_paginated, user=user, _env=env)
    else:
        return template("pejapp/home", posts=posts_paginated, user=user, _env=env)


@bottle_app.route("/register", method=["GET", "POST"])
def register():
    user = get_current_user()
    if request.method == "POST":
        username = request.forms.getunicode("username")
        email = request.forms.getunicode("email")
        password = request.forms.getunicode("password")
        confirm_password = request.forms.getunicode("confirm_password")

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
        username = request.forms.getunicode("username")
        password = request.forms.getunicode("password")
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
        title = request.forms.getunicode("title")
        content = request.forms.getunicode("content")
        user_id = user["id"]
        create_post(title, content, user_id)
        redirect("/")
    return template("pejapp/create_post", user=user, _env=env)


@bottle_app.route("/user/<username>")
def user_profile(username):
    row = get_user_by_username(username)
    if not row:
        return "Użytkownik nie istnieje"
    profile_user = dict(row)
    if "bio" not in profile_user:
        profile_user["bio"] = ""

    posts_list = get_posts_by_user(profile_user["id"])
    filters = {
        "search": request.query.get("search", ""),
        "start_date": request.query.get("start_date", ""),
        "end_date": request.query.get("end_date", ""),
        "sort": request.query.get("sort", "desc"),
    }

    if filters["search"]:
        posts_list = [
            post
            for post in posts_list
            if filters["search"].lower() in (post.get("title") or "").lower()
            or filters["search"].lower() in (post.get("content") or "").lower()
        ]
    if filters["start_date"]:
        posts_list = [
            post for post in posts_list if post["date_posted"] >= filters["start_date"]
        ]
    if filters["end_date"]:
        posts_list = [
            post for post in posts_list if post["date_posted"] <= filters["end_date"]
        ]
    reverse = True if filters["sort"] == "desc" else False
    posts_list.sort(key=lambda post: post["date_posted"], reverse=reverse)

    page = int(request.query.get("page", "1"))
    per_page = 10
    posts_paginated = paginate_items(posts_list, page, per_page)

    current = get_current_user()
    is_owner = current.get("is_authenticated") and (current.get("username") == username)

    return template(
        "pejapp/user_profile",
        profile_user=profile_user,
        posts=posts_paginated,
        is_owner=is_owner,
        current_user=current,
        user=current,
        filters=filters,
        _env=env,
    )


@bottle_app.route("/search", method=["GET"])
def search():
    query = request.query.get("q")
    db = get_db()
    query_str = "%" + query + "%"
    raw_posts = db.execute(
        "SELECT posts.*, users.username, users.email FROM posts JOIN users ON posts.author_id = users.id WHERE posts.title LIKE ?",
        (query_str,),
    ).fetchall()
    raw_users = db.execute(
        "SELECT * FROM users WHERE username LIKE ?", (query_str,)
    ).fetchall()
    posts = convert_post_rows(raw_posts, text_limit=30)
    post_page = int(request.query.get("post_page", "1"))
    user_page = int(request.query.get("user_page", "1"))
    per_page = 5
    posts_paginated = paginate_items(posts, post_page, per_page)
    users_paginated = paginate_items(list(raw_users), user_page, per_page)
    user = get_current_user()
    ajax = request.query.get("ajax")
    if ajax == "posts":
        return template(
            "pejapp/post_search_results",
            posts=posts_paginated,
            query=query,
            user=user,
            _env=env,
        )
    elif ajax == "users":
        return template(
            "pejapp/user_search_results",
            users=users_paginated,
            query=query,
            user=user,
            _env=env,
        )
    else:
        return template(
            "pejapp/search_results",
            posts=posts_paginated,
            users=users_paginated,
            query=query,
            user=user,
            _env=env,
        )


@bottle_app.route("/user/<username>/update", method=["GET", "POST"])
def update_profile(username):
    current = get_current_user()
    if not (current.get("is_authenticated") and current.get("username") == username):
        return "Nie masz uprawnień do edycji tego profilu."

    row = get_user_by_username(username)
    if not row:
        return "Użytkownik nie istnieje"
    user_record = dict(row)
    if "bio" not in user_record or user_record["bio"] is None:
        user_record["bio"] = ""

    if request.method == "POST":
        new_username = request.forms.getunicode("username")
        new_email = request.forms.getunicode("email")
        new_bio = request.forms.getunicode("bio")

        if new_username != username and get_user_by_username(new_username):
            return template(
                "pejapp/update_profile",
                error="Użytkownik o podanej nazwie już istnieje.",
                user=user_record,
                _env=env,
            )

        db = get_db()
        db.execute(
            "UPDATE users SET username = ?, email = ?, bio = ? WHERE id = ?",
            (new_username, new_email, new_bio, user_record["id"]),
        )
        db.commit()

        session = request.environ.get("beaker.session")
        updated = get_user_by_username(new_username)
        updated_obj = dict(updated)
        updated_obj["is_authenticated"] = True
        session["user"] = updated_obj
        session.save()
        redirect(f"/user/{new_username}")

    return template("pejapp/update_profile", user=user_record, _env=env)


@bottle_app.route("/post-update/<post_id>", method=["GET", "POST"])
def post_update(post_id):
    db = get_db()
    current = get_current_user()
    # Pobieramy posta wraz z danymi autora
    query = """
        SELECT posts.*, users.username, users.email 
        FROM posts 
        JOIN users ON posts.author_id = users.id 
        WHERE posts.id = ?
    """
    row = db.execute(query, (post_id,)).fetchone()
    if not row:
        return "Post nie istnieje"
    post = convert_post_row_full(row)
    # Sprawdzamy, czy aktualny użytkownik jest autorem posta
    if not (
        current.get("is_authenticated")
        and current.get("username") == post["author"]["username"]
    ):
        return "Brak uprawnień do edycji tego posta"

    if request.method == "POST":
        new_title = request.forms.getunicode("title")
        new_content = request.forms.getunicode("content")
        now = datetime.datetime.now().isoformat()
        # Jeśli post nie był wcześniej modyfikowany, zachowujemy oryginalną treść
        if not post.get("modified_flag"):
            original_content = post["content"]
        else:
            original_content = post.get("original_content", "")
        db.execute(
            "UPDATE posts SET title = ?, content = ?, last_modified = ?, modified_flag = 1, original_content = ? WHERE id = ?",
            (new_title, new_content, now, original_content, post_id),
        )
        db.commit()
        redirect("/user/" + current.get("username"))

    return template("pejapp/post_update", post=post, user=current, _env=env)


@bottle_app.route("/post-delete/<post_id>", method=["POST"])
def post_delete(post_id):
    db = get_db()
    current = get_current_user()
    # Pobieramy posta wraz z danymi autora
    query = """
        SELECT posts.*, users.username 
        FROM posts 
        JOIN users ON posts.author_id = users.id 
        WHERE posts.id = ?
    """
    row = db.execute(query, (post_id,)).fetchone()
    if not row:
        return "Post nie istnieje"
    post = convert_post_row_full(row)
    # Sprawdzamy, czy aktualny użytkownik jest autorem posta
    if not (
        current.get("is_authenticated")
        and current.get("username") == post["author"]["username"]
    ):
        return "Brak uprawnień do usunięcia tego posta"
    db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    db.commit()
    redirect("/user/" + current.get("username"))


@bottle_app.route("/static/<filepath:path>")
def static_files(filepath):
    return static_file(filepath, root=STATIC_PATH)


# ==== Session configuration ====
app = SessionMiddleware(bottle_app, session_opts)

# ==== Launching application ====
if __name__ == "__main__":
    if not os.path.exists(DATABASE):
        init_db()
    from bottle import run

    run(app=app, host="localhost", port=8081, debug=True, reloader=True)
