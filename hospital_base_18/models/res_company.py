from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    cash_receivable_acc = fields.Many2one('account.account',string="حساب كاش العملاء",
                                          check_company=True,
                                          domain="[('account_type', '=', 'asset_receivable'),"
                                                 " ('deprecated', '=', False)]")
    cash_receivable_partner = fields.Many2one('res.partner',string="حساب الشركة",
                                              check_company=True,
                                              readonly=False, )
    main_cash_journal = fields.Many2one('account.journal',string="يومية الخزينة الرئيسية",
                                        check_company=True,
                                        domain=[('type', '=', 'cash')])
    main_cash = fields.Many2one('account.account',string="حساب الخزينة الرئيسية ",
                                check_company=True,
                                domain="[('account_type', '=', 'asset_cash'), "
                                       "('deprecated', '=', False)]")
    service_exp_account = fields.Many2one('account.account',string="حساب مصروفات الخدمات",
                                          check_company=True,
                                          domain="[('account_type', '=', 'income_other'), ('deprecated', '=', False)]")
    service_tax_account = fields.Many2one('account.account',string="حساب الضريبة علي الخدمات",
                                          check_company=True,
                                          domain="[('account_type', '=', 'income_other'), ('deprecated', '=', False)]")
    reception_journal = fields.Many2one('account.journal',string="يومية الاستقبال",
                                        check_company=True,
                                        domain=[('type', '=', 'general')])
    doctor_due_account = fields.Many2one('account.account',string="حساب مصاريف الاطباء",
                                         check_company=True,
                                         domain="[('account_type', '=', 'expense'), ('deprecated', '=', False)]")
    doctor_discount_account = fields.Many2one('account.account',string="حساب خصم الاطباء", check_company=True)
    inpatient_journal = fields.Many2one('account.journal',
                                        check_company=True, readonly=False,
                                        domain=[('type', '=', 'general')])
    surgery_tax_account = fields.Many2one('account.account',string="حساب ضرائب الجراحة", check_company=True)
    surgery_tax = fields.Float(default=0, digits='Product Price', string="الضريبة علي الجراحة", check_company=True)
    nursing_exp = fields.Float(default=0, digits='Product Price',string="مصاريف التمريض", check_company=True)
    nursing_tax = fields.Float(default=0, digits='Product Price',string="ضريبة التمريض", check_company=True)
    inpatient_deposit = fields.Many2one('account.account', check_company=True,
                                        readonly=False,string="حساب تامين الداخلي ",
                                        domain="[('account_type', '=', 'liability_payable'),"
                                               " ('deprecated', '=', False)]")
    outpatient_deposit = fields.Many2one('account.account', check_company=True,string="حساب الخروج",
                                         readonly=False, domain="[('account_type', '=', 'liability_payable'),"
                                                                " ('deprecated', '=', False)]")
    contract_journal = fields.Many2one('account.journal',
                                       domain=[('type', '=', 'sale')], string="يومية التعاقدات")
