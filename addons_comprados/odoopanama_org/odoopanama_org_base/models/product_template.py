# -*- coding: utf-8 -*-
from odoo import models, fields


# class ProductTemplate(models.Model):
#     _inherit = 'product.template'
    
#     l10n_pe_withhold_code = fields.Selection(
#         selection=[],
#         string="Cód. de Detracción",
#         help="Catalogo No. 54 SUNAT. Códigos de bienes y servicios sujetos a detracciones")
#     l10n_pe_withhold_percentage = fields.Float(
#         string="Porcentaje de Detracción",
#         help="Porcentajes de detracción ")


# class ProductCategory(models.Model):
#     _inherit = "product.category"

#     unspsc_code_id = fields.Many2one('product.unspsc.code', 'UNSPSC Product Category', domain=[('applies_to', '=', 'product')],
#                                      help='The UNSPSC code related to this product.  Used for edi in Colombia, Panama and Mexico')
