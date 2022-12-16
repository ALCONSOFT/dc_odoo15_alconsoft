# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2022-TODAY OdooPanama.org - email: odoopanama.org@gmail.com - Whatsapp: +51 925019870
#
###############################################################################
{
    'name': "Estructura para CPE",
    'summary': """
		Estructura y datos base para emitir cpe a DGI - Panama""",

    'description': """
		Base para Facturación Electrónica - Panama 
		Estructura y datos base para emitir cpe a DGI - Panama
	""",
    'author': "odoopanama.org@gmail.com",
    'website': "http://www.odoopanama.org",
    'category': 'Financial',
    'version': '0.1.01',
    'depends': [
            'l10n_pa',
            'account',
            'sale_management',
            'account_debit_note',
            'l10n_latam_invoice_document',
            'odoopanama_org_vat',
            'odoopanama_org_origin'
    ],
    'data': [
        'data/res_currency_data.xml',
        'data/l10n_latam_document_type_data.xml',
        'data/pe.datas.csv',
        'views/pe_datas_view.xml',
        'views/res_currency_view.xml',
        'views/account_journal_view.xml',
        'views/account_view.xml',
        # 'views/product_view.xml',
        'views/account_invoice_debit_view.xml',


    ],
    'installable': True,
    'license': 'Other proprietary',
    'application': True,
}
