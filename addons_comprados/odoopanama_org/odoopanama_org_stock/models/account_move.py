# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import re
import logging
_logging = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    pa_stock_ids = fields.Many2many(comodel_name="stock.picking", string="Pickings",
                                    compute="_compute_pa_stock_ids", readonly=True, copy=False)
    pa_stock_name = fields.Char(
        "Número de picking", compute="_compute_pa_stock_ids", copy=False)

    def _compute_pa_stock_ids(self):
        contador = 0
        for invoice in self:
            contador = contador + 1
            if invoice.debit_origin_id or invoice.reversed_entry_id:
                invoice.pa_stock_ids = False
                invoice.pa_stock_name = ""
                continue
            picking_ids = invoice.invoice_line_ids.mapped('sale_line_ids').mapped(
                'order_id').mapped('picking_ids')  # self._cr.fetchall()
            pa_stock_ids = []
            pa_stock_name = ""
            numbers = []
            for picking_id in picking_ids:
                if picking_id.state not in ['draft', 'cancel']:
                    numbers.append(picking_id.name)
                    pa_stock_ids.append(picking_id.id)
            if numbers:
                if len(numbers) == 1:
                    pa_stock_name = numbers[0]
                else:
                    pa_stock_name = " - ".join(numbers)
            invoice.pa_stock_ids = False if len(
                pa_stock_ids) == 0 else pa_stock_ids
            invoice.pa_stock_name = pa_stock_name


    