import sqlite3
import os
from flask import Flask, render_template, g, request, flash, abort, Markup
from FDataBase import FDataBase

#Конфигурация
DATABASE = 'flsite.db'
DEBUG = True
SECRET_KEY = 'fdgfh78@#5?>gfhf89dx,v06k'

app = Flask(__name__)
# Загрузка конфигурации из приложения. Загружаем директиву __name__.
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))

def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row # Записи из БД представлены не в виде кортежей, а в виде словаря
    return conn


'''
Создание базы данных.
В файле sq_db.sql прописан скрипт на создание таблицы в базе данных
Чтобы создать базу, нужно в консоли прописать from flsite import create_db,
а затем сделать вызов функции create_db()
'''
def create_db():
    db = connect_db()
    with app.open_resource('sq_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit() # записывание изменений
    db.close() # закрытие соединения

def get_db():
    '''Соединение с БД, если оно еще не установлено'''
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db

'''
hasattr(g, 'link_db'):
Это проверка на то, существует ли в контексте глобального приложения св-во link_db
'''

@app.teardown_appcontext
def close_db(error):
    '''Закрываем соединение с БД если оно было установлено
    Декоратор срабатывает тогда, когда происходит уничтожение контекста приложения
    А это происходит в момент завершения обработки запроса
    '''

    if hasattr(g, 'link_db'):
        g.link_db.close()
'''
чтобы создать базу данных, нужно в консоли прописать from flsite import create_db
а затем вызвать в консоли функцию create_db()
затем в рабочей дирректории создастся база db
'''

'''
В момент прихода запроса устанавливается соединение с базой данных, а в момент
завершения обработки происходит разрыв с БД. Этот момент можно поймать в обработчике
'''
@app.route('/')
def index():
    db = get_db() # установка соединения в момент прихода запроса
    '''
    Функцию get_db() можно при необходимости вызывать в каждом обработчике для того чтобы установить соединение с БД
    '''
    dbase = FDataBase(db)
    print(dbase.getMenu())
    return render_template('index.html',
                           menu = dbase.getMenu(),
                           vacancy=dbase.getVacancyAnonce())

@app.route("/add_vacancy", methods=["POST", "GET"])
def addVacancy():
    db = get_db()
    dbase = FDataBase(db)

    if request.method == "POST":
        '''Поля post и name взяты из формы'''
        if len(request.form['name']) > 4 and len(request.form['description']) > 10:
            '''Класс addVacancy находится в файле FDataBase. Данный класс добавляет записи в БД
               Передается название и описание вакансии
            '''
            res = dbase.addVacancy(request.form['name'], request.form['city'], request.form['salary'],
                                   request.form['schedule'], request.form['description'])
            if not res:
                flash('Ошибка добавления вакансии', category = 'error')
            else:
                flash('Вакансия добавлена успешно', category='success')
        else:
            flash('Ошибка добавления вакансии', category='error')

    return render_template('add_post.html',
                           menu = dbase.getMenu(),
                           title="Добавление вакансии")

@app.route("/resume_analitics", methods=["POST", "GET"])
def ResumeAnalitics():
    db = get_db()
    dbase = FDataBase(db)

    desired_salary = []
    sending_date_month = []

    schedule = []
    vacancy_ammount = []

    if request.method == "POST":
        request_from_form = request.form.get('radio_button')  # get value of radio button with name "color"
        print(request_from_form)
        info_graph1 = dbase.getResumeInfo_1Graph(request_from_form)
        info_graph2 = dbase.getResumeInfo_2Graph(request_from_form)
        print(info_graph1)
        print(info_graph2)

        for d in info_graph1:
            desired_salary.append(d['desired_salary'])
            sending_date_month.append(d['sending_date_month'])

        for d in info_graph2:
            schedule.append(d['schedule'])
            vacancy_ammount.append(d['vacancy_ammount'])

    return render_template('resume_analitics.html',
                           menu = dbase.getMenu(),
                           labels1=sending_date_month,
                           data = desired_salary,
                           values=vacancy_ammount,
                           labels=schedule,
                           max = 10
                           )


'''
Обработчик для отображения поста
'''
@app.route("/vacancy/<int:id_vacancy>")
def showVacancy(id_vacancy):
    db = get_db()
    dbase = FDataBase(db)
    name, description = dbase.getVacancy(id_vacancy)
    if not description:
        abort(404)

    return render_template('vacancy_page.html', menu=dbase.getMenu(), title=name, post=description)

@app.route("/resume/<int:id_resume>")
def showResume(id_resume):
    db = get_db()
    dbase = FDataBase(db)
    profession, description = dbase.getResume(id_resume)
    if not profession:
        abort(404)

    return render_template('resume_page.html', menu=dbase.getMenu(), description=description)

@app.route("/resume_list")
def resumeList():
    db = get_db()
    dbase = FDataBase(db)
    return render_template('resume_list.html',
                           menu=dbase.getMenu(),
                           resume=dbase.getResumeAnonce())


if __name__ == "__main__":
    app.run(debug=True)
