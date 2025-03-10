from flask import Flask, render_template, url_for, redirect, request, flash
import os
from urllib.parse import urlparse
from page_analyzer.repository import Url_sql
import validators
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
db = Url_sql()


@app.template_filter('format_date')
def format_date(value):
    date_object = datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S.%f")
    return date_object.strftime("%Y-%m-%d")


@app.route('/')
def index():
    return render_template('index.html')


@app.get('/urls')
def show_urls():
    data = db.show_urls()
    return render_template("urls.html", urls=data)


@app.get('/urls/<int:id>')
def show_url(id):
    data = db.get_url_by_id(id)
    if not data:
        flash('Такая страница еще не добавлена', 'danger')
        return redirect(url_for('index'))
    data = dict(db.get_url_by_id(id)[0])
    data['checks'] = db.get_checks(data['id'])
    return render_template("url.html", url=data)


@app.post('/urls/<id>/checks')
def check_url(id):
    url_id = db.add_check(id)
    if not url_id:
        flash('Произошла ошибка при проверке', 'danger')
    else:
        flash('Страница успешно проверена', 'success')
    return redirect(url_for('show_url', id=id))


@app.post('/urls')
def add_url():
    url = request.form['url']
    if not validators.url(url) or len(url) > 255:
        flash('Некорректный URL', 'danger')
        return render_template('index.html'), 422
    url = urlparse(url)
    base_url = f"{url.scheme}://{url.netloc}/"
    data = db.get_url_by_name(name=base_url)
    if data:
        flash('Страница уже существует', 'success')
        return redirect(url_for('show_url', id=data[0]['id']))
    url_id = db.add_url(base_url)
    flash('Страница успешно добавлена', 'success')
    return redirect(url_for('show_url', id=url_id))
