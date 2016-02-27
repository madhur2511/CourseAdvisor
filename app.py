from flask.ext.mysqldb import MySQL
from flask import Flask, render_template, request, json
app = Flask(__name__)

# MySQL configurations
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'BucketList'
app.config['MYSQL_HOST'] = 'localhost'

mysql = MySQL(app)

@app.route("/")
def main():
     return render_template('index.html')

@app.route('/signUp',methods=['POST'])
def signUp():
    try:
        _name = request.form['inputName']
        _email = request.form['inputEmail']
        _password = request.form['inputPassword']

        if _name and _email and _password:
            conn = mysql.connection
            cur = conn.cursor()
            cur.execute("SELECT * FROM tbl_user WHERE user_name='%s'" % (_name))
            data = cur.fetchall()

            if len(data) is 0:
                cur.execute("""INSERT INTO tbl_user (user_name, user_username, user_password) VALUES (%s, %s, %s);""", (_name, _email, _password))
                conn.commit()
                return json.dumps({'message':'User created successfully !'})
            else:
                return json.dumps({'error':str(data[0])})
        else:
            return json.dumps({'html':'<span>Enter the required fields</span>'})

    except Exception as e:
        return json.dumps({'error':str(e)})


@app.route('/showSignUp')
def showSignUp():
    return render_template('signup.html')

app.run(debug=True)

if __name__ == "__main__":
    app.run()
