from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import PIL
from PIL import Image
import os
from dotenv import load_dotenv
import stripe
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
# Project py files.
from cart import Cart
from form import PurchaseForm, NewProductForm, LoginForm, RegisterForm


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLITE')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
carts = Cart()
# Stripe parameters
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
MY_DOMAIN = 'http://localhost:5000'
# Enable login manager
login_manager = LoginManager()
login_manager.init_app(app)
product_id = []
price_id = []


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(250), unique=False, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    img = db.Column(db.String(250), nullable=False)
    
    def __repr__(self):
        return f'<Product List {self.title}>'


# Create the User Table
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    
    
# Only did this once.
# Flask-SQLAlchemy 3.0.x will create error in create_all(). Use 2.5.1.
# db.create_all()


@login_manager.user_loader
def load_user(user_email):
    return User.query.get(int(user_email))


def admin_only(fn):
    @wraps(fn)
    def decorated_function(*args, **kwargs):
        if not current_user.is_anonymous:
            if current_user.id == 1:
                return fn(*args, **kwargs)
        return abort(403)
    return decorated_function


# Only admin can add product.
@app.route("/add", methods=['GET', 'POST'])
@admin_only
def add():
    form = NewProductForm()
    if form.validate_on_submit():
        file = form.file.data
        try:
            with Image.open(file) as user_img:
                # Save a local copy for display purpose.
                filename = f'static/images/online/{file.filename}'
                user_img.save(filename)
        except PIL.UnidentifiedImageError:
            return 'error', file

        product = Product.query.filter_by(title=form.title.data).first()
        if product:
            # Update existing product.
            product.title = form.title.data
            product.category = form.category.data
            product.stock = form.stock.data
            product.price = form.price.data
            product.description = form.description.data
            product.img = filename
            flash('You have updated an existing product!')
        else:
            # Create new product.
            new_product = Product(
                title=form.title.data,
                category=form.category.data,
                stock=form.stock.data,
                price=form.price.data,
                description=form.description.data,
                img=filename,
            )
            db.session.add(new_product)
        db.session.commit()
    return render_template('add.html', form=form)


@app.route('/', methods=['GET', 'POST'])
def home():
    global product_id, price_id
    if current_user.is_authenticated:
        products = Product.query.all()
        return render_template('index.html', products=products, cart=len(carts.items))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        # db.email is set to have unique email
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('That email does not exist, please register.')
            return redirect(url_for('register'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again')
        else:
            # login_user will pass .id to user_loader
            login_user(user)
            return redirect(url_for('home'))
    return render_template("login.html", form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=request.form["email"]).first():
            flash("You have already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        hash_salted_password = generate_password_hash(
            request.form["password"],
            method='pbkdf2:sha256',
            salt_length=8
            )
        new_user = User(
            name=request.form['name'],
            email=request.form['email'],
            password=hash_salted_password,
            )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template("register.html", form=form)


@app.route('/buy', methods=['GET', 'POST'])
def buy():
    product = Product.query.filter_by(id=request.args.get('id')).first()
    form = PurchaseForm()
    if form.validate_on_submit():
        carts.add_item(product, int(form.qty.data))
        return redirect(url_for('home'))
    return render_template('product.html', product=product, form=form, cart=len(carts.items))
    
    
# Stripe
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {'price': stripe.Product.retrieve(f'prod_SGD{item.product.id}').default_price, 'quantity': item.qty} for
                item in carts.items],
            mode='payment',
            success_url=MY_DOMAIN + '/success',
            cancel_url=MY_DOMAIN + '/cancel',
        )
        print(checkout_session)
    except Exception as e:
        return str(e)
    return redirect(checkout_session.url, code=303)


@app.route('/success')
def success():
    return render_template('success.html')


@app.route('/cancel',)
def cancel():
    return render_template('cancel.html')


def create_stripe_product():
    products = Product.query.all()
    # Remove product that not associated with price.
    for product in stripe.Product.list():
        try:
            stripe.Product.delete(product.id)
        except stripe.error.InvalidRequestError:
            pass
    # Create product and price IDs for stripe.
    for product in products:
        try:
            pid = stripe.Product.create(id=f'prod_SGD{product.id}', name=product.title, images=[f'{MY_DOMAIN}/{product.img}'])
        except Exception as e:
            print(str(e))
        # Handle error if price already exist.
        try:
            ppid = stripe.Price.create(product=f'prod_SGD{product.id}', unit_amount_decimal=str(product.price*100), currency="sgd")
            stripe.Product.modify(f'prod_SGD{product.id}', default_price=ppid.id)
        except Exception as e:
            print(str(e))
        
        
# Create stripe product list, need only once. Can also do it at Stripe's dashboard.
# create_stripe_product()
# print(stripe.Product.list())
# print('===')
# print(stripe.Price.list())

if __name__ == "__main__":
    app.run()
