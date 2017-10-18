# -*- coding: utf-8 -*-
{
    'name': "general_ledger_account_filter",

    'summary': """
        Module to add extra account filter in odoo acounting general ledger 
        """,

    'description': """
        This module is to add extra filter (account filter) in account_reports general ledger.
    """,

    'author': "Tradetec",
    'website': "http://www.tradetec.info",

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'account_reports'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
#         'views/templates.xml',
#         'views/views.xml',
    ],
    'qweb': [
#         'static/src/xml/account_report_backend.xml',
    ],    
    'js': [ 
#         "static/src/js/account_reports_backend.js" 
    ],
    'license': 'OEEL-1'
}