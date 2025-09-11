import re
from unidecode import unidecode
from datetime import datetime

card_types = {
    "visa":{
        "key": "visa",
        "name": "Visa",
        "regex": "^4\\d{15}$",
        "cvvMax": 999,
        "masterpassKey": "visa",
    },
    "mastercard":{
        "key": "mastercard",
        "name": "MasterCard",
        "regex": "^5[1-5]\\d{14}$|^2(?:2(?:2[1-9]|[3-9]\\d)|[3-6]\\d\\d|7(?:[01]\\d|20))\\d{12}$",
        "cvvMax": 999
    },
    "americanexpress":{
        "key": "americanexpress",
        "name": "American Express",
        "regex": "^3[4,7]\\d{13}$",
        "cvvMax": 9999
    },
    "discovercard":{
        "key": "discovercard",
        "name": "Discover",
        "regex": "^(?=6011|622(12[6-9]|1[3-9][0-9]|[2-8][0-9]{2}|9[0-1][0-9]|92[0-5]|64[4-9])|65)\\d{16}$",
        "cvvMax": 999
    }
}

def cc_type(card_number):
    for typ in card_types.values():
        if re.match(typ['regex'], card_number):
            return typ
    return {"key": "unknown","name": "Unknown","regex": "","cvvMax": 0}
def luhn(n):
    r = [int(ch) for ch in str(n)][::-1]
    return (sum(r[0::2]) + sum(sum(divmod(d*2,10)) for d in r[1::2])) % 10 == 0
def find_cc(text):
    text = unidecode(text)
    cc_pattern = r'(?:^|[^0-9])(\d{15,20})(?:[^0-9]|$)'
    cc = re.search(cc_pattern, text)
    if not cc:
        cc = re.search(cc_pattern, re.sub(r'\s(\d{4})', r'\1', text))
    exp_pattern = r'(?:^|[^0-9])(?:(?:(\d{2}|20\d{2})([^0-9a-zA-Z])\2*?(\d{2}))|(?:(\d{2})([^0-9a-zA-Z])\5*?(\d{2}|20\d{2})))(?:[^0-9]|$)'
    exp = re.search(exp_pattern, text)
    if not exp:
        exp = re.search(exp_pattern, text.replace(' ', ''))
    if not exp:
        exp_pattern2 = r'(?:^|[^0-9])(?:(0\d|1[012])((?:20)?[23]\d))(?:[^0-9]|$)'
        exp = re.search(exp_pattern2, text)
        if exp:
            exp = re.search(exp_pattern, f"{exp[1]}|{exp[2]}")
    if not cc or not exp or not luhn(cc[1]):
        return None
    cvv_pattern = r'(?:^|[^0-9])(\d{{{}}})(?:[^0-9]|$)'.format(len(str(cc_type(cc[1])['cvvMax'])))
    cvv = re.search(cvv_pattern, text)
    if not cvv:
        return None
    exp = [exp[1] if exp[1] else exp[4], exp[3] if exp[3] else exp[6]]
    if len(exp[0])==4 or not (exp[0].startswith('0') or exp[0].startswith('1')):
        y = exp[0]
        m = exp[1]
    else:
        y = exp[1]
        m = exp[0]
    y = y if len(y)==2 else y[2:]
    return cc[1], f'0{m}'[-2:], f'{str(datetime.now().year)[:2]}{y}'[-4:], cvv[1]
