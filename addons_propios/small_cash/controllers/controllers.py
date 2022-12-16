# -*- coding: utf-8 -*-
# from odoo import http


# class SmallCash(http.Controller):
#     @http.route('/small_cash/small_cash', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/small_cash/small_cash/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('small_cash.listing', {
#             'root': '/small_cash/small_cash',
#             'objects': http.request.env['small_cash.small_cash'].search([]),
#         })

#     @http.route('/small_cash/small_cash/objects/<model("small_cash.small_cash"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('small_cash.object', {
#             'object': obj
#         })
