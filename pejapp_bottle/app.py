from bottle import Bottle, run, jinja2_template as template
import views
import auth
import bottle

bottle.TEMPLATE_PATH.clear()
bottle.TEMPLATE_PATH.append("./templates")

app = Bottle()

app.merge(views.views)
app.merge(auth.auth)


@app.route("/")
def index():
    return template("index")


if __name__ == "__main__":
    run(app, host="localhost", port=8081, debug=True, reloader=True)
