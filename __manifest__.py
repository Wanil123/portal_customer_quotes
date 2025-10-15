# -*- coding: utf-8 -*-
{
    'name': 'Portal Customer Quotes',
    'version': '17.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Allow portal users to create and manage their quotes',
    'description': """
Portal Customer Quotes
======================
* Clients (Portail) : lister / créer / modifier leurs soumissions (états brouillon/envoyée)
* Sélection de produit au niveau variante (product.product)
* Affichage image / variantes / description
* Frais d’expédition fixe Québec : 37,00 $
* I18n complet (FR/EN)
* Validations côté client & serveur
    """,
    'author': 'Wanil Parfait',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['sale', 'portal', 'product', 'account', 'delivery'],
    'data': [
        'security/ir.model.access.csv',
        'security/portal_record_rules.xml',
        'views/portal_templates.xml',
        'reports/quote_reports.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
