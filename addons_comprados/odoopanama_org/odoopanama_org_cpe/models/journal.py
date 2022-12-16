# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_cpe = fields.Boolean("Es un CPE")
    is_synchronous = fields.Boolean("Es sincrono")
    pa_payment_method = fields.Selection(
        selection=[
            ('01', 'Crédito'),
            ('02', 'Contado'),
            ('03', 'Tarjeta Crédito'),
            ('04', 'Tarjeta Débito'),
            ('05', 'Tarjeta Fidelización'),
            ('06', 'Vale'),
            ('07', 'Tarjeta de Regalo'),
            ('08', 'Transf/Deposito cta Bancaria '),
            ('99', 'Otro.'),
        ],
        string='Método de pago para DGI',
        help='Método de pago para envio de FE-DGI')
