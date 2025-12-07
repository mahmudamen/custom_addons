
from odoo import models, fields, api, _


class DoctorDegrees(models.Model):
    _name = 'doctor.degrees'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Doctor Degrees'

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)



class DoctorServices(models.Model):
    _name = 'doctor.services'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Doctor Service Comm'

    name = fields.Char(compute='compute_name', store=True, string="الاسم")
    doctor_id = fields.Many2one('res.partner', required=True, domain=[('is_doctor', '=', True)], string="الطبيب")
    service_id = fields.Many2one('product.template', required=True, domain=[('detailed_type', '=', 'service'),
                                                                            ('hospital_product_type', '=', 'medical_service')], string="الخدمة")
    patient_account = fields.Selection([('cash', 'Cash'),
                                        ('contract', 'Contract')], default='cash', required=True, string="نوع الحساب")
    customer_id = fields.Many2many('res.partner', string='الشركات', required=False,
                                   domain=[('is_insurance', '=', True)])
    amount = fields.Float(default=0, digits='Product Price', required=True, string="القيمة")
    doctor_amount = fields.Float(default=0, digits='Product Price', required=True, string="نصيب الطبيب")
    exp_amount = fields.Float(default=0, digits='Product Price', required=True, string="مصروفات")
    tax_amount = fields.Float(default=0, digits='Product Price', required=True, string="ضريبة")
    total_amount = fields.Float(default=0, digits='Product Price', compute='compute_total_amount', store=True, string="الاجمالي")
    available_in = fields.Selection([
        ('surgeries', 'عمليات'),
        ('clinic', 'عيادات خارجية'),
        ('inpatient', 'الداخلي'),
        ('icu', 'عناية مركزة'),
        ('laboratory', 'المعمل'),
        ('catheterization', 'القسطرة'),
        ('radiology', 'الاشعة'),
        ('nursing', 'تمريض')
    ], string="متاح في", tracking=True)
    hospital_product_type = fields.Selection([
        ('medicament', 'أدوية'),
        ('consumable', 'مستهلكات'),
        ('medical_service', 'خدمة طبية'),
        ('os', 'خدمات أخري'),
        ('accommodation', 'إقامة')
    ], string="نوع الصنف", tracking=True)

    @api.depends('exp_amount', 'amount', 'tax_amount')
    def compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.exp_amount + rec.amount + rec.tax_amount

    @api.depends('service_id')
    def compute_name(self):
        for rec in self:
            if rec.service_id:
                rec.name = rec.service_id.name
            else:
                rec.name = ''


class DoctorPostVisits(models.Model):
    _name = 'doctor.post.visits'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Doctor Post Services Amount'

    name = fields.Char(tracking=True, index=True, readonly=True, copy=False, default=lambda self: '/', string="الاسم")
    doctor_id = fields.Many2one('res.partner', domain=('is_doctor', '=', True), string="الطبيب")
    date = fields.Date(default=lambda self: fields.Date.today(), string="التاريخ")
    from_rec = fields.Char(copy=False, string="من ايصال")
    to_rec = fields.Char(copy=False, string="الي ايصال")
    total_amount = fields.Float(default=0, digits='Product Price', string="الاجمالي")
    due_move = fields.Many2one('account.move', string="قيد الاستحقاق")
    pay_move = fields.Many2one('account.move', string="قيد المدفوعات")
    note = fields.Char(string="ملاحظات")
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('post', 'Posted'), ('paid', 'Paid')],
        default="draft",
        required=False, string="الحالة")
    doctor_readonly = fields.Boolean(default=False)

    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            values['name'] = self.env['ir.sequence'].next_by_code('dva')
            result = super(DoctorPostVisits, self).create(values)
            return result

    def action_post(self):
        self.ensure_one()
        move_lines = [(5, 0, 0)]
        ids = self.env.context.get('visit_post_ids')
        doctor_acc = self.env.company.doctor_due_account.id
        debit_line = (0, 0, {
            "account_id": doctor_acc,
            "partner_id": self.doctor_id.id,
            "debit": self.total_amount
        })
        credit_line = (0, 0, {
            "account_id": self.doctor_id.property_account_payable_id.id,
            "partner_id": self.doctor_id.id,
            "credit": self.total_amount
        })
        move_lines.append(debit_line)
        move_lines.append(credit_line)
        due_entry = {
            'date': fields.Date.today(),
            'journal_id': self.env.company.main_cash_journal.id,
            'ref': _('استحقاق الطبيب %s') % self.name,
            'line_ids': move_lines
        }
        entry_due = self.env["account.move"].create(due_entry)
        entry_due.action_post()
        self.due_move = entry_due.id
        self.state = 'post'
        visits = self.env['clinic.visit'].browse(ids)
        visits.doctor_posted = True

    def action_pay(self):
        self.ensure_one()
        move_lines = [(5, 0, 0)]
        ids = self.env.context.get('visit_post_ids')
        cash_acc = self.env.company.main_cash.id
        credit_line = (0, 0, {
            "account_id": cash_acc,
            "partner_id": self.doctor_id.id,
            "debit": self.total_amount
        })
        debit_line = (0, 0, {
            "account_id": self.doctor_id.property_account_payable_id.id,
            "partner_id": self.doctor_id.id,
            "credit": self.total_amount
        })
        move_lines.append(debit_line)
        move_lines.append(credit_line)
        pay_entry = {
            'date': fields.Date.today(),
            'journal_id': self.env.company.main_cash_journal.id,
            'ref': _('سداد الطبيب %s') % self.name,
            'line_ids': move_lines
        }
        entry_pay = self.env["account.move"].create(pay_entry)
        entry_pay.action_post()
        self.pay_move = entry_pay.id
        self.state = 'paid'
        visits = self.env['clinic.visit'].browse(ids)
        visits.doctor_paid = True


