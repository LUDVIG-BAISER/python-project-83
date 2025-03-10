from flask import Flask, render_template, url_for, redirect, request, flash
import os
from urllib.parse import urlparse
from page_analyzer.repository import Url_sql
import validators
from datetime import datetime
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # Секретный ключ для защиты сессий

db = Url_sql()  # Инициализация базы данных


def format_date(value: str) -> str:
    """Фильтр шаблона для форматирования даты."""
    date_object = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
    return date_object.strftime("%Y-%m-%d")


app.jinja_env.filters['format_date'] = format_date


@app.route('/')
def index():
    """Главная страница."""
    return render_template('index.html')


@app.get('/urls')
def show_urls():
    """Вывод списка URL-адресов из базы данных."""
    data = db.show_urls()
    return render_template("urls.html", urls=data)


@app.get('/urls/<int:id>')
def show_url(id: int):
    """Вывод информации об определенном URL."""
    data = db.get_url_by_id(id)
    if not data:
        flash('Такая страница еще не добавлена', 'danger')
        return redirect(url_for('index'))
    url_data = dict(data[0])
    url_data['checks'] = db.get_checks(url_data['id'])
    return render_template("url.html", url=url_data)


@app.post('/urls/<int:id>/checks')
def check_url(id: int):
    # Добавление проверки для указанного URL.
    url_id = db.add_check(id)
    if not url_id:
        flash('Произошла ошибка при проверке', 'danger')
    else:
        flash('Страница успешно проверена', 'success')
    return redirect(url_for('show_url', id=id))


@app.post('/urls')
def add_url():
    # Добавление нового URL в базу данных.
    url: str = request.form['url']
    if not validators.url(url) or len(url) > 255:
        flash('Некорректный URL', 'danger')
        return render_template('index.html'), 422

    parsed_url = urlparse(url)
    base_url: str = f"{parsed_url.scheme}://{parsed_url.netloc}/"

    existing_url = db.get_url_by_name(name=base_url)
    if existing_url:
        flash('Страница уже существует', 'success')
        return redirect(url_for('show_url', id=existing_url[0]['id']))

    url_id = db.add_url(base_url)
    flash('Страница успешно добавлена', 'success')
    return redirect(url_for('show_url', id=url_id))


if __name__ == '__main__':
    app.run(debug=True)
