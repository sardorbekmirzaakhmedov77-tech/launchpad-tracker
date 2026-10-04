"""Launchpad: a small Flask application for planning your next opportunity."""
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

ROOT = Path(__file__).resolve().parent
STAGES = ['Saved', 'Preparing', 'Submitted', 'Result']
KINDS = ['Scholarship', 'Internship']
RESULTS = ['Pending', 'Accepted', 'Rejected', 'Waitlisted']


@contextmanager
def connect(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        with db:
            yield db
    finally:
        db.close()


def initialize(path, demo):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        new = not db.execute("SELECT name FROM sqlite_master WHERE name='opportunities'").fetchone()
        db.executescript('''
          CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY, title TEXT NOT NULL, organization TEXT NOT NULL,
            kind TEXT NOT NULL, location TEXT NOT NULL, deadline TEXT NOT NULL,
            benefit TEXT NOT NULL, url TEXT NOT NULL, eligibility TEXT NOT NULL,
            notes TEXT NOT NULL, stage TEXT NOT NULL DEFAULT 'Saved',
            outcome TEXT NOT NULL DEFAULT 'Pending', archived INTEGER NOT NULL DEFAULT 0,
            is_demo INTEGER NOT NULL DEFAULT 0
          );
          CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY, opportunity_id INTEGER NOT NULL REFERENCES opportunities(id),
            title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0
          );
        ''')
        if new and demo:
            examples = [
                ('Future Leaders Fellowship', 'Northstar Foundation', 'Scholarship', 'United Kingdom', 6, 'Full tuition + living allowance', 'Preparing', 'Undergraduate degree; personal statement; two references.'),
                ('Software Engineering Intern', 'Orbit Labs', 'Internship', 'Remote', 12, 'Paid · 12 weeks', 'Preparing', 'Comfortable with Python and Git; one project to share.'),
                ('Global Impact Scholarship', 'Horizon University', 'Scholarship', 'Netherlands', 22, '€15,000 tuition award', 'Saved', 'Applicants to a master’s program; academic transcript required.'),
                ('Data & Insights Intern', 'Fieldwork Studio', 'Internship', 'Berlin, Germany', 35, 'Paid · 6 months', 'Saved', 'Python, spreadsheets, and an interest in data storytelling.'),
                ('Women in STEM Award', 'Aurora Trust', 'Scholarship', 'Canada', 46, '$8,000 study grant', 'Submitted', 'Women pursuing a STEM degree; short research proposal.'),
                ('Community Builders Grant', 'Open Path Foundation', 'Scholarship', 'Worldwide', -8, '$2,500 project grant', 'Result', 'A community project proposal and a project budget.'),
            ]
            for title, org, kind, location, days, benefit, stage, eligibility in examples:
                cursor = db.execute('''INSERT INTO opportunities
                    (title,organization,kind,location,deadline,benefit,url,eligibility,notes,stage,is_demo,outcome)
                    VALUES (?,?,?,?,?,?,?,?,?,?,1,?)''',
                    (title,org,kind,location,(date.today()+timedelta(days=days)).isoformat(),benefit,
                     '',eligibility,'Fictional example for practicing the tracker. Replace with a real opportunity.',stage,
                     'Accepted' if stage == 'Result' else 'Pending'))
                for index, task in enumerate(['Prepare résumé / CV', 'Draft personal statement', 'Request a reference', 'Review and submit application']):
                    done = int(stage in ('Submitted','Result') or (stage == 'Preparing' and index < 2))
                    db.execute('INSERT INTO tasks(opportunity_id,title,done) VALUES (?,?,?)', (cursor.lastrowid,task,done))


def text(value, label, maximum=200, optional=False):
    value = (value or '').strip()
    if (not value and not optional) or len(value) > maximum:
        raise ValueError(f'{label}: enter {"up to" if optional else "1–"} {maximum} characters.')
    return value


def validate(data):
    result = {key: text(data.get(key), label, maximum, optional) for key,label,maximum,optional in [
        ('title','Title',160,False), ('organization','Organization',120,False),
        ('location','Location',120,False), ('benefit','Funding or compensation',160,True),
        ('eligibility','Eligibility',4000,True), ('notes','Notes',6000,True), ('url','Website',1000,True)]}
    if data.get('kind') not in KINDS:
        raise ValueError('Choose scholarship or internship.')
    result['kind'] = data['kind']
    try:
        result['deadline'] = date.fromisoformat(data.get('deadline','')).isoformat()
    except ValueError:
        raise ValueError('Enter a valid application deadline.') from None
    if result['url']:
        try:
            parsed = urlsplit(result['url'])
            if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError
        except ValueError:
            raise ValueError('Website must be a full http:// or https:// address without login details.') from None
    return result


def decorate(row):
    item = dict(row)
    days = (date.fromisoformat(item['deadline']) - date.today()).days
    item['days'] = days
    item['deadline_label'] = 'Deadline passed' if days < 0 else 'Due today' if days == 0 else f'{days} days left'
    item['date_label'] = date.fromisoformat(item['deadline']).strftime('%b %d, %Y')
    item['percent'] = round(item['completed'] / item['total'] * 100) if item.get('total') else 0
    item['initials'] = ''.join(word[0] for word in item['organization'].split()[:2]).upper()
    return item


def create_app(database=None, demo=True):
    app = Flask(__name__)
    app.config.update(DATABASE=str(database or ROOT/'instance'/'launchpad.db'),
                      SECRET_KEY=os.environ.get('SECRET_KEY') or secrets.token_hex(32),
                      MAX_CONTENT_LENGTH=100_000, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')
    initialize(app.config['DATABASE'], demo)

    @app.before_request
    def protect_forms():
        session.setdefault('csrf', secrets.token_hex(24))
        if request.method == 'POST':
            supplied = request.form.get('csrf','')
            if not supplied.isascii() or not secrets.compare_digest(supplied,session['csrf']):
                abort(400, 'Form expired. Reload the page and try again.')

    @app.context_processor
    def shared():
        return dict(stages=STAGES,kinds=KINDS,results=RESULTS,csrf=session.get('csrf'),today=date.today().isoformat())

    def get_item(db, item_id):
        row = db.execute('''SELECT o.*, (SELECT COUNT(*) FROM tasks WHERE opportunity_id=o.id) total,
            (SELECT COUNT(*) FROM tasks WHERE opportunity_id=o.id AND done=1) completed
            FROM opportunities o WHERE id=?''', (item_id,)).fetchone()
        if not row:
            abort(404)
        return decorate(row)

    @app.get('/')
    def index():
        q = request.args.get('q','').strip()
        kind, stage = request.args.get('kind',''), request.args.get('stage','')
        view = request.args.get('view','all')
        sort = request.args.get('sort','deadline')
        with connect(app.config['DATABASE']) as db:
            rows = db.execute('''SELECT o.*, COUNT(t.id) total, COALESCE(SUM(t.done),0) completed
                FROM opportunities o LEFT JOIN tasks t ON t.opportunity_id=o.id
                GROUP BY o.id ORDER BY o.deadline, o.id''').fetchall()
        all_items = [decorate(row) for row in rows]
        active = [item for item in all_items if not item['archived']]
        upcoming = [item for item in active if 0 <= item['days'] <= 14 and item['stage'] in ('Saved','Preparing')]
        counts = dict(total=len(active), preparing=sum(i['stage']=='Preparing' for i in active),
                      submitted=sum(i['stage']=='Submitted' for i in active), upcoming=len(upcoming))
        items = [i for i in all_items if bool(i['archived']) == (view=='archive')]
        if view == 'deadlines':
            items = [i for i in items if i['stage'] in ('Saved','Preparing')]
        if q:
            items = [i for i in items if q.casefold() in f'{i["title"]} {i["organization"]} {i["location"]}'.casefold()]
        if kind:
            items = [i for i in items if i['kind']==kind]
        if stage:
            items = [i for i in items if i['stage']==stage]
        if sort == 'newest':
            items.sort(key=lambda i:i['id'],reverse=True)
        elif sort == 'title':
            items.sort(key=lambda i:i['title'].casefold())
        return render_template('index.html',items=items,counts=counts,upcoming=upcoming[:3],q=q,kind=kind,
                               stage=stage,view=view,sort=sort,has_demo=any(i['is_demo'] for i in all_items))

    @app.route('/new', methods=['GET','POST'])
    def new():
        data = dict(request.form) if request.method=='POST' else {}
        if request.method == 'POST':
            try:
                values = validate(request.form)
                with connect(app.config['DATABASE']) as db:
                    fields = ','.join(values)
                    placeholders = ','.join('?' for _ in values)
                    cursor = db.execute(f'INSERT INTO opportunities ({fields}) VALUES ({placeholders})', tuple(values.values()))
                    item_id = cursor.lastrowid
                    for title in ['Prepare résumé / CV','Check eligibility requirements','Review and submit application']:
                        db.execute('INSERT INTO tasks(opportunity_id,title) VALUES (?,?)',(item_id,title))
                flash('Opportunity saved. Your next chapter starts here.', 'success')
                return redirect(url_for('detail',item_id=item_id))
            except ValueError as error:
                flash(str(error),'error')
                return render_template('form.html',data=data,editing=False,view='all'),400
        return render_template('form.html',data=data,editing=False,view='all')

    @app.route('/opportunity/<int:item_id>/edit', methods=['GET','POST'])
    def edit(item_id):
        with connect(app.config['DATABASE']) as db:
            data=get_item(db,item_id)
        if request.method=='POST':
            try:
                values=validate(request.form)
                with connect(app.config['DATABASE']) as db:
                    fields=','.join(f'{field}=?' for field in values)
                    db.execute(f'UPDATE opportunities SET {fields} WHERE id=?',(*values.values(),item_id))
                flash('Changes saved.','success')
                return redirect(url_for('detail',item_id=item_id))
            except ValueError as error:
                flash(str(error),'error')
                return render_template('form.html',data={**data,**dict(request.form)},editing=True,view='all'),400
        return render_template('form.html',data=data,editing=True,view='all')

    @app.get('/opportunity/<int:item_id>')
    def detail(item_id):
        with connect(app.config['DATABASE']) as db:
            item=get_item(db,item_id)
            tasks=db.execute('SELECT * FROM tasks WHERE opportunity_id=? ORDER BY id',(item_id,)).fetchall()
        return render_template('detail.html',item=item,tasks=tasks,view='archive' if item['archived'] else 'all')

    @app.post('/opportunity/<int:item_id>/<action>')
    def update(item_id,action):
        try:
            with connect(app.config['DATABASE']) as db:
                item=get_item(db,item_id)
                if action=='stage':
                    stage=request.form.get('stage')
                    outcome=request.form.get('outcome','Pending')
                    if stage not in STAGES or outcome not in RESULTS:
                        raise ValueError('Choose a valid stage and result.')
                    if stage!='Result':
                        outcome='Pending'
                    db.execute('UPDATE opportunities SET stage=?,outcome=? WHERE id=?',(stage,outcome,item_id))
                elif action=='task':
                    title=text(request.form.get('title'),'Checklist item',200)
                    db.execute('INSERT INTO tasks(opportunity_id,title) VALUES (?,?)',(item_id,title))
                elif action=='toggle':
                    changed=db.execute('UPDATE tasks SET done=1-done WHERE id=? AND opportunity_id=?',
                                       (request.form.get('task_id'),item_id)).rowcount
                    if not changed:
                        abort(404)
                elif action=='archive':
                    db.execute('UPDATE opportunities SET archived=1-archived WHERE id=?',(item_id,))
                elif action=='notes':
                    notes=text(request.form.get('notes'),'Notes',6000,True)
                    db.execute('UPDATE opportunities SET notes=? WHERE id=?',(notes,item_id))
                else:
                    abort(404)
            flash('Saved successfully.','success')
        except ValueError as error:
            flash(str(error),'error')
        return redirect(url_for('detail',item_id=item_id))

    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html',message='This opportunity could not be found.',view='all'),404

    return app


if __name__=='__main__':
    create_app(demo=os.environ.get('TRACKER_DEMO','1')!='0').run(host='127.0.0.1',port=int(os.environ.get('PORT','5001')))
