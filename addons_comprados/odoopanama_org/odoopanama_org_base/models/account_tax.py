# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class AccountTax(models.Model):
	_inherit = 'account.tax'

	pa_is_charge = fields.Boolean("Cambio")



