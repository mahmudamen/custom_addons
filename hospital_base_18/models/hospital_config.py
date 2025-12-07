from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    cash_receivable_acc = fields.Many2one('account.account',
                                          check_company=True,
                                          related='company_id.cash_receivable_acc', readonly=False,
                                          domain="[('account_type', '=', 'asset_receivable'),"
                                                 " ('deprecated', '=', False)]", string="عملاء نقدي")
    cash_receivable_partner = fields.Many2one('res.partner',
                                              check_company=True,
                                              related='company_id.cash_receivable_partner', readonly=False, string="عملاء نقدي")
    main_cash_journal = fields.Many2one('account.journal',
                                        check_company=True,
                                        related='company_id.main_cash_journal', readonly=False,
                                        domain=[('type', '=', 'cash')], string="يومية الخزينة الرئيسية")
    main_cash = fields.Many2one('account.account',
                                check_company=True,
                                related='company_id.main_cash', readonly=False,
                                domain="[('account_type', '=', 'asset_cash'), "
                                       "('deprecated', '=', False)]", string="حساب الخزينة الرئيسية")
    service_exp_account = fields.Many2one('account.account',
                                          check_company=True, readonly=False,
                                          related='company_id.service_exp_account',
                                          domain="[('account_type', '=', 'income_other'), ('deprecated', '=', False)]", string="حساب مصروفات ادارية")
    service_tax_account = fields.Many2one('account.account',
                                          check_company=True, readonly=False,
                                          related='company_id.service_tax_account',
                                          domain="[('account_type', '=', 'income_other'), ('deprecated', '=', False)]", string="حساب الضريبة")
    reception_journal = fields.Many2one('account.journal',
                                        check_company=True, readonly=False,
                                        related='company_id.reception_journal',
                                        domain=[('type', '=', 'general')], string="يومية الاستقبال")
    doctor_due_account = fields.Many2one('account.account',
                                         check_company=True, readonly=False,
                                         related='company_id.doctor_due_account',
                                         domain="[('account_type', '=', 'expense'), ('deprecated', '=', False)]", string="حساب الاطباء")
    doctor_discount_account = fields.Many2one('account.account',
                                              check_company=True, readonly=False,
                                              related='company_id.doctor_discount_account', string="حساب خصم الاطباء")
    inpatient_journal = fields.Many2one('account.journal',
                                        check_company=True, readonly=False,
                                        related='company_id.inpatient_journal',
                                        domain=[('type', '=', 'general')], string="يومية الداخلي")
    surgery_tax_account = fields.Many2one('account.account',
                                          check_company=True, readonly=False,
                                          related='company_id.surgery_tax_account', string="حساب المصاريف الادارية")
    surgery_tax = fields.Float(default=0, digits='Product Price',
                               config_parameter='hospital.surgery_tax', string="قيمة المصاريف الادارية")
    nursing_exp = fields.Float(default=0, digits='Product Price',
                               config_parameter='hospital.nursing_exp', string="مصروفات تمريض")
    nursing_tax = fields.Float(default=0, digits='Product Price',
                               config_parameter='hospital.nursing_tax', string="ضريبة تمريض")
    inpatient_deposit = fields.Many2one('account.account', check_company=True, related='company_id.inpatient_deposit',
                                        readonly=False,
                                        domain="[('account_type', '=', 'liability_payable'),"
                                               " ('deprecated', '=', False)]", string="أمانت مرضي الداخلي")
    outpatient_deposit = fields.Many2one('account.account', check_company=True, related='company_id.outpatient_deposit',
                                         readonly=False, domain="[('account_type', '=', 'liability_payable'),"
                                                                " ('deprecated', '=', False)]", string="امانات مرضي الخارجي")
    contract_journal = fields.Many2one('account.journal',
                                        check_company=True, readonly=False,
                                        related='company_id.contract_journal',
                                        domain=[('type', '=', 'sale')], string="يومية التعاقدات")
