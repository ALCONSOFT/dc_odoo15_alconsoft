# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2022-TODAY OdooPanama.org - email: odoopanama.org@gmail.com - Whatsapp: +51 925019870
#
###############################################################################
{
    'name': "CPE-Stock",
    'summary': """
		Estructura y datos base para emitir cpe a DGI - Panama""",

    'description': """
		Base para Facturación Electrónica - Panama 
		Estructura y datos base para emitir cpe a DGI - Panama
	""",
    'author': "odoopanama.org@gmail.com",
    'website': "http://www.odoopanama.org",
    'category': 'Stock',
    'version': '0.1',
    'depends': [
            'l10n_pa',
            'stock',
            'odoopanama_org_base'
    ],
    'data': [
        'views/stock_view.xml',
        'report/report_picking.xml'
    ],
    'installable': True,
    'license': 'Other proprietary',
    'application': True,
}
