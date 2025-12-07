
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResCatheterizationClassification(models.Model):
    _name = 'catheterization.classification'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'تصنيف الفسطرة'

    name = fields.Char(string="الاسم", required=True, translate=True)
    service_id = fields.Many2one('product.template', string="الخدمة", domain=[('available_in', '=', 'catheterization')])
    active = fields.Boolean(default=True, string="الحالة")


class ResCatheterization(models.Model):
    _name = 'res.catheterization'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'القسطرة'

    name = fields.Char(required=True, string="الاسم", translate=True, tracking=True)
    sequence = fields.Integer('Sequence', default=1, help="Assigns the priority to the Surgery.")
    classification = fields.Many2one('catheterization.classification', required=True, tracking=True, string="التصنيف")
    clinic_id = fields.Many2one('res.clinics', required=True, tracking=True, string="التخصص")
    service_id = fields.Many2one('product.template', string="الخدمة", required=True, domain=[('available_in', '=', 'catheterization')],
                                 tracking=True)
    amount = fields.Float(digits='Product Price', string="القيمة", required=True, tracking=True)
    add_exp = fields.Boolean(default=False, string="مصروفات")
    is_package = fields.Boolean(default=False, string="شاملة")
    active = fields.Boolean(default=True, string="الحالة")
    medicine_lines = fields.One2many('res.catheterization.lines', inverse_name="surgery_id",
                                     domain=[('product_type', '=', 'product')])
    consumable_lines = fields.One2many('res.catheterization.lines', inverse_name="surgery_id",
                                       domain=[('product_type', '=', 'consu')])
    service_lines = fields.One2many('res.catheterization.lines', inverse_name="surgery_id", domain=[('product_type', '=', 'service')])
    total_medicine_cost = fields.Float(digits='Product Price', compute="compute_total", string="اجمالي تكلفة الادوية")
    total_consumable_cost = fields.Float(digits='Product Price', compute="compute_total", string="اجمالي تكلفة المستهلكات")
    total_service_cost = fields.Float(digits='Product Price', compute="compute_total", string="اجمالي الخدمات")
    total_cost = fields.Float(digits='Product Price', compute="compute_total", string="اجمالي التكلفة")
    total_medicine_amount = fields.Float(digits='Product Price', compute="compute_total", string="اجمالي الادوية")
    total_consumable_amount = fields.Float(digits='Product Price', compute="compute_total", string="اجمالي المستهلكات")
    total_service_amount = fields.Float(digits='Product Price', compute="compute_total", string="اجمالي الخدمات")
    total_amount = fields.Float(digits='Product Price', compute="compute_total", string="الاجمالي")

    @api.onchange('classification')
    def onchange_classification(self):
        self.service_id = self.classification.service_id.id

    @api.depends('service_lines', 'medicine_lines', 'consumable_lines')
    def compute_total(self):
        for rec in self:
            rec.total_medicine_cost = sum(rec.medicine_lines.mapped('total_cost'))
            rec.total_consumable_cost = sum(rec.consumable_lines.mapped('total_cost'))
            rec.total_service_cost = sum(rec.service_lines.mapped('total_cost'))
            rec.total_cost = rec.total_service_cost + rec.total_medicine_cost + rec.total_consumable_cost
            rec.total_medicine_amount = sum(rec.medicine_lines.mapped('total_amount'))
            rec.total_consumable_amount = sum(rec.consumable_lines.mapped('total_amount'))
            rec.total_service_amount = sum(rec.service_lines.mapped('total_amount'))
            rec.total_amount = rec.total_medicine_amount + rec.total_consumable_amount + rec.total_service_amount


class ResCatheterizationLines(models.Model):
    _name = 'res.catheterization.lines'
    _description = 'Catheterization Lines'

    surgery_id = fields.Many2one('res.catheterization', required=True)
    product_id = fields.Many2one('product.template', required=True, string="الصنف")
    product_type = fields.Selection(string="Type", related="product_id.detailed_type", store=True)
    quantity = fields.Float(digits='Product Unit of Measure', default=1, required=True, string="الكمية")
    unit_cost = fields.Float(digits='Product Price', compute="compute_cost", string="تكلفة")
    amount = fields.Float(digits='Product Price', string="السعر")
    total_cost = fields.Float(digits='Product Price', compute="compute_cost", string="اجمالي التكلفة")
    total_amount = fields.Float(digits='Product Price', compute="compute_cost", string="اجمالي السعر")

    @api.depends('product_id', 'quantity', 'amount')
    def compute_cost(self):
        for rec in self:
            rec.unit_cost = 0
            rec.total_cost = rec.unit_cost * rec.quantity
            rec.total_amount = rec.amount * rec.quantity


class Catheterization(models.Model):
    _name = 'catheterization'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Catheterization'

    name = fields.Char(tracking=True, index=True, readonly=True, copy=False, default=lambda self: '/', string="الاسم")
    surgery_id = fields.Many2one('res.surgeries', required=False, tracking=True, string="العملية")
    classification = fields.Many2one(related='surgery_id.classification', required=False, store=True, tracking=True, string="التصنيف")
    doctor_id = fields.Many2one('res.partner', required=True, tracking=True, domain=[('is_doctor', '=', True)], string="الطبيب")
    patient_id = fields.Many2one('res.partner', required=True, tracking=True, domain=[('company_type', '=', 'patient')], string="المريض")
    patient_file = fields.Many2one('patient.file', string="ملف المريض")
    patient_account = fields.Selection(related="patient_file.patient_account", default="cash" ,store=True, string="نوع الحساب")
    date_in = fields.Date(related="patient_file.date_in", string="تاريخ الدخول")
    patient_room = fields.Many2one(related="patient_file.room_id", store=True, string="الغرفة")
    patient_bed = fields.Many2one(related="patient_file.bed_id", store=True, string="السرير")
    employer = fields.Many2one(related="patient_file.employer", store=True, string="الشركة التابع لها")
    contract_company = fields.Many2one(related="patient_file.contract_company", store=True, string="شركة التعاقد")
    relative_partner = fields.Many2one(related="patient_file.relative_partner", store=True, string="المرافق")
    anesthesiologist = fields.Many2one('res.partner', required=False, tracking=True,
                                       domain=[('company_type', '=', 'doctor')], string="طبيب التخدير")
    clinic_id = fields.Many2one('res.clinics', related="doctor_id.clinic", readonly=False, required=False, tracking=True, store=True, string="التخصص")
    date = fields.Datetime(default=fields.Datetime.now, required=False, tracking=True, string="التاريخ")
    room_id = fields.Many2one('res.rooms', domain=[('room_type', '=', 'surgeries')], string="غرفة العمليات")
    nurse_id = fields.Many2many('hr.employee', 'res_catheterization_nurse_rel', 'surgery_id', 'nurse_id', string="التمريض")
    worker_id = fields.Many2many('hr.employee', 'res_catheterization_worker_rel', 'cid', 'user_id', string="العامل")
    line_ids = fields.One2many('surgeries.lines', inverse_name="surgery_id")
    medicine_lines = fields.One2many('catheterization.lines', inverse_name="surgery_id",
                                     domain=[('hospital_product_type', '=', 'medicament')])
    consumable_lines = fields.One2many('catheterization.lines', inverse_name="surgery_id",
                                       domain=[('hospital_product_type', '=', 'consumable')])
    device_lines = fields.One2many('catheterization.lines', inverse_name="surgery_id",
                                    domain=[('available_in', '=', 'catheterization')])
    state = fields.Selection(selection=[('waiting', 'Waiting'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')], default="waiting", string="الحالة")

    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            values['name'] = self.env['ir.sequence'].next_by_code('catheterization')
            result = super(Catheterization, self).create(values)
            return result

    def action_confirm(self):
        if not self.anesthesiologist:
            raise ValidationError("يجب تحديد طبيب التخدير")
        if not self.nurse_id:
            raise ValidationError("يجب تحديد فريق التمريض")
        if not self.worker_id:
            raise ValidationError("يجب تحديد العامل")
        if not self.room_id:
            raise ValidationError("يجب تحديد غرفة العمليات")
        if self.patient_file:
            lines = []
            section = self.env['res.sections'].search([('type', '=', 'catheterization')], limit=1)
            for line in self.line_ids:
                val = {
                    'patient_file_id': self.patient_file.id,
                    'product_id': line.product_id.id,
                    'date': fields.Date.context_today(self),
                    'quantity': line.quantity,
                    'amount': line.amount,
                    'package_line': line.package_line,
                    'package_qty': line.package_qty,
                    'section_id': section.id
                }
                lines.append(val)
            self.env['patient.file.line'].create(lines)
        self.state = 'confirmed'

    def button_cancel(self):
        self.state = 'cancelled'

    def button_reset(self):
        self.state = 'waiting'


class CatheterizationLines(models.Model):
    _name = 'catheterization.lines'
    _description = 'Catheterization Lines'

    surgery_id = fields.Many2one('catheterization', required=True, string="العملية")
    product_id = fields.Many2one('product.template', required=True, string="الصنف")
    product_type = fields.Selection(string="Type", related="product_id.detailed_type", store=True)
    hospital_product_type = fields.Selection(related='product_id.hospital_product_type', store=True)
    available_in = fields.Selection(related='product_id.available_in', store=True)
    quantity = fields.Float(digits='Product Unit of Measure', default=1, required=True, string="الكمية")
    amount = fields.Float(digits='Product Price', string="السعر")
    total_amount = fields.Float(default=0, digits='Product Price', compute="compute_cost", store=True, string="الاجمالي")
    package_line = fields.Many2one('res.surgeries.lines', compute="compute_package_qty", store=True)
    package_qty = fields.Float(default=0, digits='Product Price', compute="compute_package_qty", store=True)

    @api.depends('surgery_id', 'product_id')
    def compute_package_qty(self):
        for rec in self:
            rec.package_qty = 0
            rec.package_line = False
            if rec.surgery_id.surgery_id.is_package:
                line = self.env['res.catheterization.lines'].search([('surgery_id', '=', rec.surgery_id.surgery_id.id),
                                                              ('product_id', '=', rec.product_id.id)], limit=1)
                if line:
                    rec.package_line = line.id
                    rec.package_qty = line.quantity

    @api.depends('quantity', 'amount')
    def compute_cost(self):
        for rec in self:
            rec.total_amount = 0
            if rec.amount and rec.quantity:
                rec.total_amount = rec.amount * rec.quantity

