from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import ValidationError


class ContractPriceLists(models.Model):
    _name = 'contract.price.lists'
    _rec_name = 'name'
    _description = 'Contract Price Lists'

    name = fields.Char(required=True, string="الاسم")
    service_ids = fields.One2many("contract.price.lists.lines", inverse_name="price_list_id", copy=True)


class ContractPriceListsLines(models.Model):
    _name = 'contract.price.lists.lines'
    _description = 'Contract Price Lists Lines'

    price_list_id = fields.Many2one('contract.price.lists', string="قائمة الاسعار")
    service_id = fields.Many2one('product.template', required=True, domain=[('detailed_type', '=', 'service')], string="الخدمة")
    price = fields.Float(default=0, digits='Product Price', required=True, string="السعر")

    _sql_constraints = [
        ('unique_service_contract',
         'unique(price_list_id, service_id)',
         'الخدمة موجودة بالفعل.')
    ]


class InsuranceContractor(models.Model):
    _name = 'insurance.contractor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Insurance Contract'

    name = fields.Char(tracking=True, index=True, readonly=True, copy=False, default=lambda self: '/', string="الاسم")
    partner_id = fields.Many2one('res.partner', domain=[('is_insurance', '=', True)], required=True, copy=False, string="الشركة")
    date_from = fields.Date(default=lambda self: fields.Date.context_today(self), required=True, string="تاريخ البداية")
    date_to = fields.Date(default=lambda self: fields.Date.context_today(self) + timedelta(days=365), required=True, string="تاريخ النهاية")
    auto_renew = fields.Boolean(default=True, string="تجديد تلقائي")
    line_ids = fields.One2many("insurance.contractor.lines", inverse_name="contract_id", copy=True)
    local_discount = fields.Float(default=0, digits='Product Price', required=True, string="خصم أدوية محلية")
    imported_discount = fields.Float(default=0, digits='Product Price', required=True, string="خصم أدوية مستوردة")
    active = fields.Boolean(default=True, string="الحالة")
    price_list = fields.Many2one('contract.price.lists', string="قائمة الاسعار")
    exp_amount = fields.Float(default=0, digits='Product Price', required=True, string="مصروفات")
    tax_amount = fields.Float(default=0, digits='Product Price', required=True, string="ضريبة")

    _sql_constraints = [
        ('check_dates', 'CHECK(date_to > date_from)', 'يرجي مراجعة التاريخ')
    ]

    @api.onchange('price_list')
    def onchange_price_list(self):
        for rec in self:
            if rec.price_list:
                lst = []
                for line in rec.price_list.service_ids:
                    lst.append((0, 0, {
                        'service_id': line.service_id.id,
                        'price': line.price
                    }))
                rec.line_ids = lst

    @api.model_create_multi
    def create(self, values_list):
        # التأكد من أنها قائمة
        if not isinstance(values_list, list):
            values_list = [values_list]

        for values in values_list:
            if 'partner_id' in values:
                partner = values.get('partner_id')
                check = self.env['insurance.contractor'].search([
                    ('partner_id', '=', partner),
                    ('active', '=', True)
                ])
                if check:
                    raise ValidationError(_("الشركة لها عقد ساري واحد فقط"))

            if not values.get('name'):
                values['name'] = self.env['ir.sequence'].next_by_code('insurance.contract')

        return super(InsuranceContractor, self).create(values_list)


class InsuranceContractorLines(models.Model):
    _name = 'insurance.contractor.lines'
    _rec_name = 'name'
    _description = 'Insurance Contract Lines'

    name = fields.Char(compute="compute_name", store=True, index=True, string="الاسم")
    contract_id = fields.Many2one('insurance.contractor', string="العقد")
    partner_id = fields.Many2one(related="contract_id.partner_id", store=True, string="الشركة")
    active = fields.Boolean(related="contract_id.active", store=True, string="الحالة")
    service_id = fields.Many2one('product.template', required=True, domain=[('detailed_type', '=', 'service')], string="الخدمات")
    approval = fields.Boolean(default=False, string="يتطلب موافقة")
    price = fields.Float(default=0, digits='Product Price', required=True, string="السعر")

    _sql_constraints = [
        ('unique_service_contract',
         'unique(contract_id, service_id)',
         'الخدمة مسجلة بالفعل.')
    ]

    @api.depends('service_id')
    def compute_name(self):
        for rec in self:
            rec.name = ""
            if rec.service_id:
                rec.name = rec.service_id.name


class ServiceApproval(models.Model):
    _name = 'service.approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Service Approval'

    name = fields.Char(tracking=True, index=True, readonly=True, copy=False, default=lambda self: '/', string="الاسم")
    description = fields.Char(tracking=True, string="بيان")
    visit_id = fields.Many2one('clinic.visit')
    patient_file = fields.Many2one('patient.file', string="ملف المريض")
    room_id = fields.Many2one(related="patient_file.room_id", string="الغرفة")
    bed_id = fields.Many2one(related="patient_file.bed_id", string="السرير")
    service_id = fields.Many2one('product.template', string="الخدمة")
    doctor_id = fields.Many2one('res.partner', required=True, domain=[('is_doctor', '=', True)], string="الطبيب")
    patient_id = fields.Many2one('res.partner', required=True, domain=[('is_patient', '=', True)], string="المريض")
    service_provider = fields.Many2one('res.partner', domain=[('is_service_provider', '=', True)], string="مقدم الخدمة")
    patient_account = fields.Selection(related="patient_id.patient_account",default="cash" , store=True, readonly=False, string="نوع الحساب")
    patient_employer = fields.Many2one(related="patient_id.employer", store=True, readonly=False, string="الشركة التابع لها")
    patient_contract_company = fields.Many2one(related="patient_id.contract_company", store=True, readonly=False, string="شركة التعاقد")
    state = fields.Selection(string="الحالة", selection=[('waiting', 'Waiting'),
                                                        ('accepted', 'Accept'),
                                                        ('refused', 'Refused'),
                                                        ('refund', 'Refund'),
                                                        ('done', 'Done')], default='waiting', required=False)
    deposit_amount = fields.Float(default=0, digits='Product Price', string="قيمة الامانات")
    patient_per = fields.Float(default=0, digits='Product Price', string="نسبة التحمل")
    approve_number = fields.Char(string="رقم الموافقة")
    section_id = fields.Many2one('res.sections', string="القسم")
    account_journal = fields.Many2one('account.journal', domain=[('type', '=', 'cash')], string="اليومية")
    refund_move = fields.Many2one('account.move', string="قيد رد الامانات")

    @api.onchange('patient_per')
    def onchange_patient_per(self):
        for rec in self:
            if rec.patient_per < 0:
                rec.patient_per = 0
                raise ValidationError(_("النسبة يجب ان تكون بين 0 - 100"))

    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            values['name'] = self.env['ir.sequence'].next_by_code('insurance.contract.approve')
        return super(ServiceApproval, self).create(values)

    def action_accept(self):
        for rec in self:
            rec.state = 'accepted'

    def button_refused(self):
        for rec in self:
            rec.state = 'refused'

    def button_waiting(self):
        for rec in self:
            rec.state = 'waiting'

    def deposit_refund(self):
        self.ensure_one()
        if not self.account_journal:
            raise ValidationError(_("يجب تحديد يومية الخزينة"))
        if self.refund_move:
            raise ValidationError(_("تم رد الامانات من قبل"))
        move_lines = [(5, 0, 0)]
        deposit_acc = self.env.company.inpatient_deposit.id if self.section_id.type == 'inpatient' else self.env.company.inpatient_deposit.id
        debit_line = (0, 0, {
            "account_id": self.account_journal.default_account_id.id,
            "partner_id": self.patient_id.id,
            "debit": self.deposit_amount
        })
        credit_line = (0, 0, {
            "account_id": deposit_acc,
            "partner_id": self.patient_id.id,
            "credit": self.deposit_amount
        })
        move_lines.append(debit_line)
        move_lines.append(credit_line)
        cash_entry = {
            'date': fields.Date.today(),
            'journal_id': self.account_journal.id,
            'ref': _('رد امانات %s') % self.name,
            'line_ids': move_lines
        }
        entry_cash = self.env["account.move"].create(cash_entry)
        entry_cash.action_post()
        self.refund_move = entry_cash.id
        self.state = 'refund'

    def create_reservation(self):
        self.ensure_one()
        doctor = self.doctor_id.id
        return {
            'type': 'ir.actions.act_window',
            'name': _("Clinic Visit"),
            'res_model': 'clinic.visit',
            'view_mode': 'form',
            'views': [[self.env.ref('hospital_base.reception_clinic_visit_form').id, "form"]],
            'target': 'new',
            'context': {
                'default_doctor_id': doctor,
                'default_approve_id': self.id,
                'default_service_id': self.service_id.id,
                'default_patient_id': self.patient_id.id,
                'default_deposit_amount': self.deposit_amount,
                'default_patient_per': self.patient_per
            }
        }


class ContractClaim(models.Model):
    _name = 'contract.claim'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Contract Claims'

    name = fields.Char(tracking=True, index=True, readonly=True, copy=False, default=lambda self: '/', string="كود")
    contract_id = fields.Many2one('insurance.contractor', required=True, domain=[("active", "!=", False)])
    contract_company = fields.Many2one(related='contract_id.partner_id', store=True)
    from_date = fields.Date(required=True)
    to_date = fields.Date(required=True)
    state = fields.Selection(string="State", selection=[('draft', 'Draft'), ('invoiced', 'Invoiced'), ('post', 'Post'), ('canceled', 'Canceled')],
                             default='draft', required=True)
    invoice_id = fields.Many2one('account.move')
    type = fields.Selection(string="نوع المطالبة",
                            selection=[('med', 'Medicines'), ('services', 'Services')],
                            default="services", required=True)
    line_ids = fields.One2many(comodel_name="contract.claim.lines", inverse_name="claim_id", required=False)
    total_amount = fields.Float(default=0, digits='Product Price', compute="compute_claim_total", string="الاجمالي")
    total_patient = fields.Float(default=0, digits='Product Price', compute="compute_claim_total", string="ما تحمله المرضي")
    total_company = fields.Float(default=0, digits='Product Price', compute="compute_claim_total", string="المحمل علي الشركة")

    @api.onchange('from_date', 'to_date')
    def onchange_dates(self):
        if self.from_date and self.to_date:
            if self.from_date > self.to_date:
                raise ValidationError(_("يرجي مراجعة التاريخ"))

    @api.depends('line_ids', 'line_ids.company_amount')
    def compute_claim_total(self):
        for rec in self:
            rec.total_amount = 0
            rec.total_patient = 0
            rec.total_company = 0
            if rec.line_ids:
                rec.total_amount = sum(rec.line_ids.mapped('total_amount'))
                rec.total_patient = sum(rec.line_ids.mapped('patient_amount'))
                rec.total_company = sum(rec.line_ids.mapped('company_amount'))

    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            values['name'] = self.env['ir.sequence'].next_by_code('insurance.contract.claim')
        return super(ContractClaim, self).create(values)

    def button_generate(self):
        for rec in self:
            rec.line_ids = False
            services = self.env['clinic.visit'].search([('patient_contract_company', '=', rec.contract_company.id),
                                                        ('date', '>=', rec.from_date),
                                                        ('date', '<=', rec.to_date),
                                                        ('canceled', '=', False)])
            if not services:
                raise ValidationError(_("لا توجد خدمات مقدمة خلال الفترة المحددة"))
            lst = []
            for service in services:
                lst.append((0, 0, {
                    'visit_id': service.id,
                    'patient_id': service.patient_id.id,
                    'service_id': service.service_id.id,
                    'date': service.date,
                    'approve_id': service.approve_id.id,
                    'total_amount': service.total_amount,
                    'patient_amount': service.patient_amount,
                    'company_amount': service.total_amount - service.patient_amount
                }))
            rec.line_ids = lst

    def action_post(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError(_("لا توجد خدمات مقدمة خلال الفترة المحددة"))
            rec.invoice_id.action_post()
            rec.state = 'post'

    def button_draft(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError(_("لا توجد خدمات مقدمة خلال الفترة المحددة"))
            rec.invoice_id.button_draft()
            rec.state = 'draft'

    def button_cancel(self):
        if self.invoice_id:
            self.invoice_id.button_cancel()
            self.state = 'canceled'
        for line in self.line_ids:
            line.visit_id.claim_id = False

    def create_invoice(self):
        if not self.invoice_id:
            partner_id = self.contract_company.id
            invoice_date = fields.Datetime.today()
            journal_id = self.env.company.contract_journal.id
            invoice_lines = [(5, 0, 0)]
            for line in self.line_ids:
                invoice_line = (0, 0, {
                    'product_id': line.service_id.id,
                    'price_unit': line.company_amount
                })
                invoice_lines.append(invoice_line)
            invoice = self.env["account.move"].create({
                'partner_id': partner_id,
                'invoice_date': invoice_date,
                'journal_id': journal_id,
                'move_type': 'out_invoice',
                'invoice_line_ids': invoice_lines
            })
            self.invoice_id = invoice.id
            self.state = 'invoiced'
            for line in self.line_ids:
                line.visit_id.claim_id = self.id
        else:
            self.invoice_id.action_post()
            self.state = 'post'


class ContractClaimLines(models.Model):
    _name = 'contract.claim.lines'
    _rec_name = 'name'
    _description = 'Contract Claims Lines'

    name = fields.Char()
    claim_id = fields.Many2one('contract.claim', string="المطالبة")
    patient_id = fields.Many2one('res.partner', domain=[('patient_account', '=', 'contract'),
                                                        ('is_patient', '=', True)],
                                 string="المريض", required=True)
    employer = fields.Many2one(related="patient_id.employer")
    service_id = fields.Many2one('product.template', required=True, string="الخدمة")
    date = fields.Date(required=True, string="التاريخ")
    approve_id = fields.Many2one('service.approval', string="الموافقة")
    total_amount = fields.Float(default=0, digits='Product Price', required=True, string="اجمالي القيمة")
    patient_amount = fields.Float(default=0, digits='Product Price', required=True, string="ما تحمله المريض")
    company_amount = fields.Float(default=0, digits='Product Price', required=True, string="ما تتحمله الشركة")
    visit_id = fields.Many2one('clinic.visit')



