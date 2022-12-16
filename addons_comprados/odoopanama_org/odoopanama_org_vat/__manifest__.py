# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2022-TODAY OdooPanama.org - email: odoopanama.org@gmail.com - Whatsapp: +51 925019870
#	
###############################################################################
{
	'name': "Registro RUC - Panama",
	'summary': "Registro RUC - Panama",
	'description': "Registro de contactos - Panama",
	'author': "odoopanama.org@gmail.com",
	'website': "http://www.odoopanama.org",
	'category': 'Generic Modules/Base',
	'category': 'Uncategorized',
	'version': '14.0.1',
	'depends': ['base', 'l10n_pa','l10n_latam_base','base_address_city'],
	'data': [
		'security/ir.model.access.csv',
		'data/res.country.state.csv',
		'data/res.city.csv',
		'data/l10n_pa.res.city.corregimiento.csv',
		'data/l10n_latam_identification_type_data.xml',
		'views/res_partner_view.xml',		
	],
	'demo': [],
	'installable': True,
	'license': 'Other proprietary',
	"sequence": 10,
	'support': 'odoopanama.org@gmail.com',
}
