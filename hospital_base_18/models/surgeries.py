from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta


class ResSurgeriesClassification(models.Model):
    _name = 'surgeries.classification'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Surgeries classification'

    name = fields.Char(required=True, translate=True, string="الاسم")
    service_id = fields.Many2one('product.template', domain=[('available_in', '=', 'surgeries')], string="الخدمة")
    active = fields.Boolean(default=True, string="الاسم")


class ResSurgeries(models.Model):
    _name = 'res.surgeries'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Res Surgeries'

    name = fields.Char(required=True, translate=True, tracking=True, string="الاسم")
    sequence = fields.Integer(string="الترتيب", default=1, help="Assigns the priority to the Surgery.")
    classification = fields.Many2one('surgeries.classification', required=True, tracking=True, string="التصنيف")
    clinic_id = fields.Many2one('res.clinics', required=True, tracking=True, string="التخصص")
    service_id = fields.Many2one('product.template', required=True, domain=[('available_in', '=', 'surgeries')],
                                 tracking=True, string="الخدمة")
    amount = fields.Float(digits='Product Price', required=True, tracking=True, string="القيمة")
    add_exp = fields.Boolean(default=False, string="اضافة مصاريف")
    is_package = fields.Boolean(default=False, string="شاملة")
    active = fields.Boolean(default=True)
    medicine_lines = fields.One2many('res.surgeries.lines', inverse_name="surgery_id",
                                     domain=[('product_type', '=', 'product')])
    consumable_lines = fields.One2many('res.surgeries.lines', inverse_name="surgery_id",
                                       domain=[('product_type', '=', 'consu')])
    service_lines = fields.One2many('res.surgeries.lines', inverse_name="surgery_id",
                                    domain=[('product_type', '=', 'service')])
    total_medicine_cost = fields.Float(digits='Product Price', compute="compute_total", string="تكلفة الادوية")
    total_consumable_cost = fields.Float(digits='Product Price', compute="compute_total", string="تكلفة المستهلكات")
    total_service_cost = fields.Float(digits='Product Price', compute="compute_total", string="تكلفة الخدمات")
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


class ResSurgeriesLines(models.Model):
    _name = 'res.surgeries.lines'
    _description = 'Surgeries Lines'

    surgery_id = fields.Many2one('res.surgeries', required=True, string="العملية")
    product_id = fields.Many2one('product.template', required=True, string="الصنف")
    product_type = fields.Selection(string="Type", related="product_id.detailed_type", store=True)
    quantity = fields.Float(digits='Product Unit of Measure', default=1, required=True, string="الكمية")
    unit_cost = fields.Float(digits='Product Price', compute="compute_cost", string="التكلفة")
    amount = fields.Float(digits='Product Price', string="السعر")
    total_cost = fields.Float(digits='Product Price', compute="compute_cost", string="اجمالي التكلفة")
    total_amount = fields.Float(digits='Product Price', compute="compute_cost", string="اجمالي السعر")

    @api.depends('product_id', 'quantity', 'amount')
    def compute_cost(self):
        for rec in self:
            rec.unit_cost = 0
            rec.total_cost = rec.unit_cost * rec.quantity
            rec.total_amount = rec.amount * rec.quantity


class Surgeries(models.Model):
    _name = 'surgeries'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Surgeries'

    name = fields.Char(tracking=True, index=True, readonly=True, copy=False, default=lambda self: '/', string="الاسم")
    surgery_id = fields.Many2one('res.surgeries', required=False, tracking=True, string="العملية")
    classification = fields.Many2one(related='surgery_id.classification', required=False, store=True, tracking=True, string="التصنيف")
    doctor_id = fields.Many2one('res.partner', required=True, tracking=True, domain=[('is_doctor', '=', True)], string="الطبيب")
    patient_id = fields.Many2one('res.partner', required=True, tracking=True, domain=[('company_type', '=', 'patient')], string="المريض")
    patient_file = fields.Many2one('patient.file', string="ملف المريض")
    patient_account = fields.Selection(related="patient_file.patient_account",default="cash" , store=True, string="نوع الحساب")
    date_in = fields.Date(related="patient_file.date_in", string="تاريخ الدخول")
    section_id = fields.Many2one('res.sections', string="القسم")
    patient_room = fields.Many2one(related="patient_file.room_id", store=True, string="الغرفة")
    patient_bed = fields.Many2one(related="patient_file.bed_id", store=True, string="السرير")
    employer = fields.Many2one(related="patient_file.employer", store=True, string="الشركة التابع لها")
    contract_company = fields.Many2one(related="patient_file.contract_company", store=True, string="شركة التعاقد")
    relative_partner = fields.Many2one(related="patient_file.relative_partner", store=True, string="المرافق")
    anesthesiologist = fields.Many2one('res.partner', required=False, tracking=True,
                                       domain=[('company_type', '=', 'doctor')], string="طبيب التخدير")
    clinic_id = fields.Many2one('res.clinics', related="doctor_id.clinic", readonly=False, required=False, tracking=True, store=True, string="التخصص")
    date = fields.Datetime(default=fields.Datetime.now, required=False, tracking=True, string="التاريخ")
    room_id = fields.Many2one('surgery.room', required=True, string="غرفة العمليات")
    nurse_id = fields.Many2many('hr.employee', 'res_surgery_nurse_rel', 'surgery_id', 'nurse_id',required=True, string="التمريض")
    worker_id = fields.Many2many('hr.employee', 'res_surgery_worker_rel', 'cid', 'user_id',required=True, string="العامل")
    line_ids = fields.One2many('surgeries.lines', inverse_name="surgery_id",required=True,)
    medicine_lines = fields.One2many('surgeries.lines', inverse_name="surgery_id",
                                     domain=[('hospital_product_type', '=', 'medicament')])
    consumable_lines = fields.One2many('surgeries.lines', inverse_name="surgery_id",
                                       domain=[('hospital_product_type', '=', 'consumable')])
    device_lines = fields.One2many('surgeries.lines', inverse_name="surgery_id",
                                    domain=[('available_in', '=', 'surgeries')])
    state = fields.Selection(selection=[('waiting', 'Waiting'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')], default="waiting", string="الحالة")
    surgery_slot_id = fields.Many2one('surgery.slot', string="موعد العملية", readonly=True, copy=False,
                                      help="The scheduled slot for this surgery")

    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            values['name'] = self.env['ir.sequence'].next_by_code('surgeries')

        # Create the surgery record first
        result = super(Surgeries, self).create(values)

        # If we have room_id and date, create a surgery slot
        if result.room_id and result.date:
            # Calculate the end time
            start_datetime = result.date
            end_datetime = start_datetime + timedelta(hours=2)

            # Create the surgery slot
            slot_vals = {
                'name': result.name,
                'room_id': result.room_id.id,
                'patient_id': result.patient_id.id,
                'start_datetime': start_datetime,
                'end_datetime': end_datetime,
                'doctor_id': result.doctor_id.id,
                'responsible_doctor_id': result.doctor_id.id,
                'state': 'draft',
                'surgery_type': 'elective',
                'notes': f"Surgery created from {result.name}",
                'company_id': self.env.company.id,  # Fixed: using self.env.company
            }

            # Create the slot first without team members
            slot = self.env['surgery.slot'].create(slot_vals)



            # Update the original surgery record with the slot
            result.surgery_slot_id = slot.id

        return result

    def action_confirm(self):
        if not self.anesthesiologist:
            raise ValidationError("يجب تحديد طبيب التخدير")
        if not self.nurse_id:
            raise ValidationError("يجب تحديد التمريض")
        if not self.worker_id:
            raise ValidationError("يجب تحديد العامل")
        if not self.room_id:
            raise ValidationError("يجب تحديد غرفة العمليات")

        # Process patient file lines as in original code
        if self.patient_file:
            lines = []
            section = self.env['res.sections'].search([('type', '=', 'surgeries')], limit=1)
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

        # Confirm the surgery slot if it exists
        if self.surgery_slot_id:
            self.surgery_slot_id.action_confirm()

        self.state = 'confirmed'

    def button_cancel(self):
        self.state = 'cancelled'
        if self.surgery_slot_id:
            self.surgery_slot_id.action_cancel()

    def button_reset(self):
        self.state = 'waiting'


class SurgeriesLines(models.Model):
    _name = 'surgeries.lines'
    _description = 'Surgeries Lines'

    surgery_id = fields.Many2one('surgeries', required=True)
    product_id = fields.Many2one('product.template', required=True, string="الصنف")
    product_type = fields.Selection(string="Type", related="product_id.detailed_type", store=True)
    hospital_product_type = fields.Selection(related='product_id.hospital_product_type', store=True)
    available_in = fields.Selection(related='product_id.available_in', store=True)
    quantity = fields.Float(digits='Product Unit of Measure', default=1, required=True, string="الكمية")
    amount = fields.Float(digits='Product Price', string="السعر")
    total_amount = fields.Float(default=0, digits='Product Price', compute="compute_cost", store=True, string="الاجمالي")
    package_line = fields.Many2one('res.surgeries.lines', compute="compute_package_qty", store=True, string="شاملة")
    package_qty = fields.Float(default=0, digits='Product Price', compute="compute_package_qty", store=True, string="الكمية الشاملة")

    @api.depends('surgery_id', 'product_id')
    def compute_package_qty(self):
        for rec in self:
            rec.package_qty = 0
            rec.package_line = False
            if rec.surgery_id.surgery_id.is_package:
                line = self.env['res.surgeries.lines'].search([('surgery_id', '=', rec.surgery_id.surgery_id.id),
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

