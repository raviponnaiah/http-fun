from flask import Flask, request, make_response, session, abort, redirect
app = Flask(__name__)

from datetime import datetime


ASCII_HELLO = """
.................##...##..######..##.......####....####...##...##..######..........######...####..................
.................##...##..##......##......##..##..##..##..###.###..##................##....##..##.................
.................##.#.##..####....##......##......##..##..##.#.##..####..............##....##..##.................
.................#######..##......##......##..##..##..##..##...##..##................##....##..##.................
..................##.##...######..######...####....####...##...##..######............##.....####..................
..................................................................................................................
.........##..##...####....####...##..##..######..#####....####...##..##..######..#####.....##.....####..........  
.........##..##..##..##..##..##..##.##...##......##..##..##......##..##....##....##..##....##....##.............  
.........######..######..##......####....####....#####....####...######....##....#####......#.....####..........  
.........##..##..##..##..##..##..##.##...##......##..##......##..##..##....##....##..................##.........  
.........##..##..##..##...####...##..##..######..##..##...####...##..##..######..##...............####..........  
................................................................................................................  
.................##..##..######..######..#####...........######..##..##..##..##.................................  
.................##..##....##......##....##..##..........##......##..##..###.##.................................  
.................######....##......##....#####...........####....##..##..##.###.................................  
.................##..##....##......##....##..............##......##..##..##..##.................................  
.................##..##....##......##....##..............##.......####...##..##.................................  
................................................................................................................  
"""

### Hello world, Chapter 1

@app.route("/")
def hello():
    if request.headers.get("User-Agent") == "Terminal":
        return ASCII_HELLO

    return "Hello World!"


### Playing with cookies
### In order of appereance

@app.route('/cookie/set')
def cookies_set():
    name = request.args.get("name", "Test")
    resp = make_response("Name accepted")
    resp.set_cookie("name", name)
    return resp


@app.route('/cookie/secret-room')
def cookies_secret_room():
    name = request.cookies.get("username", False)

    if not name:
        abort(401)

    resp = make_response("Hello {}".format(name))
    return resp


@app.route('/cookie/login')
def cookies_login():
    name = request.args.get("username", False)
    password = request.args.get("password", False)
    print name, password
    if not password == "password" or not name:
        abort(401)

    resp = make_response("You are now authorized")
    resp.set_cookie("username", name)
    return resp

### Sessions

@app.route("/session/secret-room")
def session_secret():
    name = session.get("username", False)
    if not name:
        abort(401)

    resp = make_response("""Hello {},
You logged in at {}
""".format(name, session.get("login-time")))
    return resp


@app.route('/session/login')
def session_login():
    name = request.args.get("username", False)
    password = request.args.get("password", False)
    print name, password
    if not password == "password" or not name:
        abort(401)

    resp = make_response("You are now authorized")
    session['username'] = name
    session['login-time'] = datetime.now()
    return resp


@app.route('/resource_manager', methods=['GET', 'POST', 'PUT'])
def resource_manager():
    if "resources" not in session:
        session["resources"] = {"car": "mustang",
                                "cake": "cheesecake",
                                "drink": "zombie"}
    method = request.method
    if request.method == 'PUT':
        session['resources'] = request.form

    elif request.method == 'POST':
        for key, value in request.form.iteritems():
            session['resources'][key] = value

    return "Your current resources:\n   {}".format(
                "\n   ".join(map(lambda x: ": ".join(x),
                    session["resources"].items())))


@app.route('/resource_manager/<item>', methods=['POST', 'PUT', 'GET', 'DELETE'])
def resource_item_manager(item):
    if "resources" not in session:
        session["resources"] = {}

    if request.method == 'DELETE':
        del session['resources'][item]
    elif request.method == "PUT":
        session['resources'][item] = request.data
    return session['resources'].get(item, "")

# Status code lol cats
@app.route('/status/<int:code>')
def status_codes(code):
    resp = make_response('<img src="http://httpcats.herokuapp.com/{}" />'.format(code), code)
    if code in [301, 302, 307]:
        resp.location = "http://www.hackership.org/"
    return resp


# Redirects
# Status code lol cats
@app.route('/redirect/simple')
def redirect_simple():
    return redirect("/")


@app.route('/redirect/bounce')
def redirect_bounce():
    return redirect('/redirect/back')


@app.route('/redirect/back')
def redirect_back():
    return redirect('/redirect/bounce')


@app.route('/redirect/permanent')
def redirect_permanent():
    return redirect('/', 301)


@app.route('/redirect/old/<path:path>')
@app.route('/redirect/old')
def redirect_old(path=''):
    return redirect('http://www.hackership.org/' + path, 301)


@app.route('/redirect/restricted')
def redirect_restricted():
    if not request.args.get("accepted"):
        return redirect('/redirect/login', 303)
    return "Access granted!"


@app.route('/redirect/login', methods=["POST", "GET"])
def redirect_login():
    if request.method == "POST":
        return redirect('/redirect/restricted?accepted=1', 303)
    return "You need to POST 'username=test' to this page to login"

# HTTP Auth

from functools import wraps
import authdigest
import flask

class FlaskRealmDigestDB(authdigest.RealmDigestDb):
    def requires_auth(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            request = flask.request
            if not self.isAuthenticated(request):
                return self.challenge()

            return f(*args, **kwargs)

        return decorated

authDB = FlaskRealmDigestDB('Example Auth')
authDB.addUser('user', 'password')

@app.route('/auth/basic')
def auth_restricted():
    if not request.headers.get("Authorization"):
        abort(401)
    return "Access Granted"

@app.route("/auth/digest")
@authDB.requires_auth
def auth_digest():
    return "Yay, you are {}".format(request.authorization.username)


if __name__ == "__main__":
    app.secret_key = "complicatedHash"
    app.run(debug=True, host="0.0.0.0", port=8080)
