
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import base64
import io
import xlsxwriter
from datetime import datetime

class PatientFile(models.Model):
    _name = 'patient.file'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = "date_in desc"
    _description = 'patient file'

    name = fields.Char(string="الاسم")
    old_pat_file = fields.Char()
    currency_id = fields.Many2one('res.currency',
                                  default=lambda self: self.env.company.currency_id,
                                  string='Currency')
    patient_id = fields.Many2one('res.partner', domain=[('is_patient', '=', True)],required=True,tracking=1, string="المريض")
    patient_account = fields.Selection(related="patient_id.patient_account",default="cash" ,tracking=1, store=True, string="نوع الحساب")
    employer = fields.Many2one(related="patient_id.employer", store=True,tracking=1, string="الشركة التابع لها")
    contract_company = fields.Many2one(related="patient_id.contract_company", store=True, string="شركة التعاقد")
    relative_partner = fields.Many2one('res.partner', string="مرافق المريض في الغرفة")
    relative_partner_mobile = fields.Char(string="تليفون 1 المرافق ", store=True, tracking=1, required=False)
    relative_partner_phone = fields.Char(string="تليفون 2 المرافق", store=True, tracking=1, required=False)
    relative_partner_nat_id = fields.Char(string='الرقم القومي للمرافق', store=True, tracking=1, required=False,readonly=False)
    doctor_id = fields.Many2one('res.partner', domain=[('is_doctor', '=', True)], string="الطبيب", required=False,tracking=1)
    doctor_drags_id = fields.Many2one('res.partner', domain=[('is_doctor', '=', True)], string="طبيب التخدير", required=False,tracking=1)
    doctor_id_account = fields.Many2one('res.partner', domain=[('is_doctor', '=', True)], string="علي حساب", required=False,tracking=1)
    doctor_account = fields.Boolean(default=True, string="علي حساب طبيب اخر", tracking=1)
    patient_age = fields.Integer(related="patient_id.age", store=True, tracking=1, readonly=False, string="العمر")
    patient_street = fields.Char(related="patient_id.street", store=True, tracking=1, readonly=False, string="العنوان")
    patient_nat_id = fields.Char(related="patient_id.nat_id", store=True, tracking=1, readonly=False, string="الرقم القومي")
    patient_phone = fields.Char(related="patient_id.phone", store=True, tracking=1, readonly=False, string="تليفون 1")
    patient_mobile = fields.Char(related="patient_id.mobile", store=True, tracking=1, readonly=False, string="تليفون 2")
    attachment = fields.Binary(string='الروشتة / البطاقة')
    work_phone = fields.Char(string="تليفون العمل")
    avatar_128 = fields.Image("Avatar 128", related='image', compute_sudo=True)
    image = fields.Image(string="Image", max_width=1920, max_height=1920,
                         help="This field holds the image used for "
                              "this provider, limited to 1920x1920px")
    image_medium = fields.Binary(
        "Medium-sized image", attachment=True,
        help="Medium-sized image of this provider. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved. "
             "Use this field in form views or some kanban views.")
    image_small = fields.Binary(
        "Small-sized image", attachment=True,
        help="Small-sized image of this provider. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")
    doctor_discount = fields.Float(default=0, digits='Product Price', compute="compute_doctor_discount", store=True, string="خصم الطبيب")
    surgery_tax = fields.Float(default=0, digits='Product Price', store=True, string="المصاريف الادارية")
    paid_amount = fields.Float(default=0, digits='Product Price', compute="compute_paid_amount", string="المدفوع")
    patient_due = fields.Float(default=0, digits='Product Price', compute="compute_patient_due", store=True, string="مستحق علي المريض")
    date_in = fields.Date(default=lambda self: fields.Date.today(), readonly=False,store=True,string="تاريخ الدخول" ,required=False,tracking=1,)
    date_out = fields.Date(string="تاريخ الخروج", required=False,tracking=1,default=lambda self: fields.Date.today(), readonly=False,store=True)
    room_id = fields.Many2one('res.rooms', string="الغرفة", required=False,tracking=1,)
    room_surgery_id = fields.Many2one('surgery.room', string="غرفة العمليات", required=False, tracking=1, )
    bed_id = fields.Many2one('res.beds', string="السرير", required=False,tracking=1,)
    diagnosis = fields.Text(string="التشخيص" ,required=False,tracking=1)
    note = fields.Text(string="العملية")
    remark = fields.Text(string="ملاحظات")
    line_ids = fields.One2many('patient.file.line', inverse_name="patient_file_id")
    medicament_line_ids = fields.One2many('patient.file.line', inverse_name="patient_file_id",
                                          domain=[('hospital_product_type', '=', 'medicament')])
    consumable_line_ids = fields.One2many('patient.file.line', inverse_name="patient_file_id",
                                          domain=[('hospital_product_type', '=', 'consumable')])
    services_line_ids = fields.One2many('patient.file.line', inverse_name="patient_file_id",
                                        domain=[('hospital_product_type', '=', 'medical_service')])
    laboratory_line_ids = fields.One2many('patient.file.line', inverse_name="patient_file_id",
                                          domain=[('available_in', '=', 'laboratory')])
    radiology_line_ids = fields.One2many('patient.file.line', inverse_name="patient_file_id",
                                         domain=[('available_in', '=', 'radiology')])
    total = fields.Float(default=0, digits='Product Price', compute="compute_total_amount", store=True,
                         compute_sudo=True, string="الاجمالي")
    state = fields.Selection(selection=[('open', 'Open'),
                                        ('closed', 'Closed')], default="open", string="الحالة")
    type = fields.Selection(selection=[('inpatient', 'In-Patient'),
                                       ('icu', 'ICU')], default="inpatient", string="داخلي/عناية")
    move_id = fields.Many2one('account.move', string="القيد المحاسبي")
    total_medicament = fields.Float(default=0, digits='Product Price',currency_field='currency_id', compute="compute_total_medicament", store=True,
                                    compute_sudo=True, string="اجمالي الادوية")
    total_consumable = fields.Float(default=0, digits='Product Price', compute="compute_total_consumable", store=True,
                                    compute_sudo=True, string="اجمالي المستهلكات")
    total_services = fields.Float(default=0, digits='Product Price', compute="compute_total_services", store=True, compute_sudo=True, string="اجمالي الخدمات")
    total_laboratory = fields.Float(default=0, digits='Product Price', compute="compute_total_laboratory", store=True, compute_sudo=True, string="اجمالي التحاليل")
    total_radiology = fields.Float(default=0, digits='Product Price', compute="compute_total_radiology", store=True, compute_sudo=True, string="اجمالي الاشعة")
    package_discount = fields.Float(default=0, digits='Product Price', compute="compute_package_discount", store=True, compute_sudo=True, string="خصم الشاملة")
    surgery_slot_id = fields.Many2one('surgery.slot', string="موعد العملية", readonly=True, copy=False,
                                      help="The scheduled slot for this surgery")
    section_id = fields.Many2one('res.sections', string="القسم")
    # Add these fields to PatientFile model
    discharge_condition = fields.Selection([
        ('improved', 'تحسن'),
        ('cured', 'شفي'),
        ('stable', 'مستقر'),
        ('transferred', 'محول'),
        ('deceased', 'متوفي'),
        ('against_advice', 'خروج ضد المشورة الطبية')
    ], string="حالة المريض عند الخروج")

    follow_up_instructions = fields.Text(string="تعليمات المتابعة", help="Follow-up care instructions")
    medications_on_discharge = fields.Text(string="الأدوية عند الخروج", help="Medications prescribed at discharge")
    next_appointment_date = fields.Date(string="موعد المتابعة التالي")
    discharge_doctor = fields.Many2one('res.partner', domain=[('is_doctor', '=', True)], string="طبيب الخروج")
    discharge_notes = fields.Text(string="ملاحظات الخروج")
    discharge_summary = fields.Text(string="التوصيات الطبية",
                                    help="Summary of patient's treatment and condition at discharge")
    length_of_stay = fields.Integer(string="مدة الإقامة (أيام)", compute="_compute_length_of_stay", store=True)
    # Add these fields for patient history
    previous_visits_ids = fields.One2many(
        'clinic.visit',
        compute='_compute_previous_visits',
        string="Previous Clinic Visits"
    )
    previous_visits_count = fields.Integer(
        compute='_compute_previous_visits',
        string="Previous Visits Count"
    )

    previous_inpatient_ids = fields.One2many(
        'patient.file',
        compute='_compute_previous_inpatient',
        string="Previous Inpatient Files"
    )
    previous_inpatient_count = fields.Integer(
        compute='_compute_previous_inpatient',
        string="Previous Inpatient Count"
    )

    @api.depends('medicament_line_ids.total')
    def compute_total_medicament(self):
        for record in self:
            record.total_medicament = sum(record.medicament_line_ids.mapped('total'))

    @api.depends('consumable_line_ids.total')
    def compute_total_consumable(self):
        for record in self:
            record.total_consumable = sum(record.consumable_line_ids.mapped('total'))

    @api.depends('services_line_ids.total')
    def compute_total_services(self):
        for record in self:
            record.total_services = sum(record.services_line_ids.mapped('total'))

    @api.depends('laboratory_line_ids.total')
    def compute_total_laboratory(self):
        for record in self:
            record.total_laboratory = sum(record.laboratory_line_ids.mapped('total'))

    @api.depends('radiology_line_ids.total')
    def compute_total_radiology(self):
        for record in self:
            record.total_radiology = sum(record.radiology_line_ids.mapped('total'))

    @api.depends('patient_id', 'date_in')
    def _compute_previous_visits(self):
        for record in self:
            if record.patient_id and record.date_in:
                # Get previous clinic visits for the same patient
                domain = [
                    ('patient_id', '=', record.patient_id.id),
                    ('date', '<', record.date_in),
                ]
                previous_visits = self.env['clinic.visit'].search(
                    domain,
                    order='date desc, id desc',
                    limit=50  # Limit to last 50 visits for performance
                )
                record.previous_visits_ids = previous_visits
                record.previous_visits_count = len(previous_visits)
            else:
                record.previous_visits_ids = False
                record.previous_visits_count = 0
    @api.depends('patient_id', 'date_in')
    def _compute_previous_inpatient(self):
        for record in self:
            if record.patient_id and record.date_in:
                # Get previous inpatient files for the same patient, excluding current file
                domain = [
                    ('patient_id', '=', record.patient_id.id),
                    ('date_in', '<', record.date_in),
                ]
                # Only add id filter if record exists (has been saved)
                if record.id and not isinstance(record.id, models.NewId):
                    domain.append(('id', '!=', record.id))

                previous_inpatient = self.env['patient.file'].search(
                    domain,
                    order='date_in desc, id desc',
                    limit=50  # Limit to last 50 files for performance
                )
                record.previous_inpatient_ids = previous_inpatient
                record.previous_inpatient_count = len(previous_inpatient)
            else:
                record.previous_inpatient_ids = False
                record.previous_inpatient_count = 0
    def action_view_visit_details(self):
        """Action to view clinic visit details in readonly mode"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Clinic Visit Details - {self.name}',
            'res_model': 'clinic.visit',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'create': False,
                'edit': False,
                'delete': False,
                'duplicate': False,
                'from_history': True,
            },
            'flags': {
                'mode': 'readonly',
            }
        }
    def action_view_inpatient_details(self):
        """Action to view inpatient file details in readonly mode"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Inpatient File Details - {self.name}',
            'res_model': 'patient.file',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'create': False,
                'edit': False,
                'delete': False,
                'duplicate': False,
                'from_history': True,
            },
            'flags': {
                'mode': 'readonly',
            }
        }
    @api.depends('date_in', 'date_out')
    def _compute_length_of_stay(self):
        for record in self:
            if record.date_in and record.date_out:
                delta = record.date_out - record.date_in
                record.length_of_stay = delta.days + 1
            else:
                record.length_of_stay = 0
    def action_open_exit_wizard(self):
        """Open the patient exit wizard"""
        self.ensure_one()

        if self.state == 'closed':
            raise ValidationError("الملف مغلق بالفعل")

        return {
            'name': 'تقرير خروج المريض',
            'type': 'ir.actions.act_window',
            'res_model': 'patient.exit.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id}
        }
    def action_print_exit_report_only(self):
        """Print exit report without closing file"""
        self.ensure_one()
        return self.env.ref('hospital_base.action_report_patient_exit').report_action(self)
    # Add this method to your PatientFile model to support the dashboard
    @api.model
    def get_dashboard_data(self):
        total_patients = self.search_count([])
        open_files = self.search_count([('state', '=', 'open')])
        closed_files = self.search_count([('state', '=', 'closed')])
        inpatient_count = self.search_count([('type', '=', 'inpatient')])
        icu_count = self.search_count([('type', '=', 'icu')])

        # Get financial data
        total_revenue = sum(self.search([]).mapped('total'))
        outstanding_amount = sum(self.search([]).mapped('patient_due'))

        return {
            'total_patients': total_patients,
            'open_files': open_files,
            'closed_files': closed_files,
            'inpatient_count': inpatient_count,
            'icu_count': icu_count,
            'total_revenue': total_revenue,
            'outstanding_amount': outstanding_amount
        }
    def view_surgery_slot(self):
        """Open the surgery slot form view"""
        self.ensure_one()
        if not self.surgery_slot_id:
            raise UserError(_("No surgery slot has been created yet."))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'surgery.slot',
            'res_id': self.surgery_slot_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    @api.onchange('doctor_id','doctor_account')
    def onchange_doctors_id(self):
        self.ensure_one()
        if self.doctor_id:
            self.write({'doctor_id_account': self.doctor_id})
        else:
            self.write({'doctor_id_account': self.doctor_id_account})
    def write(self, values):
        result = super(PatientFile, self).write(values)
        for record in self:
            # If changing bed or closing the patient file
            old_bed_id = record.bed_id.id if record.bed_id else False
            new_bed_id = values.get('bed_id', old_bed_id)
            old_state = record.state
            new_state = values.get('state', old_state)



            # If patient is discharged or bed is changed
            if old_bed_id and (new_state == 'closed' or old_bed_id != new_bed_id):
                old_bed = self.env['res.beds'].browse(old_bed_id)
                old_bed.mark_as_available()

            # If new bed is assigned or file is reopened
            if new_bed_id and new_state == 'open' and (old_bed_id != new_bed_id or old_state != 'open'):
                new_bed = self.env['res.beds'].browse(new_bed_id)
                new_bed.state = 'full'
                new_bed.patient_id = record.patient_id.id
                new_bed.patient_file_id = record.id

        return result
    def action_download_image(self):
        self.ensure_one()
        if not self.image:
            return False

        # Determine filename - you may want to customize this
        filename = f"{self._name.replace('.', '_')}_{self.id}_image.png"

        # Return the image as a downloadable attachment
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/image?model={self._name}&id={self.id}&field=image&filename={filename}',
            'target': 'self',
        }
    def approve_request(self):
        self.ensure_one()
        if self.state == 'closed':
            raise ValidationError("لا يمكن انشاء موافقة لملف تم اغلاقه")
        section = self.env['res.sections'].search([('type', '=', 'inpatient')], limit=1)
        return {
            'type': 'ir.actions.act_window',
            'name': _("Request Approve"),
            'res_model': 'service.approval',
            'view_mode': 'form',
            'views': [[self.env.ref('hospital_base.inpatient_service_approval_form').id, "form"]],
            'target': 'new',
            'context': {
                'default_patient_file': self.id,
                'default_doctor_id': self.doctor_id_account.id,
                'default_patient_id': self.patient_id.id,
                'default_section_id': section.id
            }
        }
    def patient_approves(self):
        self.ensure_one()
        lines = self.env['service.approval'].search([('patient_file', '=', self.id)])
        if lines:
            return {
                'type': 'ir.actions.act_window',
                'name': _("Patient Approves"),
                'res_model': 'service.approval',
                'view_mode': 'list',
                'domain': [('id', 'in', lines.ids)],
                'views': [[self.env.ref('hospital_base.inpatient_service_approval_tree').id, "list"]],
                'target': 'target',
                'context': {'create': False, 'delete': False, 'duplicate': False, 'edit': False}
            }
        else:
            raise ValidationError("لا توجد موافقات خاصة بهذا الملف")
    @api.depends('doctor_id', 'patient_id')
    def compute_package_discount(self):
        for rec in self:
            rec.package_discount = 0
            surgery = self.env['surgeries'].search([('patient_file', '=', rec.id)], limit=1)
            if surgery.surgery_id.is_package:
                rec.package_discount = surgery.surgery_id.amount
    @api.depends('medicament_line_ids')
    def compute_total_medicament(self):
        for rec in self:
            rec.total_medicament = 0
            if rec.medicament_line_ids:
                total = sum(rec.medicament_line_ids.mapped('total'))
                rec.total_medicament = total
    @api.depends('consumable_line_ids')
    def compute_total_consumable(self):
        for rec in self:
            rec.total_consumable = 0
            if rec.consumable_line_ids:
                total = sum(rec.consumable_line_ids.mapped('total'))
                rec.total_consumable = total
    @api.depends('services_line_ids')
    def compute_total_services(self):
        for rec in self:
            rec.total_services = 0
            if rec.services_line_ids:
                total = sum(rec.services_line_ids.mapped('total'))
                rec.total_services = total
    @api.depends('laboratory_line_ids')
    def compute_total_laboratory(self):
        for rec in self:
            rec.total_laboratory = 0
            if rec.laboratory_line_ids:
                total = sum(rec.laboratory_line_ids.mapped('total'))
                rec.total_laboratory = total
    @api.depends('radiology_line_ids')
    def compute_total_radiology(self):
        for rec in self:
            rec.total_radiology = 0
            if rec.radiology_line_ids:
                total = sum(rec.radiology_line_ids.mapped('total'))
                rec.total_radiology = total
    @api.depends('doctor_id', 'line_ids', 'line_ids.total', 'services_line_ids', 'laboratory_line_ids', 'radiology_line_ids', 'package_discount')
    def compute_doctor_discount(self):
        for rec in self:
            total = sum(
                rec.line_ids.filtered(lambda w: w.hospital_product_type not in ('medicament', 'consumable')).mapped(
                    'total'))
            rec.doctor_discount = round((rec.doctor_id_account.inpatient_discount * total) / 100, 2) if rec.package_discount == 0 else 0
    @api.depends('total', 'doctor_discount', 'surgery_tax', 'paid_amount')
    def compute_patient_due(self):
        for rec in self:
            rec.patient_due = rec.total + rec.surgery_tax - rec.doctor_discount - rec.paid_amount
    @api.depends('doctor_id')
    def compute_surgery_tax(self):
        ir_config = self.env["ir.config_parameter"].sudo()
        for rec in self:
            rec.surgery_tax = 0
            if rec.doctor_id_account.surgery_tax:
                rec.surgery_tax = ir_config.get_param("hospital.surgery_tax")
    def compute_paid_amount(self):
        for rec in self:
            rec.paid_amount = 0
            get_payments = self.env['clinic.visit'].search([('patient_file', '=', rec.id)])
            if get_payments:
                rec.paid_amount = sum(get_payments.mapped('patient_amount'))
                rec.compute_patient_due()
    def patient_payment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Payment"),
            'res_model': 'clinic.visit',
            'view_mode': 'form',
            'views': [[self.env.ref('hospital_base.inpatient_payment_form').id, "form"]],
            'target': 'new',
            'context': {
                'default_patient_file': self.id,
                'default_doctor_id': self.doctor_id_account.id,
                'default_patient_id': self.patient_id.id
            }
        }
    def patient_payments(self):
        self.ensure_one()
        lines = self.env['clinic.visit'].search([('patient_file', '=', self.id)])
        if lines:
            return {
                'type': 'ir.actions.act_window',
                'name': _("Patient Payments"),
                'res_model': 'clinic.visit',
                'view_mode': 'list',
                'domain': [('id', 'in', lines.ids)],
                'views': [[self.env.ref('hospital_base.inpatient_payment_tree').id, "list"]],
                'target': 'target',
                'context': {'create': False, 'delete': False, 'duplicate': False, 'edit': False}
            }
        else:
            raise ValidationError("No Payments For this Patient")
    def patient_to_surgeries(self):
        self.ensure_one()
        if not self.doctor_id_account or not self.patient_id:
            raise ValidationError("Please Check your data")
        surgery = self.env['surgeries'].search(
            [('patient_id', '=', self.patient_id.id), ('patient_file', '=', self.id)], limit=1)
        if not surgery:
            surgery = self.env['surgeries'].create({
                "doctor_id": self.doctor_id_account.id,
                "patient_id": self.patient_id.id,
                "patient_file": self.id,
                "clinic_id": self.doctor_id_account.clinic.id,
                "date": fields.Date.today()
            })
        return {
            'type': 'ir.actions.act_window',
            'name': _("Surgery"),
            'res_model': 'surgeries',
            'view_mode': 'form',
            'res_id': surgery.id,
            'views': [[self.env.ref('hospital_base.surgeries_form').id, "form"]],
            'target': 'target',
            'context': {'create': False, 'delete': False, 'duplicate': False}
        }

    @api.depends('line_ids', 'line_ids.total', 'package_discount')
    def compute_total_amount(self):
        for rec in self:
            rec.total = 0
            if rec.line_ids:
                rec.total = sum(rec.line_ids.mapped('total')) if rec.package_discount == 0 else rec.package_discount
    def action_open(self):
        self.state = 'open'
    def action_re_open(self):
        self.state = 'open'
        if self.bed_id and self.bed_id.state != 'available':
            raise ValidationError(_("The bed assigned to this patient is no longer available. Please choose another bed."))
        if self.bed_id:
            self.bed_id.state = 'full'
            self.bed_id.patient_id = self.patient_id.id
            self.bed_id.patient_file_id = self.id
    def create_account_move(self):
        self.ensure_one()
        move_lines = [(5, 0, 0)]
        total = 0
        moves = self.line_ids.read_group([], fields=['account_id', 'total'], groupby=['account_id'], lazy=False)
        for move in moves:
            if move["account_id"]:
                total += move["total"]
                val = (0, 0, {
                    "account_id": move["account_id"][0],
                    "name": _('قيد فاتورة داخلي %s') % self.name,
                    "debit": 0,
                    "credit": move["total"]
                })
                move_lines.append(val)
        if self.surgery_tax != 0:
            total += self.surgery_tax
            val = (0, 0, {
                "account_id": self.env.company.surgery_tax_account.id,
                "name": _('المصاريف الادارية %s') % self.name,
                "debit": 0,
                "credit": self.surgery_tax
            })
            move_lines.append(val)
        if self.doctor_discount != 0:
            total -= self.doctor_discount
            val = (0, 0, {
                "account_id": self.env.company.doctor_discount_account.id,
                "name": _('خصم الطبيب %s') % self.name,
                "debit": self.doctor_discount,
                "credit": 0
            })
            move_lines.append(val)
        receivable_account = self.patient_id.property_account_receivable_id.id if self.patient_account == 'cash' else self.contract_company.property_account_receivable_id.id
        if receivable_account:
            if not self.doctor_account:
                receivable_val = (0, 0, {
                    "account_id": receivable_account,
                    "name": _('ملف %s') % self.name,
                    "partner_id": self.partner_id.id if self.patient_account == 'cash' else self.contract_company.id,
                    "debit": total,
                    "credit": 0
                })
                move_lines.append(receivable_val)
            else:
                receivable_val = (0, 0, {
                    "account_id": self.doctor_id_account.property_account_receivable_id.id if self.doctor_id_account else self.patient_id.property_account_receivable_id.id,
                    "partner_id": self.doctor_id_account.id if self.doctor_id_account else self.patient_id.id,
                    "name": _('ملف %s') % self.name,
                    "debit": total,
                    "credit": 0
                })
                move_lines.append(receivable_val)
        due_entry = {
            'date': fields.Date.today(),
            'journal_id': self.env.company.inpatient_journal.id,
            'ref': _('قيد ملف داخلي %s') % self.name,
            'line_ids': move_lines
        }
        entry_due = self.env["account.move"].create(due_entry)
        self.move_id = entry_due.id
    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            values['name'] = self.env['ir.sequence'].next_by_code('inpat')

        result = super(PatientFile, self).create(values)

        # If patient file is created with bed and is open
        if result.bed_id and result.state == 'open':
            result.bed_id.state = 'full'
            result.bed_id.patient_id = result.patient_id.id
            result.bed_id.patient_file_id = result.id

        return result

    attachment_ids = fields.Many2many(
        'ir.attachment',
        'patient_file_attachment_rel',
        'patient_file',
        'attachment_id',
        string='Attachments'
    )

    # Optional: You can add a compute field to show the number of attachments
    attachment_count = fields.Integer(
        string='Attachment Count',
        compute='_compute_attachment_count'
    )

    def action_view_attachments(self):
        self.ensure_one()
        return {
            'name': 'Attachments',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.attachment_ids.ids)],
            'context': {'default_res_model': self._name, 'default_res_id': self.id},
        }
    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = len(record.attachment_ids)

    # Update bed_id with onchange to check room capacity
    @api.onchange('room_id')
    def _onchange_room_id(self):
        self.bed_id = False
        if self.room_id:
            return {'domain': {'bed_id': [('room_id', '=', self.room_id.id), ('state', '=', 'available')]}}
        else:
            return False

    @api.onchange('bed_id')
    def _onchange_bed_id(self):
        if self.bed_id and not self.room_id:
            self.room_id = self.bed_id.room_id
        else:
            return False


    def action_export_excel(self):
        """Export patient file data to Excel"""
        # Create Excel file in memory
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('بيانات المريض')

        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#4CAF50',
            'font_color': 'white',
            'border': 1
        })

        cell_format = workbook.add_format({
            'font_size': 11,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'text_wrap': True
        })

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#2196F3',
            'font_color': 'white'
        })

        # Set column widths
        worksheet.set_column('A:B', 25)
        worksheet.set_column('C:D', 20)
        worksheet.set_column('E:F', 15)

        # Add title
        worksheet.merge_range('A1:F1', f'تقرير المريض الداخلي - {self.name}', title_format)

        row = 3

        # Patient Information
        worksheet.write(row, 0, 'رقم الملف', header_format)
        worksheet.write(row, 1, self.name or '', cell_format)
        worksheet.write(row, 2, 'اسم المريض', header_format)
        worksheet.write(row, 3, self.patient_id.name or '', cell_format)
        row += 1

        worksheet.write(row, 0, 'تاريخ الدخول', header_format)
        worksheet.write(row, 1, str(self.date_in) if self.date_in else '', cell_format)
        worksheet.write(row, 2, 'تاريخ الخروج', header_format)
        worksheet.write(row, 3, str(self.date_out) if self.date_out else '', cell_format)
        row += 1

        worksheet.write(row, 0, 'الطبيب المعالج', header_format)
        worksheet.write(row, 1, self.doctor_id.name or '', cell_format)
        worksheet.write(row, 2, 'الغرفة', header_format)
        worksheet.write(row, 3, self.room_id.name or '', cell_format)
        row += 1

        worksheet.write(row, 0, 'السرير', header_format)
        worksheet.write(row, 1, self.bed_id.name or '', cell_format)
        worksheet.write(row, 2, 'التشخيص', header_format)
        worksheet.write(row, 3, self.diagnosis or '', cell_format)
        row += 2

        # Medications
        if self.medicament_line_ids:
            worksheet.merge_range(f'A{row + 1}:F{row + 1}', 'الأدوية', title_format)
            row += 2

            # Headers
            headers = ['المنتج', 'الوصف', 'التاريخ', 'الكمية', 'السعر', 'الإجمالي']
            for col, header in enumerate(headers):
                worksheet.write(row, col, header, header_format)
            row += 1

            # Data
            for line in self.medicament_line_ids:
                worksheet.write(row, 0, line.product_id.name or '', cell_format)
                worksheet.write(row, 1, line.description or '', cell_format)
                worksheet.write(row, 2, str(line.date) if line.date else '', cell_format)
                worksheet.write(row, 3, line.quantity or 0, cell_format)
                worksheet.write(row, 4, line.amount or 0, cell_format)
                worksheet.write(row, 5, line.total or 0, cell_format)
                row += 1
            row += 1

        # Services
        if self.services_line_ids:
            worksheet.merge_range(f'A{row + 1}:F{row + 1}', 'الخدمات', title_format)
            row += 2

            # Headers
            for col, header in enumerate(headers):
                worksheet.write(row, col, header, header_format)
            row += 1

            # Data
            for line in self.services_line_ids:
                worksheet.write(row, 0, line.product_id.name or '', cell_format)
                worksheet.write(row, 1, line.description or '', cell_format)
                worksheet.write(row, 2, str(line.date) if line.date else '', cell_format)
                worksheet.write(row, 3, line.quantity or 0, cell_format)
                worksheet.write(row, 4, line.amount or 0, cell_format)
                worksheet.write(row, 5, line.total or 0, cell_format)
                row += 1
            row += 1

        # Financial Summary
        worksheet.merge_range(f'A{row + 1}:F{row + 1}', 'الملخص المالي', title_format)
        row += 2

        worksheet.write(row, 0, 'إجمالي الأدوية', header_format)
        worksheet.write(row, 1, self.total_medicament or 0, cell_format)
        row += 1

        worksheet.write(row, 0, 'إجمالي الخدمات', header_format)
        worksheet.write(row, 1, self.total_services or 0, cell_format)
        row += 1

        worksheet.write(row, 0, 'الإجمالي الكلي', header_format)
        worksheet.write(row, 1, self.total or 0, cell_format)
        row += 1

        worksheet.write(row, 0, 'المبلغ المدفوع', header_format)
        worksheet.write(row, 1, self.paid_amount or 0, cell_format)
        row += 1

        worksheet.write(row, 0, 'المستحق على المريض', header_format)
        worksheet.write(row, 1, self.patient_due or 0, cell_format)

        workbook.close()
        output.seek(0)

        # Create attachment
        filename = f'patient_file_{self.name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'store_fname': filename,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'res_model': self._name,
            'res_id': self.id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
    # Update the existing action_close method
    def action_close(self):
        """Close patient file and update exit date"""
        self.state = 'closed'
        if not self.date_out:
            self.date_out = fields.Date.today()
        if self.bed_id:
            self.bed_id.mark_as_available()
    def action_create_exit_report(self):
        """Create exit report and close patient file"""
        self.ensure_one()

        if self.state == 'closed':
            raise ValidationError("الملف مغلق بالفعل")

        # Set discharge date to today if not set
        if not self.date_out:
            self.date_out = fields.Date.today()

        # Set discharge doctor to current attending doctor if not set
        if not self.discharge_doctor:
            self.discharge_doctor = self.doctor_id

        # Close the case
        self.action_close()

        # Create and download exit report
        return self.action_download_exit_report()


class PatientFileLine(models.Model):
    _name = 'patient.file.line'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"
    _description = 'patient file line'

    name = fields.Char(string="الاسم")
    patient_file_id = fields.Many2one('patient.file', string="رقم الملف")
    patient_account = fields.Selection(related="patient_file_id.patient_account",default="cash" , store=True, string="نوع الحساب")
    contract_company = fields.Many2one(related="patient_file_id.contract_company", store=True, string="شركة التعاقد")
    account_id = fields.Many2one('account.account', string="الحساب")
    product_id = fields.Many2one('product.template', string="الصنف")
    doctor_id = fields.Many2one('res.partner', domain=[('is_doctor', '=', True)], string="الطبيب")
    doctor_drags_id = fields.Many2one('res.partner', domain=[('is_doctor', '=', True)], string="طبيب التخدير", required=False,tracking=1)
    doctor_id_account = fields.Many2one('res.partner', domain=[('is_doctor', '=', True)], string="علي حساب", required=False,tracking=1)
    date = fields.Date(default=lambda self: fields.Date.context_today(self), string="التاريخ")
    hospital_product_type = fields.Selection(related='product_id.hospital_product_type', store=True)
    available_in = fields.Selection(related='product_id.available_in', store=True)
    description = fields.Char(string="بيان")
    quantity = fields.Float(default=1, digits='Product Unit of Measure', string="الكمية")
    amount = fields.Float(default=0, digits='سعر الوحدة', compute="get_amount", store=True, compute_sudo=True, string="القيمة")
    total = fields.Float(default=0, digits='الاجمالي', compute="compute_total_line_amount", store=True, string="الاجمالي")
    package_line = fields.Many2one('res.surgeries.lines', store=True, string="شاملة")
    package_qty = fields.Float(default=0, digits='Product Price', store=True, string="الكمية داخل الشاملة")
    section_id = fields.Many2one('res.sections', string="القسم")
    item_bill = fields.Char(string="ItemBill")

    @api.depends('product_id', 'hospital_product_type', 'doctor_id', 'patient_account', 'contract_company')
    def get_amount(self):
        for rec in self:
            rec.amount = 0
            if rec.hospital_product_type in ('medicament', 'consumable'):
                rec.amount = rec.product_id.list_price
            else:
                if rec.patient_account == 'cash':
                    doc_service = self.env['doctor.services'].search([('service_id', '=', rec.product_id.id),
                                                                      ('doctor_id', '=', rec.doctor_id_account.id),
                                                                      ('patient_account', '=', 'cash')], limit=1)
                    rec.amount = doc_service.amount if doc_service else rec.product_id.list_price
                if rec.patient_account == 'contract':
                    service = self.env['insurance.contractor.lines'].search([('service_id', '=', rec.product_id.id),
                                                                      ('partner_id', '=', rec.contract_company.id)], limit=1)
                    rec.amount = service.price if service else rec.product_id.list_price

    @api.onchange('product_id')
    def onchange_product(self):
        account = self.env['product.template'].sudo().browse(self.product_id.id)._get_product_accounts()
        self.account_id = account["income"].id
        self.doctor_id = self.patient_file_id.doctor_id_account.id if self.product_id.hospital_product_type not in ('medicament', 'consumable') else False

    @api.depends('quantity', 'amount', 'package_qty')
    def compute_total_line_amount(self):
        for rec in self:
            rec.total = 0
            if rec.quantity and rec.amount:
                rec.total = rec.amount * (rec.quantity - rec.package_qty)
