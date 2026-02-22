# -*- coding: utf-8 -*-


to_9 = ("", "", "", "ثلاث", "أربع", "خمس", "ست", "سبع", "ثماني", "تسع")
to_19 = (
    "صفر",
    "واحد",
    "اثنان",
    "ثلاثة",
    "أربعة",
    "خمسة",
    "ستة",
    "سبعة",
    "ثمانية",
    "تسعة",
    "عشرة",
    "أحد عشر",
    "اثنا عشر",
    "ثلاثة عشر",
    "أربعة عشر",
    "خمسة عشر",
    "ستة عشر",
    "سبعة عشر",
    "ثمانية عشر",
    "تسعة عشر",
)

tens = (
    "عشرون",
    "ثلاثون",
    "أربعون",
    "خمسون",
    "ستون",
    "سبعون",
    "ثمانون",
    "تسعون",
)
denom = ("", "ألف", "مليون", "مليار", "تريليون", "كوادريليون")


def _convert_nn(val):
    """convert a value < 100 to English."""
    if val < 20:
        return to_19[val]
    for dcap, dval in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens)):
        if dval + 10 > val:
            if val % 10:
                return to_19[val % 10] + " و " + dcap
            return dcap


def _convert_nnn(val):
    """
    convert a value < 1000 to english, special cased because it is the level that kicks
    off the < 100 special case.  The rest are more general.  This also allows you to
    get strings in the form of 'forty-five hundred' if called directly.
    """
    word = ""
    (mod, rem) = (val % 100, val // 100)
    if rem < 3 and rem > 0:
        word = "مائة" if rem == 1 else "مائتين"
    elif rem < 10 and rem > 2:
        word = to_9[rem] + "مائة"
        if mod > 0:
            word += " "

    if rem > 9:
        word = to_19[rem] + " مائة"
        if mod > 0:
            word += " "
    if mod > 0:
        word += " "
        word += "و" + " " + _convert_nn(mod)
    return word


def english_number(val):
    if val < 100:
        return _convert_nn(val)
    if val < 1000:
        return _convert_nnn(val)
    for didx, dval in ((v - 1, 1000**v) for v in range(len(denom))):
        if dval > val:
            mod = 1000**didx
            l = val // mod
            r = val - (l * mod)
            if l < 100:
                ret = _convert_nn(l) + " " + denom[didx]
            else:
                ret = _convert_nnn(l) + " " + denom[didx]
            if r > 0:
                ret = ret + " و " + english_number(r)
            return ret


def _get_currency_name_by_code(cur):
    result = {
        "SDG": ["جنيه", "قروش", "قرش"],
        "AED": ["درهم", "فلسات", "فلس"],
        "CFA": ["فرنك", "سنتات", "سنت"],
        "EGP": ["جنيه", "قروش", "قرش"],
        "EUR": ["يورو", "سنتات", "سنت"],
        "USD": ["دولار", "سنتات", "سنت"],
        "SSP": ["جنيه", "قروش", "قرش"],
        "SAR": ["ريال", "هللات", "هللة"],
    }
    return result[cur.upper()]


def amount_to_text_arabic(number, currency):
    number = "%.2f" % number
    units_name = currency
    list = str(number).split(".")
    start_word = english_number(int(list[0]))
    end_word = english_number(int(list[1]))
    cents_number = int(list[1])
    cents_name = (
        (cents_number > 10 or cents_number == 0)
        and _get_currency_name_by_code(currency)[2]
        or _get_currency_name_by_code(currency)[1]
    )
    #
    # return ' '.join(filter(None,
    #                        [start_word, units_name,  'و'.decode('utf-8'),
    #                         end_word, cents_name]))
    return (
        "فقط "
        + start_word
        + " "
        + _get_currency_name_by_code(currency)[0]
        + " "
        + "و"
        + " "
        + end_word
        + " "
        + cents_name
    )


def number_to_text(number):
    number = "%.2f" % number
    list = str(number).split(".")
    start_word = english_number(int(list[0]))
    end_word = english_number(int(list[1]))
    cents_number = int(list[1])
    # cents_name = (cents_number > 10 or cents_number == 0)

    return start_word + " " + "يوما"
