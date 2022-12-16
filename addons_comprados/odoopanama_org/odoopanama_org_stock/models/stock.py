# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Picking(models.Model):
	_inherit = "stock.picking"

	pa_invoice_ids = fields.Many2many(comodel_name="stock.picking", string="Pickings", 
									compute ="_compute_pa_invoice_ids", readonly=True)
	pa_invoice_name = fields.Char("Internal Number", compute ="_compute_pa_invoice_ids")
	
	pa_number = fields.Char("Numero de Guia")
	

	
	@api.model
	def _compute_pa_invoice_ids(self):
		pa_invoice_ids = False
		pa_invoice_name=[]
		for stock_id in self:
			stock_id.sale_id
			pa_invoice_ids = stock_id.sale_id.order_line.invoice_lines.move_id.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund'))
			if pa_invoice_ids:
				pa_invoice_name = pa_invoice_ids.mapped('name')
			stock_id.pa_invoice_ids=pa_invoice_ids and pa_invoice_ids.ids or []
			stock_id.pa_invoice_name = ", ".join(pa_invoice_name) or False
