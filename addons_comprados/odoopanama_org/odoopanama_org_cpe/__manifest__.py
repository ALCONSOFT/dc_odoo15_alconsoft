# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2022-TODAY OdooPanama.org - email: odoopanama.org@gmail.com - Whatsapp: +51 925019870
#	
###############################################################################
{
	'name': "Factura Electronica Panama",
	'summary': """
		Emision de comprobantes electronicos a DGI - Panamá""",

	'description': """
		Facturación electrónica - Panamá 
		Emision de comprobantes electronicos a DGI - Panamá
	""",
	'author': "odoopanama.org@gmail.com",
	'website': "http://www.odoopanama.org",
	'category': 'Financial',
	'version': '15.0.1.2',
	'depends': [
			'l10n_pa',
			'odoopanama_org_unspsc',
			'odoopanama_org_server',
			'odoopanama_org_base',
			'web'
	],
	'data': [
		'security/security.xml',
		'security/ir.model.access.csv',
		'data/cron.xml',
		'data/template_email_cpe.xml',
		'views/assets.xml',
        'views/account_journal_view.xml',
        'views/account_move_view.xml',
        'views/odoopanama_cpe_view.xml',
        # 'report/report_invoice_ticket.xml',
		'report/report_invoice_document.xml',
        'wizard/account_invoice_debit_view.xml',
		'wizard/account_move_annul_view.xml',
		
	],
	'installable': True,
	'license': 'Other proprietary',
	'application': True,
	"sequence": 1,
}
