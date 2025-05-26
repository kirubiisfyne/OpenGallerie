from flask import Flask, render_template, request, session, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.secret_key = '1234'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    
    portfolio = db.relationship('Portfolio', back_populates='user', lazy=True, uselist=False)
class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.JSON, nullable=True) 

    user = db.relationship('User', back_populates='portfolio', lazy=True, uselist=False) 
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_filename = db.Column(db.Text, nullable=False)
    image_description = db.Column(db.Text, nullable=True)
    date_uploaded = db.Column(db.DateTime, default=datetime.utcnow)

    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=False)
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
            session['user_id'] = user.id
            return redirect(url_for('open_gallery', user=user))
        else:
            return redirect(url_for('signup_redirect', error="User not found"))
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

                new_portfolio = Portfolio(user_id=new_user.id, user=new_user)
                db.session.add(new_portfolio)
                db.session.commit() 

                session['user_id'] = new_user.id

                return redirect(url_for('open_gallery', user=new_user))
        except Exception as e:
            print(f"Error creating user: {e}")
            return render_template('signup.html', error="Error creating user")
    else:
        return render_template('signup.html')

@app.route('/open_gallery', methods=['GET'])
def open_gallery():
    images = Image.query.all()
    user = User.query.filter_by(id=session.get('user_id')).first()
    if not images:
        print("No images found in the database")
    return render_template('open_gallery.html', images=images, user=user)

@app.route('/delete_account', methods=['POST', 'GET'])
def delete_account():
    if request.method == 'POST':
        user_id = session.get('user_id')
        user = User.query.filter_by(id=user_id).first()
        if user:
            for image in user.portfolio.images:
                db.session.delete(image)
            db.session.delete(Portfolio.query.filter_by(user_id=user.id).first())
            db.session.delete(user)
            db.session.commit()
            return render_template('login.html', message="Account deleted successfully")
        else:
            return redirect(url_for('open_gallery', error="User not found"))
    else:
        return redirect(url_for('open_gallery'))


@app.route('/upload_image', methods=['POST', 'GET'])
def upload_image():
    if 'image' not in request.files:
        return render_template('upload_image.html')
    
    user_id = session.get('user_id')
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return "User not found"

    if request.method == 'POST':
        file = request.files.get('image')
        title = request.form.get('filename')
        description = request.form.get('description')
        
        if Image.query.filter_by(image_filename=title).first():
            flash('Image with this filename already exists!', 'error')
            return redirect(url_for('upload_image'))

        if file.filename == '':
            return "No selected file"
        if file and allowed_file(file.filename):
            portfolio = user.portfolio
            portfolio_id = portfolio.id   

            new_file = Image(portfolio_id=portfolio_id, portfolio=portfolio, image_filename=title, image_description=description)
            db.session.add(new_file)
            db.session.commit()

            file.save(os.path.join('static/uploads', title))

            return redirect(url_for('display_profile'))
        else:
            return flash('No file selected!', 'error')
    
@app.route('/display_profile', methods=['GET'])
def display_profile():
    user_id = session.get('user_id')
    user = User.query.filter_by(id=user_id).first()

    images = user.portfolio.images if user and user.portfolio else []
    return render_template('profile.html', user=user, images=images)

@app.route('/delete_image', methods=['POST', 'GET'])
def delete_image():
    if request.method == 'POST':
        image_filename = request.form.get('image_filename')
        image = Image.query.filter_by(image_filename=image_filename).first()
        if image:
            file_path = os.path.join('static/uploads', image_filename)

            if os.path.exists(file_path):
                os.remove(file_path)
            else:
                print("File does not exist, cannot delete")

            db.session.delete(image)
            db.session.commit()
            flash('Image deleted successfully', 'success')
        else:
            flash('Image not found', 'error')
    return redirect(url_for('display_profile'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000,debug=True)