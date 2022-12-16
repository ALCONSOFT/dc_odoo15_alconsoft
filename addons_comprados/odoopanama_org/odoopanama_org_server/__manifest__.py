# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2022-TODAY OdooPanama.org - email: odoopanama.org@gmail.com - Whatsapp: +51 925019870
#	
###############################################################################
{
    'name': "Server Administration",

    'summary': """
        Server Administration""",

    'description': """
        Server Administration
    """,
    'author': "odoopanama.org@gmail.com",
	'website': "http://www.odoopanama.org",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Localization/Panamanian',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'l10n_pa',
    ],
    # always loaded
    'data': [
        'views/res_company.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'license': 'Other proprietary',
    'installable': True,
}
