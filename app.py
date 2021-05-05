from flask import Flask, request
from gen_summary import Main
import datetime
import unittest
from mako.template import Template

app = Flask(__name__)

class _args: pass

WAGE_DAY=5
DATETIME_FORMAT='%d.%m.%Y'

def get_closest_wage_dates(now):
    if now.day < WAGE_DAY:
        if now.month > 1:
            left = now.replace(day = WAGE_DAY, month = now.month - 1)
        else:
            left = now.replace(day = WAGE_DAY, month = 12, year = now.year - 1)
        right = now.replace(day = WAGE_DAY)
        return left, right
    else:
        left = now.replace(day = WAGE_DAY)
        if now.month < 12:
            right = now.replace(day = WAGE_DAY, month = now.month + 1)
        else:
            right = now.replace(day = WAGE_DAY, month = 1, year = now.year + 1)

    return left, right

class UT1(unittest.TestCase):
    def test1(self):
        now = datetime.datetime.strptime('01.03.2021', DATETIME_FORMAT)
        a,b = get_closest_wage_dates(now)
        self.assertEqual(datetime.datetime.strptime('05.02.2021', DATETIME_FORMAT), a)
        self.assertEqual(datetime.datetime.strptime('05.03.2021', DATETIME_FORMAT), b)

    def test2(self):
        now = datetime.datetime.strptime('15.03.2021', DATETIME_FORMAT)
        a,b = get_closest_wage_dates(now)
        self.assertEqual(datetime.datetime.strptime('05.03.2021', DATETIME_FORMAT), a)
        self.assertEqual(datetime.datetime.strptime('05.04.2021', DATETIME_FORMAT), b)

    def test2(self):
        now = datetime.datetime.strptime('05.03.2021', DATETIME_FORMAT)
        a,b = get_closest_wage_dates(now)
        self.assertEqual(datetime.datetime.strptime('05.03.2021', DATETIME_FORMAT), a)
        self.assertEqual(datetime.datetime.strptime('05.04.2021', DATETIME_FORMAT), b)

@app.route('/')
def index():
    req_args_after = request.args.get('after')
    req_args_before = request.args.get('before')
    args = _args()
    if req_args_after is None:
        args.after, args.before = get_closest_wage_dates(datetime.datetime.now())
    else:
        args.after = datetime.datetime.strptime(req_args_after, DATETIME_FORMAT)
        args.before = datetime.datetime.strptime(req_args_before, DATETIME_FORMAT)

    args.db = "db/db.mysql3"

    self = Main(args)
    en = self.read_database()
    en = list(en)

    by_cat = self.group_by_category(en)

    en_no_tr = self.filter_transfers(en)
    en_no_tr = list(en_no_tr)
    expenses_by_day = self.expenses_by_day(en_no_tr)
    # spd_rows, spd_headers, spd_all_curs, spd_rows_c = self.pintable_speed(expenses_by_day, printable=False)
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
    while cwod < 6:
        crow += [(None,None,None)]
        cwod += 1
    spd_rows += [crow]

    rows, headers, acc_curs, by_acc_cur, by_acc_cur_c, _com = self.printable_summary(by_cat, printable=False)

    prev_after, prev_before = get_closest_wage_dates(args.after - datetime.timedelta(days=1))
    next_after, next_before = get_closest_wage_dates(args.before)

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
        'spd_rows' : spd_rows
        }

    # html = self.do_htmlout(
    #     self.printable_speed(expenses_by_day, printable=False), 
    #     self.printable_summary(by_cat, printable=False)
    #     )
    tm = Template(filename="templates/summary.html")
    return tm.render(data=data)

if __name__ == '__main__':
    app.run(debug=True)
