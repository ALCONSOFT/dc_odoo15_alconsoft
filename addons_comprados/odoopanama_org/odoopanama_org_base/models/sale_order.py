# -*- coding: utf-8 -*-
from odoo import api, fields, models


# class SaleOrderLine(models.Model):
#     _inherit = "sale.order.line"

#     pa_license_plate = fields.Char("Placa Vehicular", readonly=True, states={
#                                    'draft': [('readonly', False)]}, copy=False)


# class SaleOrder(models.Model):
#     _inherit = "sale.order"

#     pa_license_plate = fields.Char("Placa Vehicular", readonly=True, states={
#                                    'draft': [('readonly', False)]}, copy=False)

#     @api.onchange('pa_license_plate')
#     def onchange_pa_license_plate(self):
#         for line in self.order_line:
#             if line.product_id.require_plate:
#                 line.pa_license_plate = self.pa_license_plate
