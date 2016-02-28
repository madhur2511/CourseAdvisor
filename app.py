from flask.ext.mysqldb import MySQL
from flask_oauthlib.client import OAuth
from flask import Flask, redirect, url_for, session, request, jsonify, json, render_template

app = Flask(__name__)
app.config['GOOGLE_ID'] = "554572499920-tgb7m9i8a8lbjvtbu0srrq50paq0oduj.apps.googleusercontent.com"
app.config['GOOGLE_SECRET'] = "3gGmjuO8He7e6FTyXniNls7p"
app.debug = True
app.secret_key = 'development'
oauth = OAuth(app)

google = oauth.remote_app(
    name='google',
    consumer_key=app.config.get('GOOGLE_ID'),
    consumer_secret=app.config.get('GOOGLE_SECRET'),
    request_token_params={
        'scope': 'email'
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth'
)

# MySQL configurations
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'BucketList'
app.config['MYSQL_HOST'] = 'localhost'

mysql = MySQL(app)


@app.route("/")
def index():
    access_token = session.get('access_token')
    if access_token is None:
        return redirect(url_for('login'))

    access_token = access_token[0]
    from urllib2 import Request, urlopen, URLError

    headers = {'Authorization': 'OAuth '+access_token}
    req = Request('https://www.googleapis.com/oauth2/v1/userinfo',
                  None, headers)
    try:
        res = urlopen(req)
    except URLError, e:
        if e.code == 401:
            session.pop('access_token', None)
            return redirect(url_for('login'))
        return res.read()

    userInfo = res.read()
    return updateDB(json.loads(userInfo))


def updateDB(userInfo):
    _email  = userInfo['email']
    _name   = userInfo['name']

    if _name and _email:
        conn = mysql.connection
        cur = conn.cursor()
        cur.execute("SELECT * FROM student WHERE name='%s'" % (_name))
        data = cur.fetchall()

        if len(data) is 0:
            cur.execute("""INSERT INTO student (name, email) VALUES (%s, %s);""", (_name, _email))
            conn.commit()
            return json.dumps({'message':'User created successfully !'})
    else:
        return json.dumps({'html':'<span>Enter the required fields</span>'})



@app.route('/login')
def login():
    callback=url_for('authorized', _external=True)
    return google.authorize(callback=callback)

@app.route('/login/authorized')
@google.authorized_handler
def authorized(resp):
    if resp is not None:
        access_token = resp['access_token']
        session['access_token'] = access_token, ''
        return redirect(url_for('index'))

@google.tokengetter
def get_access_token():
    return session.get('access_token')

@app.route('/singlecourse', methods=['GET'])
def getCourseInfo():
    return json.dumps({'course':'<span>'+request.args.get('course')+'</span>'})


@app.route('/multiplecourses', methods=['GET'])
def compareCourses():
    return json.dumps({'course':'<span>'+request.args.get('course')+'</span>'})


if __name__ == "__main__":
    app.run()
