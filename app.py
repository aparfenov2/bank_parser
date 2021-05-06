import flask
from gen_summary import Main
from update_database import Main as UpdateMain
import datetime
import unittest
from mako.template import Template
import numpy as np
import os

app = flask.Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'upload'

class _args: pass

WAGE_DAY=5
DATETIME_FORMAT='%d.%m.%Y'
DATABASE_PATH='db/db.mysql3'

def get_closest_wage_dates(now):
    if now.day < WAGE_DAY:
        if now.month > 1:
            left = now.replace(day = WAGE_DAY, month = now.month - 1)
        else:
            left = now.replace(day = WAGE_DAY, month = 12, year = now.year - 1)
        right = now.replace(day = WAGE_DAY - 1)
        return left, right
    else:
        left = now.replace(day = WAGE_DAY)
        if now.month < 12:
            right = now.replace(day = WAGE_DAY - 1, month = now.month + 1)
        else:
            right = now.replace(day = WAGE_DAY - 1, month = 1, year = now.year + 1)

    return left, right

class UT1(unittest.TestCase):
    def test1(self):
        now = datetime.datetime.strptime('01.03.2021', DATETIME_FORMAT)
        a,b = get_closest_wage_dates(now)
        self.assertEqual(datetime.datetime.strptime('05.02.2021', DATETIME_FORMAT), a)
        self.assertEqual(datetime.datetime.strptime('04.03.2021', DATETIME_FORMAT), b)

    def test2(self):
        now = datetime.datetime.strptime('15.03.2021', DATETIME_FORMAT)
        a,b = get_closest_wage_dates(now)
        self.assertEqual(datetime.datetime.strptime('05.03.2021', DATETIME_FORMAT), a)
        self.assertEqual(datetime.datetime.strptime('04.04.2021', DATETIME_FORMAT), b)

    def test2(self):
        now = datetime.datetime.strptime('05.03.2021', DATETIME_FORMAT)
        a,b = get_closest_wage_dates(now)
        self.assertEqual(datetime.datetime.strptime('05.03.2021', DATETIME_FORMAT), a)
        self.assertEqual(datetime.datetime.strptime('04.04.2021', DATETIME_FORMAT), b)


def expenses_calendar(self, expenses_by_day):
    all_curs = {tr.currency for d, trs in expenses_by_day.items() for tr in trs}

    def make_sum(trs):
        _sum = {cur : sum([tr.amount for tr in trs if tr.currency == cur]) for cur in all_curs}
        return ','.join([f"{s:6.2f} {c}" for c,s in _sum.items() if abs(s) > 0])

    spd_rows = [] # [(d,v,c)]
    cwod = 0
    crow = []
    for d,trs in sorted(expenses_by_day.items(),  key=lambda kv: kv[0]):
        while cwod < d.weekday():
            crow += [(None,None,None)]
            cwod += 1
        crow += [(d.day, make_sum(trs), self.tr_format_html(list(sorted(trs, key=lambda kv: kv.amount))) )]
        if cwod >= 6:
            spd_rows += [crow]
            crow = []
            cwod = 0
        else:
            cwod += 1
    if len(crow) > 0:
        while cwod <= 6:
            crow += [(None,None,None)]
            cwod += 1
        spd_rows += [crow]

    def _make_row(_cur):
        by_day_sums = [sum([tr.amount for tr in trs if tr.currency == _cur]) for d,trs in sorted(expenses_by_day.items(), key=lambda kv: kv[0])]
        return [f'by day,{_cur}'] + by_day_sums + [np.mean(by_day_sums[-7:])]
    
    rows = [ _make_row(_cur) for _cur in all_curs] 

    return spd_rows, ', '.join([f"{r[-1]:6.2f} {c}/day" for c,r in zip(all_curs,rows)])

@app.route('/')
def index():
    req_args_after = flask.request.args.get('after')
    req_args_before = flask.request.args.get('before')
    args = _args()
    if req_args_after is None:
        args.after, args.before = get_closest_wage_dates(datetime.datetime.now())
    else:
        args.after = datetime.datetime.strptime(req_args_after, DATETIME_FORMAT)
        args.before = datetime.datetime.strptime(req_args_before, DATETIME_FORMAT)

    args.db = DATABASE_PATH

    self = Main(args)
    en = self.read_database()
    en = list(en)

    by_cat = self.group_by_category(en)

    en_no_tr = self.filter_transfers(en)
    en_no_tr = list(en_no_tr)
    expenses_by_day = self.expenses_by_day(en_no_tr)
    # spd_rows, spd_headers, spd_all_curs, spd_rows_c = self.pintable_speed(expenses_by_day, printable=False)
    spd_rows, avg_7 = expenses_calendar(self, expenses_by_day)

    rows, headers, acc_curs, by_acc_cur, by_acc_cur_c, _com = self.printable_summary(by_cat, printable=False)

    prev_after, prev_before = get_closest_wage_dates(args.after - datetime.timedelta(days=1))
    next_after, next_before = get_closest_wage_dates(args.before + datetime.timedelta(days=1))

    data = {        
        'rows':rows, 
        'headers':headers, 
        'acc_curs':acc_curs, 
        'by_acc_cur':by_acc_cur, 
        'by_acc_cur_c':by_acc_cur_c, 
        '_com':_com,
        'after' : args.after.strftime(DATETIME_FORMAT),
        'before' : args.before.strftime(DATETIME_FORMAT),
        'prev_after' : prev_after.strftime(DATETIME_FORMAT),
        'prev_before' : prev_before.strftime(DATETIME_FORMAT),
        'next_after' : next_after.strftime(DATETIME_FORMAT),
        'next_before': next_before.strftime(DATETIME_FORMAT),
        'spd_rows' : spd_rows,
        '7_avg' : avg_7
        }

    # html = self.do_htmlout(
    #     self.printable_speed(expenses_by_day, printable=False), 
    #     self.printable_summary(by_cat, printable=False)
    #     )
    tm = Template(filename="templates/summary.html")
    return tm.render(data=data)


def delete_all(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            os.unlink(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

@app.route('/upload', methods=['GET','POST'])
def upload():
    if flask.request.method == "POST":
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        files = flask.request.files.getlist("file[]")
        if len(files) > 0:
            delete_all(app.config['UPLOAD_FOLDER'])
            for file in files:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

            args = _args()
            args.csvdir = app.config['UPLOAD_FOLDER']
            args.database = DATABASE_PATH
            UpdateMain(args).main()

        # return flask.redirect("/upload")
        return f"imported {[f.filename for f in files]}"
    else:
        return """
<form method="POST" enctype="multipart/form-data" action="/upload">
  <input type="file" name="file[]" multiple="">
  <input type="submit" value="Import">
</form>
    """

if __name__ == '__main__':
    app.run(debug=True)
