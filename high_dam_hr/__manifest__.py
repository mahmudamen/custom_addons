# -*- coding: utf-8 -*-
{
    'name': "high_dam_hr",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/hr_security.xml',
        'views/main_menu.xml',
        'views/hr_employee.xml',
        'views/qualitative_group.xml',
        'views/hr_sufficiency_report.xml',
        'report/print_report_emp.xml',
        'views/hr_punch.xml',
        'views/hr_department.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
