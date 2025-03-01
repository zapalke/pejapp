from bottle import Bottle, run, jinja2_template as template
from models import session, User
import bottle

bottle.TEMPLATE_PATH.clear()
bottle.TEMPLATE_PATH.append("./templates")
app = Bottle()


@app.route("/")
def index():
    return template("index")


@app.route("/users")
def users():
    users_list = session.query(User).all()
    return template("users", users=users_list)


if __name__ == "__main__":
    run(app, host="localhost", port=8081, debug=True, reloader=True)
