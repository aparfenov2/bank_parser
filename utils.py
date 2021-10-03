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

    def lookup_header(lines, reg):
        for i,l in enumerate(lines):
            ret = re.search(reg, l)
            if ret is not None:
                return i
        return None

    def read_op_sum(lines, start):
        csv_reader = csv.DictReader(lines, delimiter=';')
        for lineno, row in enumerate(csv_reader):
            lineno += start
            tstamp = datetime.datetime.strptime(row['Дата транзакции'], '%d.%m.%Y %H:%M:%S')
            op = row['Операция']
            amount = float(row['Сумма'].replace(',','.').replace(' ',''))
            currency = row['Валюта']
            amount_byn = float(row['Обороты по счету'].replace(',','.').replace(' ',''))
            category = row['Категория операции']
            transactions.append(rec_t(tstamp, op, amount, currency, amount_byn, op+';'+category, os.path.basename(filename), lineno))

    def read_blocked(lines, start):
        csv_reader = csv.reader(lines, delimiter=';')
        headers = None
        for lineno, row in enumerate(csv_reader):
            if lineno == 0:
                headers = row
                continue
            rowh = {k : v for k,v in zip(headers, row)}
            lineno += start
            tstamp = datetime.datetime.strptime(rowh['Дата транзакции'], '%d.%m.%Y %H:%M:%S')
            op = rowh['Транзакция']
            amount = float(rowh['Сумма транзакции'].replace(',','.').replace(' ',''))
            currency = row[3]
            amount_byn = float(rowh['Сумма блокировки'].replace(',','.').replace(' ',''))
            category = rowh['Категория операции']
            transactions.append(rec_t(tstamp, op, -amount, currency, -amount_byn, op+';'+category, os.path.basename(filename), lineno))

    with open(filename, 'r', encoding="windows-1251") as f:
        lines = f.readlines()

    start = lookup_header(lines, r'Дата транзакции;Операция;Сумма;')
    if start is None:
        raise Exception(f"cant find header in bad csv {filename}")
    end = lookup_header(lines[start:], r'Всего по контракту;Зачислено;Списано;')
    if end is None:
        raise Exception(f"cant find footer in bad csv {filename}")
    end += start
    read_op_sum(lines[start:end], start)

    start = lookup_header(lines[end:], r'Дата транзакции;Операция;Сумма;')
    if start is not None:
        start += end
        end = lookup_header(lines[start:], r'Всего по контракту;Зачислено;Списано;')
        end += start
        read_op_sum(lines[start:end], start)

    start = lookup_header(lines[end:], r'Дата транзакции;Транзакция;Сумма')
    if start is not None:
        start += end
        read_blocked(lines[start:], start)    

    return transactions


alfa_t = named_dict('alfa_t', ['account_name', 'account_num', 'currency', 'date', 'ref', 'category', 'amount', 'filename', 'lineno'])

def read_alfa(filename):
    transactions = []
    # Тип счёта Номер счета Валюта  Дата операции   Референс проводки   Описание операции   Приход  Расход

    with open(filename, 'r', encoding="windows-1251") as f:
        csv_reader = csv.DictReader(f, delimiter=';')
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
