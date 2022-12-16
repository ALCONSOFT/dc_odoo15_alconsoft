# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import re
from . import amount_to_text_es
import logging
_logging = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    amount_text = fields.Char("Monto en letras", compute="_get_amount_text")
    pa_related_ids = fields.Many2many(
        "account.move", string="Facturas relacionadas", compute="_get_related_ids")
    annul = fields.Boolean('Anulado', readonly=True)
    state = fields.Selection(
        selection_add=[('annul', 'Anulado'), ], ondelete={'annul': 'cascade'})

    def button_annul(self):
        self.button_cancel()
        self.write({'annul': True, 'state': 'annul'})
        return True

    @api.depends('amount_total')
    def _get_amount_text(self):
        for invoice in self:
            if invoice.amount_total < 2 and invoice.amount_total >= 1:
                currency_name = invoice.currency_id.singular_name or invoice.currency_id.plural_name or invoice.currency_id.name or ""
            else:
                currency_name = invoice.currency_id.plural_name or invoice.currency_id.name or ""
            fraction_name = invoice.currency_id.fraction_name or ""
            amount_text = invoice.currency_id.amount_to_text(
                invoice.amount_total)
            invoice.amount_text = amount_text

    @api.depends('invoice_line_ids')
    def _get_related_ids(self):
        for move_id in self:
            related_ids = move_id.invoice_line_ids.mapped(
                'pa_invoice_id').ids or []
            if move_id.debit_origin_id:
                related_ids.append(move_id.debit_origin_id.id)
            if move_id.reversed_entry_id:
                related_ids.append(move_id.reversed_entry_id.id)
            move_id.pa_related_ids = related_ids

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        res = super(AccountMove, self)._prepare_refund(invoice, date_invoice=date_invoice, date=date,
                                                       description=description, journal_id=journal_id)
        journal_id = res.get('journal_id')
        if journal_id and not self.env.context.get("is_pa_debit_note"):
            journal = self.env['account.journal'].browse(journal_id)
            res['journal_id'] = journal.credit_note_id and journal.credit_note_id.id or journal.id
        elif journal_id and self.env.context.get("is_pa_debit_note"):
            journal = self.env['account.journal'].browse(journal_id)
            res['journal_id'] = journal.dedit_note_id and journal.dedit_note_id.id or journal.id
            res['type'] = "out_invoice"
            res['refund_invoice_id'] = invoice.id
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    amount_discount = fields.Float(
        "Amount Discount", compute="_compute_amount_discount")
    pa_invoice_ids = fields.Many2many('account.move', 'pa_account_invoice_line_invoice_rel',
                                      'line_id', 'move_id', string="Invoices lines", copy=False, readonly=True)
    pa_invoice_id = fields.Many2one(
        'account.move', string="Invoices", copy=False, readonly=True)

    @api.depends('price_unit', 'discount', 'move_id.currency_id')
    def _compute_amount_discount(self):
        for line in self:
            price = line.price_unit * (line.discount or 0.0) / 100.0
            amount_discount = line.tax_ids.compute_all(price, line.move_id.currency_id,
                                                       line.quantity, line.product_id, line.move_id.partner_id)
            line.amount_discount = amount_discount['total_excluded']
