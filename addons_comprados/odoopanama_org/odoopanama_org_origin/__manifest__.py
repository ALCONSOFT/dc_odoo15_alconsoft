# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2022-TODAY OdooPanama.org - email: odoopanama.org@gmail.com - Whatsapp: +51 925019870
#	
###############################################################################

{
    'name': 'Origen de Documentos Rectificados',
    'version': '14.0.1.0.0',
	'author': "odoopanama.org@gmail.com",
	'website': "http://www.odoopanama.org",
    'summary': '''
        Create in the credit notes (rectifying invoices), several fields that allow identifying the document that the credit or debit note is rectifying.
    ''',
    'category': 'Accounting',
    'depends': ['account','l10n_latam_invoice_document'],
    'data': ['views/account_move_views.xml'],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 2.00
}
