from flask import Flask, render_template, request, redirect, session, flash
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
app= Flask(__name__)
app.secret_key = 'My super secret key'
bcrypt = Bcrypt(app)

import re
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

@app.route('/home')
def begin():
    return render_template("index.html")

@app.route('/adduser', methods=['POST'])
def register():
    is_valid = True
    if len(request.form['first_name']) < 2:
        is_valid = False
        flash("Please enter a first name")
    if len(request.form['last_name']) < 2:
        is_valid = False
        flash("Please enter a last name")
    if not EMAIL_REGEX.match(request.form['email']):
        is_valid= False
        flash("Invalid email address!")
    if len(request.form['password']) < 8:
        is_valid = False
        flash("Please enter a password with at least 8 characters")
    if request.form['password'] != request.form['confirm']:
        is_valid = False
        flash("Passwords must match")
    mysql = connectToMySQL("privatewall")
    query = "SELECT * FROM users WHERE email= %(email)s;"
    data = {
        "email": request.form["email"],
        }
    result = mysql.query_db(query, data)
    if len(result) > 0:
        is_valid=False
        flash("Email already used")
    if not is_valid:
        return redirect("/home")

    else:
        pw_hash = bcrypt.generate_password_hash(request.form['password'])
        mysql = connectToMySQL("privatewall")
        query = "INSERT INTO users (first_name, last_name, email, password) VALUES (%(first_name)s, %(last_name)s, %(email)s, %(password_hash)s);"
        data = {
            "first_name": request.form['first_name'],
            "last_name": request.form['last_name'],
            "email": request.form["email"],
            "password_hash": pw_hash ,
            }
        newuser = mysql.query_db(query, data)
        session['username'] = newuser
        print (newuser)
        flash("You have successfully registered!")
        return redirect('/welcome')

@app.route('/login', methods=['POST'])
def login():
    mysql = connectToMySQL("privatewall")
    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = { "email" : request.form["email"] }
    result = mysql.query_db(query, data)
    if len(result) > 0:
        if bcrypt.check_password_hash(result[0]['password'], request.form['password']):
            session['userid'] = result[0]['id']
            session['username'] = result[0]['first_name']
            return redirect('/welcome')
        else:
            flash('Invalid email/password combination')
    else:
        flash("Email not in database")
        return redirect("/home")

@app.route('/welcome')
def success():
    user_id = session['userid']
    mysql = connectToMySQL("privatewall")
    user = mysql.query_db('SELECT * FROM users')

    mysql = connectToMySQL("privatewall")
    query = "SELECT * FROM messages JOIN users on users.id= users_id WHERE rec_id = %(rec_id)s;" 
    data = {
            "rec_id": session['userid']
        }
    sender= mysql.query_db(query, data)
    mysql = connectToMySQL("privatewall")
    query = "SELECT * FROM users WHERE id != %(me)s;"
    data = {
            "me": session['userid']
        }
    recip = mysql.query_db(query, data)
    print(recip)
    return render_template("success.html", user=user[0], messages=sender, other=recip)

@app.route('/send', methods=['POST'])
def send():
    if len(request.form['messages']) < 5:
        flash("Please enter a first name")
    mysql = connectToMySQL("privatewall")
    query="INSERT INTO messages (messages, users_id, rec_id) VALUES (%(message)s, %(users_id)s, %(rec_id)s)"
    data={
        "message": request.form['messages'],
        "users_id": session['userid'],
        "rec_id": request.form['rec_id'],
    }
    sent= mysql.query_db(query, data)
    print(sent)
    return redirect ('/welcome')

@app.route('/messages/<message_id>/delete', methods=["POST"])
def delete(message_id):
    mysql = connectToMySQL("privatewall")
    query="DELETE FROM messages WHERE id = %(form_message)s"
    data={
        "form_message": message_id
    }
    mysql.query_db(query, data)
    return redirect('/welcome')


@app.route('/logout', methods=["POST"])
def logout():
    session.clear()
    return render_template("logout.html")

if __name__== "__main__":
    app.run(debug= True)