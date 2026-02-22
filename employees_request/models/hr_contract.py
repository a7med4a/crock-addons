# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError
import calendar
from datetime import date
from num2words import num2words
import math
import re
import uuid
from .money_to_text_ar import amount_to_text_arabic
from .money_to_text_ar import number_to_text


class HrContractT(models.Model):
    _inherit = "hr.contract"

    day = fields.Char("Day", compute="_get_day_name", translate=True, readonly=False)
    day_ar = fields.Char("Day", compute="_get_day_name_ar")
    # contract_rep = fields.Many2one('hr.employee',string='Contract Representative')

    @api.depends("date_start")
    def _get_day_name(self):
        for record in self:
            if record.date_start:
                d = record.date_start
                record.day = calendar.day_name[d.weekday()]
            else:
                record.day = "/"

    @api.depends("day")
    def _get_day_name_ar(self):
        for record in self:
            record.day_ar = "/"
            if record.day == "Wednesday":
                record.day_ar = "الأربعاء"
            if record.day == "Thursday":
                record.day_ar = "الخميس"
            if record.day == "Friday":
                record.day_ar = "الجمعة"
            if record.day == "Saturday":
                record.day_ar = "السبت"
            if record.day == "Sunday":
                record.day_ar = "الأحد"
            if record.day == "Monday":
                record.day_ar = "الاثنين"
            if record.day == "Tuesday":
                record.day_ar = "الثلاثاء"

    def compute_amount_in_word_en(self, amount):
        if self.env.user.lang == "en_US":
            num_word = str(self.currency_id.amount_to_text(amount)) + " only"
            return num_word
        elif self.env.user.lang == "ar_001":
            num_word = num2words(amount, to="currency", lang=self.env.user.lang)
            num_word = str(num_word) + " فقط"
            return num_word

    def amount_text_arabic(self, amount):
        return amount_to_text_arabic(amount, self.currency_id.name)

    def _number_to_text(self, num):
        return number_to_text(num)
