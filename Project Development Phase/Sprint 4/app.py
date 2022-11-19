create a flask app
import re
import ibm_db
from flask import Flask, flash, render_template, request, redirect, url_for, session
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')
app.secret_key = 'sus'
conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=1bbf73c5-d84a-4bb0-85b9-ab1a4348f4a4.c3n41cmd0nqnrk39u98g.databases.appdomain.cloud;PORT=32286;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=htq60326;PWD=nI8y1DzMccwV4Ub7;","","")

 print("Connected to database", conn)

session = {}


# route for sending email
@app.route('/sendemail')
def sendemail():
    id=session["id"]
    sql="select email from users1 WHERE id=?;"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, id)
    ibm_db.execute(stmt)
    data = ibm_db.fetch_assoc(stmt)
    print(data) 

    message = Mail(from_email='vijiaya.raj@gmail.com',to_emails=data['EMAIL'],subject='CONTAINMENT ZONE ALERT!!!',html_content='<strong>OPPS!<br> YOU HAVE ENTERED A CONTAMINATED ZONE! <br> PLEASE STAY SAFE.</strong>')
    try:
        sg = SendGridAPIClient('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')
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)

    return render_template('home.html')
            


# create a route for the home page
@app.route('/', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST':
        # get the data from the form
        name = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        # if nothing is entered in the form
        if not name or not email or not password or not confirm_password:
            message = 'Please fill all the fields!'
            return render_template('register.html', message=message)
        # if the password and confirm password do not match
        elif password != confirm_password:
            message = 'Passwords do not match!'
            return render_template('register.html', message=message)

        #  password length must be 8 or above
        if len(password) < 8:
            message = 'Password must be 8 or more characters'
            return render_template('register.html', message=message)
        # check if the email is valid
        if re.match(r"[^@]+@[^@]+\.[^@]+", email):
            # insert the data into the database
            # check if email already exists in the database
            sql = "SELECT * FROM users1 WHERE email = '" + email + "'"
            stmt = ibm_db.exec_immediate(conn, sql)
            # print("stmt", stmt)
            result = ibm_db.fetch_assoc(stmt)
            # print("result", result)
            if result:
                message = 'The username or email already exists!'
            else:
                sql = "INSERT INTO users1 ( username, email, password,type) VALUES (?, ?, ?, ?)"
                stmt = ibm_db.prepare(conn, sql)
        
                ibm_db.bind_param(stmt, 1, name)
                ibm_db.bind_param(stmt, 2, email)
                ibm_db.bind_param(stmt, 3, password)
                ibm_db.bind_param(stmt, 4, "ssss")
                ibm_db.execute(stmt)
                message = 'You have successfully registered!'
                return redirect(url_for('login'))
        else:
            message = 'The email is invalid!'
    return render_template('register.html', message=message)


@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST':
        # get the data from the form
        email = request.form['email']
        password = request.form['password']
        # if nothing is entered in the form
        if not email or not password:
            message = 'Please fill all the fields!'
            return render_template('login.html', message=message)
        # check if the username and password are valid
        sql = "SELECT * FROM users1 WHERE email = '" + email + "' AND password = '" + password + "'"
        stmt = ibm_db.exec_immediate(conn, sql)
        result = ibm_db.fetch_assoc(stmt)
        # print("result", result)
        if result:
            # message = 'You have successfully logged in!'
            session['id'] = result['ID']
            session['username'] = result['USERNAME']
            session['email'] = result['EMAIL']
            # print("id ==", session['id'])
            return render_template('home.html', mail=email)
        else:
            message = 'The email or password is incorrect!'
    return render_template('login.html', message=message)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# create a route for the home page and open only if the user is logged in
@app.route('/home', methods=['GET', 'POST'])
def home():
    # print(name)

    if 'id' in session:
        if request.method == 'GET':
            return render_template('home.html', name=session['username'])
        if request.method == "POST":
            # get data
            lat = request.form["lat"]
            lon = request.form["lon"]
            sql = "SELECT * FROM inf_location WHERE locate_lat = ? AND locate_lang = ?;"

            stmt = ibm_db.prepare(conn, sql)

            ibm_db.bind_param(stmt, 1, lat)
            ibm_db.bind_param(stmt, 2, lon)

            ibm_db.execute(stmt)
            data = ibm_db.fetch_assoc(stmt)
            if (data)!=0:

                flash("OOH!! You Have Entered A Contaminated Zone")
                return redirect(url_for('sendemail'))

            else:
                flash("You Are in Safe Zone")
                return redirect(url_for('home'))    

        return render_template('home.html')
    else:
        return redirect(url_for('login'))      
                      
           
           


# create a route for the data page and open only if the user is logged in
@app.route('/data')
def data():
    if 'id' not in session:
        return redirect(url_for('login'))
    else:
        # create a query to fetch the data from the database
        sql = "SELECT * FROM inf_location"
        stmt = ibm_db.exec_immediate(conn, sql)
        # print("stmt", stmt)
        # fetch all the data from the database and store it in the result dictionary
        result = ibm_db.fetch_assoc(stmt)

        # create a list to store the data
        data = []
        # loop through the result dictionary and append the data to the list
        while result:
            data.append(result)
            result = ibm_db.fetch_assoc(stmt)
        # print(data)
        return render_template('data.html', data=data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
