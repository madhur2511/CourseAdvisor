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
app.config['MYSQL_DB'] = 'courseadvisor'
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
    updateDB(json.loads(userInfo))
    return render_template('homepage.html')


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
    try:
        courseNumber = request.args.get('courseNumber')
        return json.dumps(getCourseInfoFromDB(courseNumber))
    except Exception as e:
        return json.dumps({'status':'Bad Request', 'reason' : e})

@app.route('/multiplecourses', methods=['GET'])
def compareCourses():
    try:
        courseNumber1 = request.args.get('courseNumber1')
        courseNumber2 = request.args.get('courseNumber2')
        courseNumber3 = request.args.get('courseNumber3')
        return json.dumps(getCoursesInfoFromDB(courseNumber1, courseNumber2, courseNumber3))
    except Exception as e:
        return json.dumps({'status':'Bad Request', 'reason' : e})

def getCoursesInfoFromDB(courseNumber1, courseNumber2, courseNumber3):
    courseJson1 = getCourseInfoFromDB(courseNumber1)
    courseJson2 = getCourseInfoFromDB(courseNumber2)
    courseJson3 = getCourseInfoFromDB(courseNumber3)

    return courseJson1['Easiness'] + courseJson2['Easiness'] + courseJson['Easiness']


def getCourseInfoFromDB(courseNumber):
    courseNumber = courseNumber.upper()
    conn = mysql.connection
    cur = conn.cursor()
    cur.execute("SELECT * FROM courses WHERE cnum='%s'" % (courseNumber))
    data = cur.fetchall()[0]

    courseJson = {}
    courseJson['cnum'] = data[5]
    courseJson['name'] = data[1]
    courseJson['description'] = data[2]
    courseJson['level'] = data[3]
    courseJson['department'] = data[4]

    cur1 = conn.cursor()
    cur1.execute("SELECT rating.rid, mapping.cid, rating.easiness, rating.iRel, rating.tExp, rating.grade, rating.fun, rating.participation FROM rating INNER JOIN mapping ON rating.rid = mapping.rid WHERE mapping.cid = %s" % (data[0]))
    averageData = cur1.fetchall()
    params = [0.0] * 6
    if len(averageData) >= 1:
        for data in averageData:
            for i, d in enumerate(data[2:]):
                params[i] += d
        params = [param / len(averageData) for param in params]

    courseJson['Easiness'] = params[0]
    courseJson['Industry Relevance'] = params[1]
    courseJson['Time Expense'] = params[2]
    courseJson['Grading'] = params[3]
    courseJson['Overall Experience'] = params[4]
    courseJson['Class Participation'] = params[5]

    return courseJson


def updateDB(userInfo):
    _email  = userInfo['email']
    _name   = userInfo['name']
    _gender = userInfo['gender']

    if _name and _email and _gender:
        conn = mysql.connection
        cur = conn.cursor()
        cur.execute("SELECT * FROM student WHERE name='%s'" % (_name))
        data = cur.fetchall()

        if len(data) is 0:
            _gender = 1 if _gender == 'male' else 0
            cur.execute("""INSERT INTO student (name, email, gender) VALUES (%s, %s, %s);""", (_name, _email, _gender))
            conn.commit()
            return {'message':'User created successfully !'}
    else:
        return json.dumps({'html':'<span>Enter the required fields</span>'})



if __name__ == "__main__":
    app.run()
