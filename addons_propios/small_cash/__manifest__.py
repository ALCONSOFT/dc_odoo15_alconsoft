# -*- coding: utf-8 -*-
{
    'name': "small_cash",

    'summary': """
        Adecuacion del modulo hr_expense para gestion de caja chica o menuda - Panama""",

    'description': """
        Adecuación del modulo hr_expense para la gestión de caja menuda o caja chica.
        La caja chica gestiona pagos a terceros o reemblsos para facilitar la gestion de
         los gastos y costos en proyectos o gestión en operaciones fuera o lejos de la 
         Administración de la Empresa o Proyecto.
    """,

    'author': "Alconsoft",
    'website': "http://alconsoft.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accountig',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr_expense'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        #'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
