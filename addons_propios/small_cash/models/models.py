# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    dv = fields.Char(string="D.V. VAT/Tax ID")

class SmallCashAccountMove(models.Model):
    _inherit = 'account.move'

    expense_id = fields.Many2one('hr.expense', string='Ref de Gasto', index=True)

class Small_Cash_Expense(models.Model):
    _inherit = 'hr.expense'

    supplier_invoice = fields.One2many('account.move', 'expense_id',"Ref. Fact. Proveedor", domain=[('move_type', '=', 'in_invoice')], context={'default_move_type': 'in_invoice'})
    vat = fields.Char(string="VAT/Tax ID")
    dv_vat = fields.Char(string="D.V. VAT/Tax ID")
    partner_id = fields.Many2one('res.partner', readonly=True, tracking=True,
        states={'draft': [('readonly', False)]},
        check_company=True,
        string='Partner', change_default=True, ondelete='restrict')
    partner_name = fields.Char(
        'Company Name', tracking=20, index=True,
        readonly=False, store=True,
        help='Nombre del Proveedor')
    #untaxed_amount = fields.Float("Subtotal", store=True, compute='_compute_amount_tax', digits='Account', copy=True)
    taxed_amount = fields.Float("Impuesto", store=True, digits='Account', copy=True)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        # OVERRIDE
        print("Cambiando partner y asignando nombre y datos fiscales...")
        self.partner_name = self.partner_id.name
        self.vat = self.partner_id.vat
        self.dv_vat = self.partner_id.dv
        #res = super(AccountMove, self)._onchange_partner_id()
        #res = super(Small_Cash_Expense, self)._onchange_partner_id()
        return 
    
    @api.onchange('supplier_invoice')
    def _onchange_supplier_invoice(self):
        self.partner_name = self.supplier_invoice.partner_id.name
        self.vat = self.supplier_invoice.partner_id.vat
        self.partner_id = self.supplier_invoice.partner_id.id
        self.taxed_amount = self.supplier_invoice.amount_tax
        self.untaxed_amount = self.supplier_invoice.amount_untaxed
        self.total_amount = self.supplier_invoice.amount_total
        self.untaxed_amount = self.total_amount - self.taxed_amount
        self.reference = self.supplier_invoice.ref
        if (self.partner_name != False and self.supplier_invoice.ref != False and self.product_id.name):
            self.name = self.partner_name + '/' + self.supplier_invoice.ref + '-' + self.product_id.name
        
        return
    
    @api.onchange('taxed_amount','total_amount')
    def _onchange_(self):
        self.untaxed_amount = self.total_amount - self.taxed_amount
        return