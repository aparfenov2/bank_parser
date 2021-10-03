import sqlalchemy as sq
from sqlalchemy.orm import declarative_base

db_base_t = declarative_base()

class trs_t(db_base_t):
    __tablename__ = 'trs'
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    account = sq.Column(sq.String,  nullable=False)
    currency = sq.Column(sq.String,  nullable=False)
    adate = sq.Column(sq.DateTime, nullable=False)
    amount = sq.Column(sq.Float, nullable=False)
    descr = sq.Column(sq.UnicodeText, nullable=False)
    ahash = sq.Column(sq.String,  unique=True, index=True, nullable=False)
    # ahash = sq.Column(sq.String, nullable=False)

    def __repr__(self) -> str:
        return f"id {self.id} acc {self.account} curr {self.currency} adate {self.adate} amnt {self.amount} hash {self.ahash} descr {self.descr}"
