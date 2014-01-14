from datetime import datetime
from dateutil import parser
import sqlite3

from flask import Flask, flash, g, jsonify, redirect, render_template, request, url_for

DATABASE = '/var/www/flask-timekeeper/main.db'
DEBUG = True
SECRET_KEY = '\x02\xbb(M\xcd\xdc\xea,7\x02\x00\xdey\x9e?\xa2\x14b\xc8T+\xce\xba\xf7'

app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/')
def show_projects():
    cur = g.db.execute('select id, name, description from project order by id desc')
    projects = [dict(id=row[0], name=row[1], description=row[2]) for row in cur.fetchall()]
    return render_template('show_projects.html', projects=projects)

@app.route('/project/add', methods=['POST'])
def add_project():
    g.db.execute('insert into project (name, description) values (?, ?)', [request.form['name'], request.form['description']])
    g.db.commit()
    flash('New project was successfully added', 'success')
    return redirect(url_for('show_projects'))

@app.route('/project/edit/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    if request.method == 'POST':
        g.db.execute('update project set name=(?), description=(?) where (id)=(?)', [request.form['name'], request.form['description'], project_id])
        g.db.commit()
        flash('Project successfully modified.', 'success')
        return redirect(url_for('show_projects'))
    else:
        cur = g.db.execute('select id, name, description from project where (id)=(?)', [project_id])
        result = cur.fetchall()[0]
        project = dict(id=result[0], name=result[1], description=result[2])
        return render_template('project_edit.html', project=project)

@app.route('/project/delete/<int:project_id>', methods=['GET'])
def delete_project(project_id):
    g.db.execute('delete from timekeeper where (project_id)=(?)', [project_id])
    g.db.commit()
    g.db.execute('delete from project where (id)=(?)', [project_id])
    g.db.commit()
    flash('Project was deleted!', 'warning')
    return redirect(url_for('show_projects'))

@app.route('/project/<int:project_id>', methods=['GET'])
def project_detail(project_id):
    cur = g.db.execute('select id, name, description from project where (id)=(?)', [project_id])
    result = cur.fetchall()[0]
    project = dict(id=result[0], name=result[1], description=result[2])
    cur = g.db.execute('select id, project_id, start_date, stop_date from timekeeper where (project_id)=(?) order by start_date asc', [project_id])
    timekeeper = [dict(id=row[0], project_id=row[1], start_date=row[2], stop_date=row[3]) for row in cur.fetchall()]
    total = None
    for time in timekeeper:
        if time['stop_date']:
            time['duration'] = parser.parse(time['stop_date']) - parser.parse(time['start_date'])
            if not total:
                total = time['duration']
            else:
                total += time['duration']
    return render_template('project_detail.html', project=project, timekeeper=timekeeper, total=total)

@app.route('/project/start/', methods=['POST'])
def project_start():
    project_id = request.form['project_id']
    start_date = datetime.now()
    g.db.execute('insert into timekeeper (project_id, start_date) values (?, ?)', [project_id, start_date])
    g.db.commit()
    return redirect(url_for('project_detail', project_id=project_id))
    
@app.route('/project/stop/', methods=['POST'])
def project_stop():
    project_id = request.form['project_id']
    timekeeper_id = request.form['timekeeper_id']
    stop_date = datetime.now()
    g.db.execute('update timekeeper set stop_date=(?) where (id)=(?)', [stop_date, timekeeper_id])
    g.db.commit()
    return redirect(url_for('project_detail', project_id=project_id))

@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    date = parser.parse(date)
    native = date.replace(tzinfo=None)
    format='%b %d, %Y %I:%M%p'
    return native.strftime(format)

@app.template_filter('deltaformat')
def _timedelta_format(timedelta):
    hours, remainder = divmod(timedelta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return '%2d hour%s, %2d minute%s' % (hours, "s"[hours==1:], minutes, "s"[minutes==1:])

if __name__ == '__main__':
    app.run()
