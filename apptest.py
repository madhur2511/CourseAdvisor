from flask import Flask, redirect, url_for, session, request, jsonify
from flask_oauthlib.client import OAuth


app = Flask(__name__)
app.config['GOOGLE_ID'] = "GOOGLEID"
app.config['GOOGLE_SECRET'] = "GOOGLESECRET"
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


@app.route('/')
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
            # Unauthorized - bad token
            session.pop('access_token', None)
            return redirect(url_for('login'))
        return res.read()

    return res.read()


@app.route('/login')
def login():
    callback=url_for('authorized')
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



if __name__ == '__main__':
    app.run()
