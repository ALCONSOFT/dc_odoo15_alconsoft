# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta


class PePaymentDate(models.Model):

    _name = "pe.payment.date"
    _description = "Panama Payment Date"

    amount = fields.Float("Monto", required=True, )
    date = fields.Date("Fecha", required=True)
    order_id = fields.Many2one("sale.order", "Order")
    move_id = fields.Many2one("account.move", "Invoice")
    number_quot = fields.Char(string="Line Nº", compute='_compute_number')
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

    def _compute_number(self):
        number_quot = 1
        for move in self:
            move.number_quot = ("Cuota-{}".format(str(number_quot)))
            number_quot += 1

    def get_payment_values(self):
        res = []
        for line in self:
            res.append((0, 0, {'amount': line.amount, 'date': line.date}))
        return res

    @api.model
    def get_payment_by_qty_date(self):
        date_start = self.env.context.get(
            'pe_payment_date_start') or fields.Date.context_today(self)
        date_end = self.env.context.get(
            'pe_payment_date_end') or fields.Date.context_today(self)
        qty = self.env.context.get('pe_payment_qty') or 1
        amount = self.env.context.get('pe_payment_amount') or 0
        pa_payment_method = self.env.context.get('pa_payment_method')
        amount_part = round(amount/qty, 2)
        date_vals = {}
        odate_start = fields.Date.from_string(date_start)
        odate_end = fields.Date.from_string(date_end)
        days = (odate_end - odate_start).days
        quote_part = int(round(days / qty, 0))
        for i in range(qty):
            if i != qty-1:
                odate_start = odate_start+timedelta(quote_part)
            else:
                odate_start = odate_end
            date_vals[i] = fields.Date.to_string(odate_start)
        res = []
        for i in range(qty):
            res.append((0, 0, {'pa_payment_method': pa_payment_method,
                       'amount': amount_part, 'date': date_vals[i]}))
            amount -= amount_part
            if i == qty-1:
                amount_part = amount

        return res
