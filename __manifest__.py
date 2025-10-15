{
    'name': 'Portal Customer Quotes',
    'version': '17.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Allow portal users to create and manage their quotes',
    'description': """
Portal Customer Quotes
======================
* Clients can create, edit, and delete their own quotes (draft/sent states)
* Product selection with category filtering
* Image/variant/description display
* Fixed shipping fee for Quebec: $37.00
* Full i18n support (FR/EN)
* Client-side and server-side validation
    """,
    'author': 'Wanil Parfait',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['sale', 'portal', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'security/portal_record_rules.xml',
        'views/portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'portal_customer_quotes/static/src/css/quote.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}