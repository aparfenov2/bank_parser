import sys, os, re, datetime, json
from utils import read_transactions, read_alfa, named_dict
import argparse, logging
from collections import namedtuple, defaultdict
from typing import List, DefaultDict, Dict, Union
# from mypy_extensions import TypedDict
from tabulate import tabulate
import numpy as np
import xlsxwriter

uni_t = named_dict('uni_t', ['account', 'date', 'amount', 'currency', 'category', 'src'])

class float_and_list_t(dict):
    def __init__(self, v=0., trs=[]):
        self.v : float = v
        self.trs : List[uni_t] = trs
        super().__init__(self.__dict__)

    def __add__(self, o):
        return float_and_list_t(self.v + o.v, self.trs + o.trs)

class Main:
    @staticmethod
    def make_parser():
        parser = argparse.ArgumentParser()
        parser.add_argument('csvdir')
        parser.add_argument('--debug', action='store_true')
        parser.add_argument('--days_after', type=int)
        parser.add_argument('--days_before', type=int)
        parser.add_argument('--after',  type=lambda s: datetime.datetime.strptime(s, '%d.%m.%Y'))        
        parser.add_argument('--before', type=lambda s: datetime.datetime.strptime(s, '%d.%m.%Y'))        
        parser.add_argument('--allout', default="transactions.json")
        parser.add_argument('--sumout', default="summary.json")
        parser.add_argument('--bydayout', default="expenses_by_day.json")

        return parser

    def  __init__(self, args):
        self.args = args
        self.logger = logging.getLogger(self.__class__.__name__)

    def read_datadir(self):
        for f in os.listdir(self.args.csvdir):
            if f.endswith('.csv'):
                try:
                    fullpath = os.path.join(self.args.csvdir,f)
                    if 'rub' in f:
                        trs = read_alfa(fullpath)
                        yield 'rub', trs
                    elif 'credit' in f:
                        trs = read_alfa(fullpath)
                        yield 'credit', trs
                    elif 'byn' in f:
                        trs = read_transactions(fullpath)
                        yield 'byn', trs
                    elif 'usd' in f:
                        trs = read_transactions(fullpath)
                        yield 'usd', trs
                    else:
                        self.logger.warning(f"{fullpath} is not recognized")
                except Exception:
                    self.logger.exception(fullpath)
                    raise

    def to_unified_rec(self, en):
        for _type, trs in en:
            #['date', 'amount', 'currency', 'category', 'src']
            for tr in trs:
                if _type in ['rub', 'credit']:
                    cat = tr.category
                else:
                    cat = tr.op + tr.category
                _tr = uni_t(_type, tr.date, tr.amount, tr.currency, cat, tr)
                cat = self.get_category(_tr)
                tr = uni_t(_type, tr.date, tr.amount, tr.currency, cat, tr)
                yield tr

    def filter_by_date(self, en : List[uni_t]):
        min_date = None
        max_date = None
        if self.args.days_after is not None:
            min_date = datetime.datetime.today() - datetime.timedelta(days=self.args.days_after)
        if self.args.after is not None:
            min_date = self.args.after

        if self.args.days_before is not None:
            max_date = datetime.datetime.today() - datetime.timedelta(days=self.args.days_before)
        if self.args.before is not None:
            max_date = self.args.before

        if min_date is not None:
            self.logger.info(f"min_date {min_date}")
        if max_date is not None:
            self.logger.info(f"max_date {max_date}")

        for tr in en:
            if min_date is not None:
                if tr.date <= min_date:
                    continue
            if max_date is not None:
                if tr.date >= max_date:
                    continue
            yield tr

    def filter_transfers(self, en):
        for tr in en:
            if tr.category not in ['income','to BYN', 'to RUB', 'to CREDIT']:
                yield tr

    def get_category(self, tr : uni_t):

        if tr.amount > 0:
            return 'income'

        cat_defs = {
            'sadik' : [r'Парфенов\s+Сергей'],
            'kv' : [r'в пользу"ЧЕЛЯБИНВЕСТБАНК"'],
            'kv_otop' : [r'RU GOROD74.RU'],
            'cash' : [r'Alfa Iss'],
            'dolina' : [r'DOLINA'],
            'molnia' : [r'MOLNIA'],
            'taxi' : [r'TAXI'],
            'eats' : [r'MAGNIT', r'PYATEROCHKA',r'Магазины продуктовые'],
            'to KATE' : [r'на \+79511286005'],
            'gas' : [r'GAZPROMNEFT',r'AZS', r'АЗС'],
            'to RUB' : [r'CH Debit BLR MINSK P2P_SDBO_INTERNATIONAL'],
            'to BYN' : [r'CH Debit BLR MINSK P2P SDBO NO FEE'],
            'to CREDIT' : [r'Внутрибанковский перевод между счетами'],            
            'Kate eats' : [r'STOLOVAYA VILKA', r'Ресторация'],
        }

        for cat, regs in cat_defs.items():
            for reg in regs:
                # print(reg)
                ret = re.search(reg, tr.category)
                # print(ret, tr.category == ss)
                if ret:
                    return cat
        return 'other'

    def group_by_category(self, en : List[uni_t]):
        # ValueOrlistDict = TypedDict('ValueOrlistDict', {
        #         'v'   : float,
        #         'trs' : List[uni_t]
        #     })

        summary : DefaultDict[str,DefaultDict[str, DefaultDict[str, float_and_list_t]]] = \
            defaultdict(lambda: defaultdict(lambda: defaultdict(float_and_list_t)))

        for tr in en:
            summary[tr.category][tr.account][tr.currency] += float_and_list_t(tr.amount, [tr])

        cat_totals : DefaultDict[str,DefaultDict[str,float_and_list_t]] = defaultdict(lambda: defaultdict(float_and_list_t))
        acc_totals : DefaultDict[str,DefaultDict[str,float_and_list_t]] = defaultdict(lambda: defaultdict(float_and_list_t))
        spent_total : DefaultDict[str,float_and_list_t] = defaultdict(float_and_list_t)

        for tr in self.filter_transfers(en):
            cat_totals[tr.category][tr.currency] += float_and_list_t(tr.amount, [tr])
            acc_totals[tr.account][tr.currency] += float_and_list_t(tr.amount, [tr])
            spent_total[tr.currency] += float_and_list_t(tr.amount, [tr])

        return {
            'summary' : summary, 
            'cat_totals' : cat_totals, 
            'acc_totals' : acc_totals, 
            'spent_total' : spent_total
            }

    def printable_summary(self, en):
        by_acc_cur = {
            cat : {
                f"{acc}_{cur}" : f"{v.v:6.2f}" for acc, curd in accd.items() for cur, v in curd.items()
            } for cat, accd in en['summary'].items()
        }
        for cat, curd in en['cat_totals'].items():
            by_acc_cur[cat]['total'] = { cur : f"{v.v:6.2f}" for cur, v in curd.items() }

        total_by_acc = {f"{acc}_{cur}" : f"{v.v:6.2f}" for acc, accd in en['acc_totals'].items() for cur, v in accd.items()}
        total_by_acc['total'] = {cur : f"{v.v:6.2f}" for cur, v in en['spent_total'].items()}

        acc_curs = ['usd_USD','usd_BYN', 'byn_BYN','usd_RUB','byn_RUB','rub_RUB','credit_RUB', 'total']
        headers = ['cat'] + acc_curs
        _sum = [
            [cat] + [accurd.get(acc_cur, '') for acc_cur in acc_curs] \
                for cat, accurd in [('income',by_acc_cur['income'])] + sorted([(k,v) for k,v in by_acc_cur.items() if k != 'income'], key=lambda kv: kv[0])
        ]
        _sum += [['total'] + [total_by_acc.get(acc_cur, '') for acc_cur in acc_curs]]

        return tabulate(_sum, headers=headers)

    def write_summary_to_excel(self, en_no_tr, by_cat):

        expenses_by_day = self.expenses_by_day(en_no_tr)

        # eval speed
        headers = [''] + [d.day for d in sorted(expenses_by_day.keys())] + ['avg_7']
        all_curs = {tr.currency for d, trs in expenses_by_day.items() for tr in trs}
        def tr_format(tr):
            return f"{tr.account}-{tr.category} {tr.amount:6.2f} {tr.src.category}"

        def _make_row(_cur, collapse=True):
            if collapse:
                by_day_sums = [sum([tr.amount for tr in trs if tr.currency == _cur]) for d,trs in sorted(expenses_by_day.items(), key=lambda kv: kv[0])]
                return [f'by day,{_cur}'] + by_day_sums + [np.mean(by_day_sums[-7:])]
            else:
                by_day_sums = [[tr_format(tr) for tr in trs if tr.currency == _cur] for d,trs in sorted(expenses_by_day.items(), key=lambda kv: kv[0])]
                return by_day_sums
        
        rows = [ _make_row(_cur) for _cur in all_curs] 
        rowsc = [ _make_row(_cur, collapse=False) for _cur in all_curs] 

        def addr(c,r):
            return str(chr(ord('A')+c))+str(r+1)

        workbook = xlsxwriter.Workbook('summary.xlsx')
        worksheet = workbook.add_worksheet()

        for i,h in enumerate(headers):            
            worksheet.write(addr(i,0), h)
        for r, row in enumerate(rows):
            for c,v in enumerate(row):
                worksheet.write(addr(c,r+1), v)
        for r, row in enumerate(rowsc):
            for c,trs in enumerate(row):
                worksheet.write_comment(addr(c+1,r+1), str(trs))

        # worksheet.write_comment('A1', 'This is a comment')
        workbook.close()        

    def speed_by_day(self, en):
        ret = defaultdict(lambda: defaultdict(float))
        for tr in en:
            ret[tr.date.date()][tr.currency] += min(tr.amount, 0)
        return ret

    def expenses_by_day(self, en):
        ret = defaultdict(list)
        for tr in en:
            ret[tr.date.date()] += [tr]
        return ret

    def printable_speed(self, spd):
        headers = [''] + [d.day for d,v in sorted(spd.items(), key=lambda kv: kv[0])] + ['avg_7']
        d_minus_7 = max(spd.keys()) - datetime.timedelta(days=7)
        all_curs = {cur for d, curd in spd.items() for cur,v in curd.items()}
        def _make_row(_cur):
            return [f'by day,{_cur}'] + \
            [v for d,curd in sorted(spd.items(), key=lambda kv: kv[0]) for cur, v in curd.items() if cur == _cur] + \
            [np.mean([v for d, curd in spd.items() if d > d_minus_7 for cur,v in curd.items() if cur == _cur])]
        row = [ _make_row(_cur) for _cur in all_curs] 
        return tabulate(row, headers=headers)

    def sterilize(self, obj):
        if isinstance(obj, datetime.datetime):
            return str(obj)
        assert False, str(type(obj))

    def go(self):
        en = self.read_datadir()
        en = self.to_unified_rec(en)
        en = self.filter_by_date(en)
        en = list(en)
        en = sorted(en, key=lambda tr: tr.date)

        with open(self.args.allout, 'w') as f:
            json.dump(en, f, indent=4, default=self.sterilize, ensure_ascii=False)

        en_no_tr = self.filter_transfers(en)
        en_no_tr = list(en_no_tr)        

        # expenses_by_day = self.expenses_by_day(en_no_tr)
        # expenses_by_day = [(str(d),trs) for d, trs in sorted(expenses_by_day.items(), key=lambda kv: kv[0])]

        # with open(self.args.bydayout, 'w') as f:
        #     json.dump(expenses_by_day, f, indent=4, default=self.sterilize, ensure_ascii=False)

        spd = self.speed_by_day(en_no_tr)
        print(self.printable_speed(spd))
        print('\n')

        by_cat = self.group_by_category(en)
        print(self.printable_summary(by_cat))

        self.write_summary_to_excel(en_no_tr, by_cat)

        # with open(self.args.sumout, 'w') as f:
        #     json.dump(en, f, indent=4, default=self.sterilize, ensure_ascii=False)

    @staticmethod
    def main(args):
        logging.basicConfig(level=logging.INFO if not args.debug else logging.DEBUG)
        Main(args).go()

if __name__ == "__main__":
    Main.main(Main.make_parser().parse_args())
