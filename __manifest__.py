{
    'name': 'Garments TNA & Templates',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Garments time and action plans with reusable, editable milestone templates',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/dynamic_template_views.xml',
        'views/garments_tna_views.xml',
    ],
    'installable': True,
    'application': True,
}
