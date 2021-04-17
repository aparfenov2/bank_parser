import argparse, os, datetime
import logging
from gen_summary import Main as _Main
from enum import Enum
from typing import Dict, Any
import hashlib
import json, sqlite3

class Account(Enum):
    USD_prior = 'usd'
    BYN_prior = 'byn'
    Alfa = 'rub'
    Credit = 'credit'
    Kate = 'sb_kate'

class Currency(Enum):
    USD = 'USD'
    BYN = 'BYN'
    RUB = 'RUB'

class Main(_Main):

    @staticmethod
    def make_parser():
        parser = argparse.ArgumentParser()
        parser.add_argument('csvdir')
        # parser.add_argument('--days_after', type=int)
        # parser.add_argument('--days_before', type=int)
        parser.add_argument('database')
        # parser.add_argument('--after',  type=lambda s: datetime.datetime.strptime(s, '%d.%m.%Y'))        
        # parser.add_argument('--before', type=lambda s: datetime.datetime.strptime(s, '%d.%m.%Y'))        
        return parser

    DB_SCHEMA = """
create table trs (
    id           integer primary key autoincrement not null,
    account      text not null,
    currency     text not null,
    adate        datetime not null,
    amount       float not null,
    descr        text not null,
    ahash        text not null
);
    """

    @staticmethod
    def dict_hash(dictionary: Dict[str, Any]) -> str:
        """MD5 hash of a dictionary."""
        dhash = hashlib.md5()
        # We need to sort arguments so {'a': 1, 'b': 2} is
        # the same as {'b': 2, 'a': 1}
        encoded = json.dumps(dictionary, sort_keys=True).encode()
        dhash.update(encoded)
        return dhash.hexdigest()    

    @staticmethod
    def get_hash(account, c):
        vc = {
            'account' : account,
            'currency': c.currency,
            'adate'   : c.date.strftime('%Y-%m-%d %H:%M:%S'),
            'amount'  : c.amount,
            'descr'   : c.category,
            }
        return Main.dict_hash(vc)

    def update_database(self, en):
        db_is_new = not os.path.exists(self.args.database)
        with sqlite3.connect(self.args.database) as conn:
            conn.set_trace_callback(self.logger.info)
            if db_is_new:
                self.logger.info(f'Creating database schema for db {self.args.database}')
                conn.executescript(self.DB_SCHEMA)
                conn.commit()
            cursor = conn.cursor()
            for account, c in en:
                try:
                    vc = {'ahash' : self.get_hash(account, c)}
                    cursor.execute("SELECT * FROM trs WHERE ahash = :ahash", vc)
                    item = cursor.fetchone()
                    if item is not None:
                        print(item)
                        self.logger.info(f"matched hash {self.get_hash(account,c)} to id {item[0]} account={account}, c={c}, item={item}")
                    else:
                        vc = {
                            'account' : account,
                            'currency': c.currency,
                            'adate'   : c.date.strftime('%Y-%m-%d %H:%M:%S'),
                            'amount'  : c.amount,
                            'descr'   : c.category,
                            'ahash'   : self.get_hash(account, c)
                            }
                        not_none = list(vc.keys())
                        cursor.execute("INSERT INTO trs ({}) VALUES ({})" \
                            .format(", ".join(not_none), ", ".join([":"+f for f in not_none])), vc)
                    conn.commit()
                except Exception:
                    self.logger.exception("")
                yield c

    def emit_trs(self, en):
        for account, trs in en:
            for tr in trs:
                yield account, tr

    def main(self):
        en = self.read_datadir()
        en = self.emit_trs(en)
        # en = self.to_unified_rec(en)
        # en = self.filter_by_date(en)
        # en = list(en)
        # en = sorted(en, key=lambda tr: tr.date)
        en = self.update_database(en)
        list(en)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    Main(Main.make_parser().parse_args()).main()
