{
    'name': "hospital_base",

    'summary': "alfourqan Base",

    'description': """
alfourqan Base Customization partners, users
    """,

    'author': "Ahmed Amen",
    'website': "https://www.yourcompany.com",
    'support': "mahmudamen@gmail.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Hospital',
    'version': "18.0.1.0.0",

    # any module necessary for this one to work correctly
    'depends': ['base','mail','contacts', 'product','purchase', 'account','account_accountant', 'hr', 'sale','planning','web_gantt'],
    'demo': [],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/access_rights.xml',
        'data/contract_sequence.xml',
        'data/reception_sequence.xml',
        'data/surgeries_sequence.xml',
        'data/clinic_sequence.xml',
        'data/lab_sequence.xml',
        'data/system_params.xml',
        #'wizard/clinic_visit_wizard.xml',
        'views/res_users.xml',
        'views/hospital_menu.xml',
        'views/insurance_contract.xml',
        'views/sections.xml',
        'views/product.xml',
        'views/res_partner.xml',
        'views/clinics.xml',
        'views/doctors.xml',
        'views/patient.xml',
        'views/surgeries.xml',
        'views/catheterization.xml',
        'views/rooms.xml',
        'views/clinic_visit.xml',
        'views/inpatient.xml',
        'views/laboratory.xml',
        'views/radiology.xml',
        'views/reception_new.xml',
        'views/accounting_reception.xml',
        'views/hospital_config.xml',
        'views/sale_order.xml',
        'views/other.xml',
        'views/nursing_service.xml',
        'views/lab_service.xml',
        'report/reception_receipt.xml',
        'report/clinic_print.xml',
        'report/report_radiology.xml',
        'views/visit_dosage.xml',
        'views/visit_duration.xml',
        'views/surgery_slots.xml',
        'report/inpatient_report.xml',
        'report/patient_exit_report.xml',
        'views/account_payment_cash.xml',
        'wizard/patient_exit_wizard_view.xml',
        #'security/pharma_security.xml',
        #'views/dashboard_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            #'https://cdn.jsdelivr.net/npm/chart.js',
            'hospital_base/static/src/js/kanban.js',
            'hospital_base/static/src/js/inpatient_form.js',
            'hospital_base/static/src/css/surgery_gantt.scss',
            'hospital_base/static/src/scss/hospital_sections_kanban.scss',
            'hospital_base/static/src/js/room_kanban_style.js',
            'hospital_base/static/src/css/rooms_dashboard.scss',
            'hospital_base/static/src/css/kanban.css',
            #'hospital_base/static/src/scss/inpatient_form.scss',
            'hospital_base/static/src/scss/inpatient_form_extended.scss',
            'hospital_base/static/src/js/doctor_services_kanban.js',
            'hospital_base/static/src/scss/doctor_services_kanban.scss',
            #'hospital_base/static/src/scss/furkan.scss',
            'hospital_base/static/src/components/dashboard/patient_file_dashboard.js',
            'hospital_base/static/src/components/dashboard/patient_file_dashboard.scss',
            'hospital_base/static/src/xml/patient_templates.xml',

        ],
        'web.report_assets_common': [
            'hospital_base/static/src/fonts/Tajawal-Regular.ttf',
            'hospital_base/static/src/fonts/Tajawal-Bold.ttf',
        ],
    },
}
