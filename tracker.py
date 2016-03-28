from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form, StringField, validators

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta as delta
import calendar


DATABASE = 'tracker.db'

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

calendar.setfirstweekday(calendar.SUNDAY)
months = [('', ''),
          ('January', 'Jan'),
          ('February', 'Feb'),
          ('March', 'Mar'),
          ('April', 'Apr'),
          ('May', 'May'),
          ('June', 'Jun'),
          ('July', 'Jul'),
          ('August', 'Aug'),
          ('September', 'Sep'),
          ('October', 'Oct'),
          ('November', 'Nov'),
          ('December', 'Dec')]
_re_time = '^(?:\d|[01]\d|2[0-3]):([0-5]\d)\s*([aApP][mM])?$'


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10))
    start = db.Column(db.String(5))
    stop = db.Column(db.String(5))
    task = db.Column(db.String(200))

    def __init__(self, date, start, stop, task):
        self.date = date
        self.start = start
        self.stop = stop
        self.task = task

    def __repr__(self):
        return '<Entry: ({}  {}-{}) {}>'.format(self.date, self.start,
                                                self.stop, self.task)


class EntryForm(Form):
    start = StringField('Start Time', [validators.Length(min=4, max=8),
                                       validators.regexp(_re_time),
                                       validators.DataRequired()])
    stop = StringField('Stop Time', [validators.Length(min=4, max=8),
                                     validators.regexp(_re_time),
                                     validators.DataRequired()])
    task = StringField('Task', [validators.Length(min=1, max=200),
                                validators.DataRequired()])


def _validate_month(month):
    if month.isdigit():
        if 13 > int(month) > 0:
            n_month = int(month)
            d_month = months[n_month][0]
        else:
            return None
    else:
        month = month.capitalize()
        if len(month) == 3:
            try:
                n_month = [i for i, v in enumerate(months) if v[1] == month][0]
                d_month = months[n_month][0]
            except:
                return None
        else:
            try:
                n_month = [i for i, v in enumerate(months) if v[0] == month][0]
                d_month = month
            except:
                return None

    return {'number': n_month, 'name': d_month}


def _add_entry(form):
    return render_template('debug.html', stuff=form)


def _remove_entry():
    pass


@app.route('/')
def index():
    return ''


@app.route('/tracker/')
def root_view():
    return render_template('index.html')


@app.route('/tracker/<int:year>/')
def year_view(year=None):
    prev_year = (parse(str(year)) + delta(years=-1)).strftime('%Y')
    next_year = (parse(str(year)) + delta(years=+1)).strftime('%Y')

    return render_template('year.html', year=year, months=months[1:],
                           next=next_year, prev=prev_year)


@app.route('/tracker/<int:year>/<month>/')
def month_view(year=None, month=None):
    v_month = _validate_month(month)
    if not v_month:
        return render_template('404.html')

    date = '-'.join(map(str, [year, v_month['name']]))

    prev_month = (parse(date) + delta(months=-1)).strftime('%Y/%b')
    next_month = (parse(date) + delta(months=+1)).strftime('%Y/%b')

    _days = calendar.weekheader(2).split(" ")
    _month = calendar.monthcalendar(year, v_month['number'])
    return render_template('month.html', year=year, month=month,
                           d_month=v_month['name'], _month=_month, _days=_days,
                           prev=prev_month, next=next_month)


@app.route('/tracker/<int:year>/<month>/<int:day>', methods=['GET', 'POST'])
def day_view(year=None, month=None, day=None):
    form = EntryForm(request.form)

    v_month = _validate_month(month)
    if not v_month:
        return render_template('404.html')
    date = '-'.join(map(str, [year, v_month['number'], day]))

    prev_day = (parse(date) + delta(days=-1)).strftime('%Y/%b/%d')
    next_day = (parse(date) + delta(days=+1)).strftime('%Y/%b/%d')

    if request.method == 'POST':
        if 'add' in request.form and form.validate():
            start = parse(form.start.data).strftime('%H:%M')
            stop = parse(form.stop.data).strftime('%H:%M')
            entry = Entry(date, start, stop, form.task.data)
            db.session.add(entry)
            db.session.commit()
        elif 'delete' in request.form:
            entry_id = request.form['delete']
            entry = Entry.query.filter_by(id=entry_id).delete()
            db.session.commit()
        else:
            return render_template('debug.html', stuff=request.form)

    entries = Entry.query.filter_by(date=date).order_by(Entry.start).all()

    return render_template('day.html', year=year, month=month, day=day,
                           d_month=v_month['name'], entries=entries,
                           prev=prev_day, next=next_day, form=form)


if __name__ == "__main__":
    db.create_all()
    app.debug = False
    app.run(host='127.0.0.1')
