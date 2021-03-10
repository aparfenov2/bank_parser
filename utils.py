import csv,re, datetime, os

# json -friendly named tuple
def named_dict(typename, fieldnames):

    def ctor(self, *args):
        for k,v in zip(self._fields, args):
            setattr(self,k, v)
        super(self.__class__, self).__init__(self.__dict__)

    d = {f:None for f in fieldnames}
    d['__init__'] = ctor
    d['_fields']  = fieldnames
    return type(typename, (dict,), d)

rec_t = named_dict('rec_t', ['date', 'op', 'amount', 'currency', 'amount_byn', 'category', 'filename', 'lineno'])

def read_transactions(filename):
    transactions = []
    # Дата транзакции;Операция;Сумма;Валюта;Дата операции по счету;Комиссия/Money-back;Обороты по счету;Цифровая карта;Категория операции;

    with open(filename, 'r', encoding="windows-1251") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        for lineno, row in enumerate(csv_reader):
            # ret = re.match(r'Операции по.*?(\d+)', row[0]):
            if len(row) < 10:
                # print(row)
                continue
            ret = re.match(r'(\d\d)\.(\d\d)\.(\d\d\d\d) (\d\d)\:(\d\d)\:(\d\d)', row[0])
            if ret:
                # print(len(row))
                tstamp = datetime.datetime.strptime(row[0], '%d.%m.%Y %H:%M:%S')
                op = row[1]
                amount = float(row[2].replace(',','.').replace(' ',''))
                currency = row[3]
                amount_byn = float(row[-4].replace(',','.').replace(' ',''))
                category = row[-2]
                if len(category.strip()) == 0:
                    category = op
                transactions.append(rec_t(tstamp, op, amount, currency, amount_byn, category, os.path.basename(filename), lineno))

    return transactions


alfa_t = named_dict('alfa_t', ['account_name', 'account_num', 'currency', 'date', 'ref', 'category', 'amount', 'filename', 'lineno'])

def read_alfa(filename):
    transactions = []
    # Тип счёта Номер счета Валюта  Дата операции   Референс проводки   Описание операции   Приход  Расход

    with open(filename, 'r', encoding="windows-1251") as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=';')
        for lineno, row in enumerate(csv_reader):
            try:
                account_name = row['Тип счёта']
                if len(account_name) == 0:
                    continue
                account_num  = row['Номер счета']
                currency     = row['Валюта'].replace('RUR','RUB')
                tstamp       = datetime.datetime.strptime(row['Дата операции'], '%d.%m.%y')
                ref          = row['Референс проводки']
                category     = row['Описание операции']
                income       = float(row['Приход'].replace(',','.'))
                spent        = float(row['Расход'].replace(',','.'))
                amount       = income - spent
                transactions.append(alfa_t(account_name, account_num, currency, tstamp, ref, category, amount, os.path.basename(filename), lineno))
            except Exception as e:
                raise Exception(f"line {lineno}", e)

    return transactions
