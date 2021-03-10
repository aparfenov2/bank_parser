import sys, os, re, datetime, json
from utils import read_transactions, read_alfa, named_dict
import argparse, logging
from collections import namedtuple, defaultdict
from typing import List, DefaultDict, Dict, Union
# from mypy_extensions import TypedDict

uni_t = named_dict('uni_t', ['account', 'date', 'amount', 'currency', 'category', 'src'])

class list_and_float_t(dict):
    def __init__(self, v=0., trs=[]):
        self.v : float = v
        self.trs : List[uni_t] = trs
        super().__init__(self.__dict__)

    def __add__(self, o):
        return list_and_float_t(self.v + o.v, self.trs + o.trs)

class Main:
    @staticmethod
    def make_parser():
        parser = argparse.ArgumentParser()
        parser.add_argument('csvdir')
        parser.add_argument('--debug', action='store_true')
        parser.add_argument('--days_ago', type=int)
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
        if self.args.days_ago is not None:
            min_date = datetime.today() - datetime.timedelta(days=self.args.days_ago)
            self.logger.info(f"min_date {min_date}")

        for _type, trs in en:
            #['date', 'amount', 'currency', 'category', 'src']
            for tr in trs:
                if self.args.days_ago is not None:
                    if tr.date < min_date:
                        continue
                if _type in ['rub', 'credit']:
                    yield uni_t(_type, tr.date, tr.amount, tr.currency, tr.category, tr)
                else:
                    yield uni_t(_type, tr.date, tr.amount, tr.currency, tr.op, tr)

    def get_category(self, tr : uni_t):
        cat_defs = {
            'sadik' : [r'Парфенов\s+Сергей']
        }
        for cat, regs in cat_defs.items():
            for reg in regs:
                ret = re.search(reg, tr.category)
                if ret:
                    return cat
            if tr.amount > 0:
                return 'income'
            return 'other'

    def group_by_category(self, en : List[uni_t]):
        # ValueOrlistDict = TypedDict('ValueOrlistDict', {
        #         'v'   : float,
        #         'trs' : List[uni_t]
        #     })

        summary : DefaultDict[str,DefaultDict[str, DefaultDict[str, list_and_float_t]]] = \
            defaultdict(lambda: defaultdict(lambda: defaultdict(list_and_float_t)))

        for tr in en:
            cat = self.get_category(tr)
            summary[cat][tr.account][tr.currency].v += tr.amount
            summary[cat][tr.account][tr.currency].trs += [tr]

        cat_totals : DefaultDict[str,DefaultDict[str,list_and_float_t]] = defaultdict(lambda: defaultdict(list_and_float_t))
        acc_totals : DefaultDict[str,DefaultDict[str,list_and_float_t]] = defaultdict(lambda: defaultdict(list_and_float_t))
        spent_total : DefaultDict[str,list_and_float_t] = defaultdict(list_and_float_t)

        for cat, accd in summary.items():
            for acc, curd in accd.items():
                for cur, v in curd.items():
                    cat_totals[cat][cur] += v
                    acc_totals[acc][cur] += v
                    spent_total[cur] += v if cat != 'income' else list_and_float_t()

        return {
            'summary' : summary, 
            'cat_totals' : cat_totals, 
            'acc_totals' : acc_totals, 
            'spent_total' : spent_total
            }

    def go(self):
        en = self.read_datadir()
        en = self.to_unified_rec(en)
        en = list(en)
        en = sorted(en, key=lambda tr: tr.date)

        def sterilize(obj):
            if isinstance(obj, datetime.datetime):
                return str(obj)
            assert False, str(type(obj))

        with open(self.args.allout, 'w') as f:
            json.dump(en, f, indent=4, default=sterilize, ensure_ascii=False)

        en = self.group_by_category(en)

        with open(self.args.sumout, 'w') as f:
            json.dump(en, f, indent=4, default=sterilize, ensure_ascii=False)

    @staticmethod
    def main(args):
        logging.basicConfig(level=logging.INFO if not args.debug else logging.DEBUG)
        Main(args).go()

if __name__ == "__main__":
    Main.main(Main.make_parser().parse_args())
