import sys, os, re, datetime, json
from utils import read_transactions, read_alfa, named_dict
import argparse, logging
from collections import namedtuple, defaultdict
from typing import List, DefaultDict, Dict, Union
# from mypy_extensions import TypedDict
from tabulate import tabulate

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
                    cat = tr.op
                tr = uni_t(_type, tr.date, tr.amount, tr.currency, cat, tr)
                cat = self.get_category(tr)
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

    def get_category(self, tr : uni_t):

        if tr.amount > 0:
            return 'income'

        cat_defs = {
            'sadik' : [r'Парфенов\s+Сергей'],
            'kv' : [r'в пользу"ЧЕЛЯБИНВЕСТБАНК"'],
            'kv_otop' : [r'RU GOROD74.RU'],
            'cash' : [r'Alfa Iss'],
            'taxi' : [r'TAXI'],
            'eats' : [r'MAGNIT', r'PYATEROCHKA'],
            'to KATE' : [r'на \+79511286005'],
            'gas' : [r'GAZPROMNEFT'],
            'to RUB' : [r'P2P_SDBO_INTERNATIONAL'],
            'to BYN' : [r'P2P SDBO NO FEE'],
            'Kate eats' : [r'STOLOVAYA VILKA'],
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

        for cat, accd in summary.items():
            if cat != 'income':
                for acc, curd in accd.items():
                    for cur, v in curd.items():
                        cat_totals[cat][cur] += v
                        acc_totals[acc][cur] += v
                        spent_total[cur] += v

        return {
            'summary' : summary, 
            'cat_totals' : cat_totals, 
            'acc_totals' : acc_totals, 
            'spent_total' : spent_total
            }

    def printable_summary(self, en):
        by_acc_cur = {
            cat : {
                f"{acc}_{cur}" : f"{v.v:6.0f}" for acc, curd in accd.items() for cur, v in curd.items()
            } for cat, accd in en['summary'].items()
        }
        for cat, curd in en['cat_totals'].items():
            by_acc_cur[cat]['total'] = { cur : f"{v.v:6.0f}" for cur, v in curd.items() }

        total_by_acc = {f"{acc}_{cur}" : f"{v.v:6.0f}" for acc, accd in en['acc_totals'].items() for cur, v in accd.items()}
        total_by_acc['total'] = {cur : f"{v.v:6.0f}" for cur, v in en['spent_total'].items()}

        acc_curs = ['usd_USD','usd_BYN', 'byn_BYN','usd_RUB','byn_RUB','rub_RUB','credit_RUB', 'total']
        headers = ['cat'] + acc_curs
        _sum = [
            [cat] + [accurd.get(acc_cur, '') for acc_cur in acc_curs] \
                for cat, accurd in sorted(by_acc_cur.items(), key=lambda kv: kv[0])
        ]
        _sum += [['total'] + [total_by_acc.get(acc_cur, '') for acc_cur in acc_curs]]

        return tabulate(_sum, headers=headers)

    def go(self):
        en = self.read_datadir()
        en = self.to_unified_rec(en)
        en = self.filter_by_date(en)
        en = list(en)
        en = sorted(en, key=lambda tr: tr.date)

        def sterilize(obj):
            if isinstance(obj, datetime.datetime):
                return str(obj)
            assert False, str(type(obj))

        with open(self.args.allout, 'w') as f:
            json.dump(en, f, indent=4, default=sterilize, ensure_ascii=False)

        en = self.group_by_category(en)

        print(self.printable_summary(en))

        with open(self.args.sumout, 'w') as f:
            json.dump(en, f, indent=4, default=sterilize, ensure_ascii=False)

    @staticmethod
    def main(args):
        logging.basicConfig(level=logging.INFO if not args.debug else logging.DEBUG)
        Main(args).go()

if __name__ == "__main__":
    Main.main(Main.make_parser().parse_args())
