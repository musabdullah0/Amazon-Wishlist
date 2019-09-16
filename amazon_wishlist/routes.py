import os
import secrets
from apscheduler.schedulers.blocking import BlockingScheduler
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from amazon_wishlist import app, db, bcrypt
from amazon_wishlist.forms import ItemForm, RegistrationForm, LoginForm, UpdateAccountForm, UpdateItemForm
from amazon_wishlist.models import User, Item
from flask_login import login_user, current_user, logout_user, login_required
from amazon_wishlist.scraper import Scraper


scheduler = BlockingScheduler()
scheduler.add_executor('processpool')
scheduler.add_job(Scraper.update_db, 'interval', seconds=30)


@app.route('/')
def home():
    items = Item.query.all()
    return render_template('home.html', title='Home', items=items)


@app.route('/add', methods=['GET', 'POST'])
def add():
    form = ItemForm()
    if form.validate_on_submit():
        title, price = Scraper.amazon_parser(form.asin.data)
        if title and price and price > float(form.alert_price.data):
            item = Item(asin=form.asin.data, title=title, price=price, alert_price=form.alert_price.data, author=current_user)
            db.session.add(item)
            db.session.commit()
            flash('you added an item', 'success')
            return redirect(url_for('home'))
        elif float(form.alert_price.data) == price:
            flash('please select a different alert price', 'warning')
        else:
            flash('u did something wrong fam', 'danger')
    return render_template('add_item.html', title='Add Item', form=form, legend='Add Item')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('try again fam', 'danger')
    return render_template('login.html', title='Log In', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(password=form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Sign Up', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


@app.route('/item/<int:item_id>')
def item(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template('item.html', title=item.title, item=item)


@app.route("/item/<int:item_id>/update", methods=['GET', 'POST'])
@login_required
def update_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.author != current_user:
        abort(403)
    form = UpdateItemForm()
    if form.validate_on_submit():
        item.title = form.title.data
        item.price = form.price.data
        item.alert_price = form.alert_price.data
        db.session.commit()
        flash('Your item has been updated!', 'success')
        return redirect(url_for('item', item_id=item.id))
    elif request.method == 'GET':
        form.title.data = item.title
        form.price.data = item.price
        form.alert_price.data = item.alert_price
    return render_template('update_item.html', title='Update item',
                           form=form, legend='Update item')


@app.route("/item/<int:item_id>/delete", methods=['POST'])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.author != current_user:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    flash('Your item has been deleted!', 'success')
    return redirect(url_for('home'))



