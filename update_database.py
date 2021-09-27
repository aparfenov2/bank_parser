import argparse, os, datetime, re
import logging
from gen_summary import Main as _Main, trs_t, db_base_t
from enum import Enum
from typing import Dict, Any
import hashlib
import json
import sqlalchemy as sq

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
    def get_hash(account, c, salt=0):
        vc = {
            'account' : account,
            'currency': c.currency,
            'adate'   : c.date.strftime('%Y-%m-%d'),
            'amount'  : "{:.2f}".format(c.amount),
            'descr'   : re.sub(r"[^0-9a-zA-Zа-яёА-ЯЁ]",'',c.category).upper(),
            }
        if salt > 0:
            vc['salt'] = salt
        return Main.dict_hash(vc)

    def update_database(self, en):
        # db_is_new = not os.path.exists(self.args.database)
        # with sqlite3.connect(self.args.database) as conn:

        db = sq.create_engine(self.args.database)
        Session = sq.orm.sessionmaker(db)
        db_base_t.metadata.create_all(db)

        with Session() as session:
            used_hashes = set()

            for account, c in en:
                try:
                    salt = 0
                    ahash = self.get_hash(account, c, salt)
                    while ahash in used_hashes:
                        salt += 1
                        new_hash = self.get_hash(account, c, salt)
                        self.logger.warning(f"repeated hash {ahash} for account {account} c {c} new hash {new_hash} salt {salt}")
                        ahash = new_hash
                    used_hashes.add(ahash)

                    item = session.query(trs_t).where(trs_t.ahash == ahash).first()
                    # vc = {'ahash' : ahash}
                    # cursor.execute("SELECT * FROM trs WHERE ahash = :ahash", vc)
                    # item = cursor.fetchone()
                    if item is not None:
                        self.logger.info(f"matched hash {ahash} to id {item.id} account={account}, c={c}, item={item}")
                    else:
                        item = trs_t()
                        item.account = account
                        item.currency = c.currency
                        item.adate = c.date
                        item.amount = c.amount
                        item.descr = c.category
                        item.ahash = ahash
                        # vc = {
                        #     'account' : account,
                        #     'currency': c.currency,
                        #     'adate'   : c.date.strftime('%Y-%m-%d %H:%M:%S'),
                        #     'amount'  : c.amount,
                        #     'descr'   : c.category,
                        #     'ahash'   : ahash
                        #     }
                    #     not_none = list(vc.keys())
                    #     cursor.execute("INSERT INTO trs ({}) VALUES ({})" \
                    #         .format(", ".join(not_none), ", ".join([":"+f for f in not_none])), vc)
                    # conn.commit()
                        session.add(item)
                        session.commit()
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
