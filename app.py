from flask import Flask, render_template, url_for, request, redirect, jsonify, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.JSON, nullable=True)

    user = db.relationship('User', backref='portfolio', lazy=True, uselist=False)
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=False)
    image_filename = db.Column(db.Text, nullable=False)
    date_uploaded = db.Column(db.DateTime, default=datetime)

    portfolio = db.relationship('Portfolio', backref='images', lazy=True)

def to_dict(self):
        return {
            'username': self.username,
            'email': self.email,
        }

@app.route('/', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first() # Query the database for the user

        if user: # Checks if the user exists
            print(f"User ID: {user.id}")
            return render_template('open_gallery.html', user=user)
        else:
            return render_template('signup_redirect.html', error="User not found")
    else:
        return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        new_user = User(username=username, email=email, password=password)
        try:
            user = User.query.filter_by(username=username).first() # Query the database for the user
            if user: # Checks if the user exists
                return render_template('signup.html', error="User already exists")
            else:
                db.session.add(new_user)
                db.session.commit()

                return render_template('open_gallery.html', user=new_user)
        except Exception as e:
            print(f"Error creating user: {e}")
            return render_template('signup.html', error="Error creating user")
    else:
        return render_template('signup.html')

@app.route('/open_gallery', methods=['POST', 'GET'])
def delete_account():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        print(user_id)
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return render_template('login.html', message="Account deleted successfully")
        else:
            return render_template('open_gallery.html', error="User not found")
    else:
        return render_template('open_gallery.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000,debug=True)