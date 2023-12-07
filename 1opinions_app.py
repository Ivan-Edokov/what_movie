import csv
import click
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
# Импортируется функция выбора случайного значения
from random import randrange
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, URLField
from wtforms.validators import DataRequired, Length, Optional
from flask_migrate import Migrate


app = Flask(__name__)

# Подключается БД SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'

# Задаётся конкретное значение для конфигурационного ключа
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'ghjnbgjghnb7594763987hbfgr67830jhg'

# Создаётся экземпляр класса SQLAlchemy и передаётся 
# в качестве параметра экземпляр приложения Flask
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Opinion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    text = db.Column(db.Text, unique=True, nullable=False)
    source = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    added_by = db.Column(db.String(64))


class OpinionForm(FlaskForm):
    title = StringField(
        'Введите название фильма',
        validators=[DataRequired(message='Обязательное поле'),
                    Length(1, 128)]
    )
    text = TextAreaField(
        'Напишите мнение',
        validators=[DataRequired(message='Обязательное поле')]
    )
    source = URLField(
        'Добавьте ссылку на подробный обзор фильма',
        validators=[Length(1, 256), Optional()]
    )
    submit = SubmitField('Д  обавить')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    # В таких случаях можно откатить незафиксированные изменения в БД
    db.session.rollback()
    return render_template('500.html'), 500



@app.route('/')
def index_view():
    # Определяется количество мнений в базе данных
    quantity = Opinion.query.count()
    # Если мнений нет,
    if not quantity:
        abort(404)
    # Иначе выбирается случайное число в диапазоне от 0 и до quantity
    ofdet_value = randrange(quantity)
    # И определяется случайный объект
    opinion = Opinion.query.offset(ofdet_value).first()
    return render_template('opinion.html', opinion=opinion)


@app.route('/add', methods=['GET', 'POST'])
def add_opinion_view():
    # Вот тут создаётся новый экземпляр формы
    form = OpinionForm()
    # Если ошибок не возникло, то
    if form.validate_on_submit():
        text = form.text.data
        # Если в БД уже есть мнение с текстом, который ввёл пользователь,
        if Opinion.query.filter_by(text=text).first():
            # вызвать функцию flash и передать соответствующее сообщение
            flash('Такое мнение уже было оставлено ранее!')
            # и вернуть пользователя на страницу «Добавить новое мнение»
            return render_template('add_opinion.html', form=form)
        # нужно создать новый экземпляр класса Opinion
        opinion = Opinion(
            title=form.title.data,
            text=form.text.data,
            source=form.source.data
        )
        # Затем добавить его в сессию работы с базой данных
        db.session.add(opinion)
        db.session.commit()
        # Затем перейти на страницу добавленного мнения
        return redirect(url_for('opinion_view', id=opinion.id))
    # Иначе просто отрисовать страницу с формой
    return render_template('add_opinion.html', form=form)


@app.route('/opinions/<int:id>')
def opinion_view(id):
    opinion = Opinion.query.get_or_404(id)
    return render_template('opinion.html', opinion=opinion)


@app.cli.command('load_opinions')
def load_opinions_command():
    """Функция загрузки мнений в базу данных."""
    # Открывается файл
    with open('opinions.csv', encoding='utf-8') as f:
        # Создаётся итерируемый объект, который отображает каждую строку
        # в качестве словаря с ключами из шапки файла
        reader = csv.DictReader(f)
        # Для подсчёта строк добавляется счётчик
        counter = 0
        for row in reader:
            # Распакованный словарь можно использовать 
            # для создания объекта мнения
            opinion = Opinion(**row)
            # Изменения нужно зафиксировать
            db.session.add(opinion)
            db.session.commit()
            counter += 1
    click.echo(f'Загружено мнений: {counter}')


if __name__ == '__main__':
    app.run()
