from flask import Flask, render_template, request, redirect, session, flash
import os, binascii, hashlib
from mysqlconnection import MySQLConnector
from flask_bcrypt import Bcrypt
app = Flask(__name__)
bcrypt = Bcrypt(app)
mysql = MySQLConnector(app,'the_wall')
app.secret_key = 'shushmans'
import re
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/register', methods=['POST'])
def create():

    query= "INSERT INTO  users(first_name, last_name, email, password) VALUES (:first_name,:last_name, :email, :password )"
    pw_hash = bcrypt.generate_password_hash(request.form['password'])
    values = {
    'first_name': request.form['first_name'],
    'last_name': request.form['last_name'],
    'email': request.form['email'],
    'password': pw_hash
    }
    if len(request.form['first_name'])<2:
        flash('INVALID FIRST NAME')
    if len(request.form['last_name'])<2:
        flash('INVALID LAST NAME')
    elif not EMAIL_REGEX.match(request.form['email']):
        flash('INVALID EMAIL')
    elif len(request.form['password']) <8:
        flash('8 CHARACTER MINIMUM')
    elif request.form['password'] != request.form['confirmation']:
        flash('PASSWORD AND CONFIRMATION DO NOT MATCH')
    else:
        mysql.query_db(query,values)
    return redirect('/')

@app.route('/verify', methods=['post'])
def verification():
    email=request.form['login_email']
    password=request.form['login_password']
    print password

    query = "SELECT * FROM users WHERE email = :email"
    data = {
            'email': email
    }
    returnData=mysql.query_db(query, data)
    if len(returnData) > 0:
        if bcrypt.check_password_hash(returnData[0]['password'], password):
            returnData[0].pop('password', None)
            session['name'] = returnData[0]['first_name']
            session['id'] = returnData[0]['id']
            return redirect('/wall')
    flash('INVALID CREDENTIALS')
    return redirect('/')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/wall')
def load_wall():
    query= 'SELECT first_name, last_name, message, messages.id, messages.created_at FROM users JOIN messages ON messages.users_id = users.id ORDER BY messages.created_at DESC'
    messages = mysql.query_db(query)

    query='SELECT first_name, last_name, comment, message_id, comments.created_at FROM users JOIN comments ON comments.user_id = users.id ORDER BY comments.created_at DESC'


    comments = mysql.query_db(query)
    print messages[0]['id']
    return render_template('wall.html', messages=messages, comments=comments)

@app.route('/post', methods=['POST'])
def post_to_wall():
    query= "INSERT INTO  messages(users_id, message, created_at) VALUES (:users_id, :message, NOW())"
    values= {
    'users_id': session['id'],
    'message': request.form['post_text']
    }
    mysql.query_db(query,values)

    return redirect ('/wall')

@app.route('/comment', methods=['POST'])
def post_comment_to_wall():
    query= "INSERT INTO  comments(user_id, message_id, comment, comments.created_at) VALUES (:user_id, :message_id, :comment, NOW())"
    values= {
    'user_id': session['id'],
    'message_id': request.form['post_id'],
    'comment': request.form['comment_text']

    }
    mysql.query_db(query,values)

    return redirect ('/wall')

app.run(debug=True)
