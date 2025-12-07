
from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

class VisitTemplate(models.Model):
    _name = 'visit.template'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Visit Template'

    name = fields.Char(required=True)
    doctor_id = fields.Many2one('res.partner', domain=[('is_doctor', '=', True)])
    medicament_lines = fields.One2many('visit.template.lines', inverse_name="visit_template_id",
                                       domain=[('medicament_id', '!=', False)],
                                       copy=True)
    laboratory_lines = fields.One2many('visit.template.lines', inverse_name="visit_template_id",
                                       domain=[('laboratory_id', '!=', False)],
                                       copy=True)
    radiology_lines = fields.One2many('visit.template.lines', inverse_name="visit_template_id",
                                      domain=[('radiology_id', '!=', False)],
                                      copy=True)
    diagnosis = fields.Text()
    notes = fields.Text()
    active = fields.Boolean(default=True)
class VisitTemplateLines(models.Model):
    _name = 'visit.template.lines'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Visit Template'

    name = fields.Char(required=False)
    visit_template_id = fields.Many2one('visit.template')
    medicament_id = fields.Many2one('product.template', domain=[('hospital_product_type', '=', 'medicament')])
    medicament_product_id = fields.Many2one('product.product', related="medicament_id.product_variant_id")
    laboratory_id = fields.Many2one('product.template', domain=[('available_in', '=', 'laboratory')])
    radiology_id = fields.Many2one('product.template', domain=[('available_in', '=', 'radiology')])
    notes = fields.Char()
    dosage = fields.Char()
    dosage_id = fields.Many2one('visit.dosage', string="Dosage")
    duration_id = fields.Many2one('visit.duration', string="Duration")
class ClinicVisit(models.Model):
    _name = 'clinic.visit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Clinic Visit'

    name = fields.Char(tracking=True, index=True, readonly=True, copy=False, default=lambda self: '/', string="الاسم")
    queue_number = fields.Integer(required=True, default=1, index=True, string="الدور")
    date_next_visit = fields.Date(default=lambda self: fields.Date.today() + timedelta(days=7), tracking=True, string="ميعاد الاستشارة")
    doctor_id = fields.Many2one('res.partner', required=False, domain=[('is_doctor', '=', True)], string="الطبيب")
    doctor_shift = fields.Boolean(related="doctor_id.is_shift", store=True, string="شيفت")
    shift = fields.Selection(selection=[('morning', 'صباحا'), ('night', 'مساءا')], string="الشيفت")
    clinic_id = fields.Many2one('res.clinics', related="doctor_id.clinic", required=True, tracking=True, string="التخصص")
    patient_code = fields.Char(
        string='كود المريض',
        copy=False,
        related="patient_id.patient_code",
        index=True,
        tracking=True,
        help="Unique patient code"
    )
    product_filter = fields.Selection([
        ('all', 'جميع المنتجات'),
        ('medicament', 'أدوية'),
        ('consumable', 'مستهلكات'),
        ('medical_service', 'خدمة طبية'),
        ('os', 'خدمات أخري'),
        ('accommodation', 'إقامة')
    ], string="فلتر المنتجات", default='all')

    patient_id = fields.Many2one('res.partner', required=False, domain=[('is_patient', '=', True)], string="المريض")
    patient_file = fields.Many2one('patient.file', string="ملف المريض")
    currency_id = fields.Many2one('res.currency',
                                  default=lambda self: self.env.company.currency_id,
                                  string='Currency')
    patient_room = fields.Many2one(related="patient_file.room_id", store=True, string="الغرفة")
    patient_bed = fields.Many2one(related="patient_file.bed_id", store=True, string="السرير")
    patient_account = fields.Selection(related="patient_id.patient_account",default="cash" , store=True, readonly=False, string="نوع الحساب")
    patient_employer = fields.Many2one(related="patient_id.employer", store=True, readonly=False, string="الشركة التابع لها")
    patient_contract_company = fields.Many2one(related="patient_id.contract_company", store=True, readonly=False, string="شركة التعاقد")
    patient_age = fields.Integer(related="patient_id.age", store=True, tracking=1,  readonly=False,
                              string="العمر")
    patient_street = fields.Char(related="patient_id.street", store=True, tracking=1, readonly=False,
                                 string="العنوان")
    patient_nat_id = fields.Char(related="patient_id.nat_id", store=True, tracking=1,  readonly=False,
                                 string="الرقم القومي")
    patient_phone = fields.Char(related="patient_id.phone", store=True, tracking=1,  readonly=False,
                                string="تليفون 1")
    patient_mobile = fields.Char(related="patient_id.mobile", store=True, tracking=1, readonly=False,
                                 string="تليفون 2")
    service_id = fields.Many2one('doctor.services', string="الخدمة")
    available_in = fields.Selection([
        ('surgeries', 'عمليات'),
        ('clinic', 'عيادات خارجية'),
        ('inpatient', 'الداخلي'),
        ('icu', 'عناية مركزة'),
        ('laboratory', 'المعمل'),
        ('catheterization', 'القسطرة'),
        ('radiology', 'الاشعة'),
        ('nursing', 'تمريض')
    ], string="متاح في",related="service_id.available_in")
    hospital_product_type = fields.Selection([
        ('medicament', 'أدوية'),
        ('consumable', 'مستهلكات'),
        ('medical_service', 'خدمة طبية'),
        ('os', 'خدمات أخري'),
        ('accommodation', 'إقامة')
    ], string="نوع الصنف",related="service_id.hospital_product_type")
    product_id = fields.Many2one(related="service_id.service_id", store=True, readonly=False, string="الصنف")
    can_be_installment = fields.Boolean(related='product_id.can_be_installment', string="يمكن تقسيطها")
    reservation_date = fields.Datetime(default=fields.Datetime.now, tracking=True, string="تاريخ الحجز")
    date = fields.Date(default=lambda self: fields.Date.today(), tracking=True, string="تاريخ الخدمة")
    state = fields.Selection(selection=[('waiting', 'Waiting'), ('done', 'Done'), ('cancelled', 'cancelled')],
                             default="waiting",
                             required=False, string="الحالة")
    template_id = fields.Many2one('visit.template', string="قالب العيادة")
    medicament_lines = fields.One2many('visit.lines', inverse_name="clinic_visit_id")
    laboratory_lines = fields.One2many('laboratory.visit.lines', inverse_name="clinic_visit_id")
    radiology_lines = fields.One2many('radiology.visit.lines', inverse_name="clinic_visit_id")
    lab_request_id = fields.Many2one('lab.request')
    radiology_request_id = fields.Many2one('radiology.request')
    sales_order = fields.Many2one('sale.order', string="امر البيع")
    diagnosis = fields.Text(string="التشخيص")
    notes = fields.Text(string="ملاحظات")
    move_id = fields.Many2one('account.move', string="القيد")
    doctor_amount = fields.Float(default=0, digits='Product Price', tracking=True, compute="compute_amount", store=True, string="أجر الطبيب")
    deposit_amount = fields.Float(default=0, string="أمانات")
    show_deposit = fields.Boolean(default=False, compute="_compute_show_deposit", store=True, string="إظهار الامانات")
    pay_deposit = fields.Boolean(default=False, string="أمانات")
    approve_id = fields.Many2one('service.approval', string="الموافقة")
    amount = fields.Float(default=0, digits='Product Price', tracking=True, compute="compute_amount", store=True, compute_sudo=True, string="القيمة")
    patient_per = fields.Float(default=0, digits='Product Price', tracking=True, string="نسبة التحمل")
    service_exp_amount = fields.Float(default=0, digits='Product Price', tracking=True, compute="compute_amount", store=True, compute_sudo=True, string="مصروفات ادارية")
    service_tax_amount = fields.Float(default=0, digits='Product Price', tracking=True, compute="compute_amount", store=True, compute_sudo=True, string="ضريبة")
    total_amount = fields.Float(default=0, digits='Product Price', tracking=True, compute="compute_amount", store=True, compute_sudo=True, string="الاجمالي")
    patient_amount = fields.Float(default=0, digits='Product Price', tracking=True, string="مطلوب من المريض")
    cash_posted = fields.Boolean(default=False, string="ترحيل خزينة")
    doctor_posted = fields.Boolean(default=False, string="ترحيل للطبيب")
    doctor_paid = fields.Boolean(default=False, string="دفع للطبيب")
    session_id = fields.Many2one('close.user.session', string="شيفت الاستقبال")
    accounting_user = fields.Many2one('res.users', string="مسئول الحسابات")
    section_id = fields.Many2one('res.sections', string="القسم")
    account_id = fields.Many2one('account.account', string="الحساب")
    nursing_service = fields.One2many('nursing.services.line', inverse_name="clinic_visit_id", string="التمريض")
    lab_service = fields.One2many('lab.services.line', inverse_name="clinic_visit_id", string="المعمل")
    lab_services = fields.One2many('lab.services.line', inverse_name="clinic_visit_id", string="المعمل")
    on_site = fields.Boolean(string="داخلي/خارجي")
    canceled = fields.Boolean(default=False, string="تم الالغاء")
    claim_id = fields.Many2one('contract.claim')
    #print direct
    print_count = fields.Integer(string="Print Count", default=0, readonly=True)
    last_print_status = fields.Selection([
        ('none', 'Not Printed'),
        ('success', 'Print Success'),
        ('failed', 'Print Failed')
    ], string="Last Print Status", default='none')
    # Add this field for patient visit history
    previous_visits_ids = fields.One2many(
        'clinic.visit',
        compute='_compute_previous_visits',
        string="Previous Visits"
    )
    previous_visits_count = fields.Integer(
        compute='_compute_previous_visits',
        string="Previous Visits Count"
    )
    # Add inpatient history fields
    previous_inpatient_ids = fields.One2many(
        'patient.file',
        compute='_compute_previous_inpatient',
        string="Previous Inpatient Files"
    )
    previous_inpatient_count = fields.Integer(
        compute='_compute_previous_inpatient',
        string="Previous Inpatient Count"
    )

    @api.onchange('product_filter')
    def _onchange_product_filter(self):
        """Refresh nursing service lines when filter changes"""
        # This will trigger recomputation of the product_domain in child lines
        for line in self.nursing_service:
            line._compute_product_domain()
    @api.depends('patient_id', 'date')
    def _compute_previous_visits(self):
        for record in self:
            if record.patient_id and record.date:
                # Get previous visits for the same patient, excluding current visit
                domain = [
                    ('patient_id', '=', record.patient_id.id),
                    ('date', '<', record.date),
                ]
                # Only add id filter if record exists (has been saved)
                if record.id and not isinstance(record.id, models.NewId):
                    domain.append(('id', '!=', record.id))

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
    @api.depends('patient_id', 'date')
    def _compute_previous_inpatient(self):
        for record in self:
            if record.patient_id and record.date:
                # Get previous inpatient files for the same patient
                domain = [
                    ('patient_id', '=', record.patient_id.id),
                    ('date_in', '<', record.date),
                ]
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
        """Action to view visit details in readonly mode"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Visit Details - {self.name}',
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
    def print_reception_receipt(self):
        data = {
            'ids': self.ids,
            'model': 'clinic.visit',
            'report_type': 'reception',
        }
        return self.env.ref('hospital_base.report_reception_receipt').report_action(self, data=data)
    def print_accounting_receipt(self):
        data = {
            'ids': self.ids,
            'model': 'clinic.visit',
            'report_type': 'accounting',
        }
        return self.env.ref('hospital_base.report_accounting_receipt').report_action(self, data=data)
    def print_pharmacy_receipt(self):
        data = {
            'ids': self.ids,
            'model': 'clinic.visit',
            'report_type': 'pharmacy',
        }
        return self.env.ref('hospital_base.report_pharmacy_receipt').report_action(self, data=data)
    def print_receipt_direct(self):
        """Direct print receipt without preview"""
        self.ensure_one()
        self.print_count += 1
        print_type = "original" if self.print_count == 1 else f"copy_{self.print_count - 1}"

        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'name': self.name,
                'print_type': print_type,
                'print_count': self.print_count
            },
        }

        # Check if OmniPrint is installed
        if self.env['ir.module.module'].sudo().search([
            ('name', '=', 'omni_print'),
            ('state', '=', 'installed')
        ]):
            return self._print_with_omniprint(data, print_type)
        else:
            return self._print_with_direct_js(data, print_type)
    def _print_with_omniprint(self, data, print_type):
        """Use OmniPrint for direct printing if available"""
        return {
            'type': 'ir.actions.report',
            'report_name': 'hospital_base.report_receipt',
            'report_type': 'omniprint',
            'data': data,
            'print_immediately': True,
            'context': {
                'print_type': print_type,
                'clinic_visit_id': self.id,
            }
        }
    def _print_with_direct_js(self, data, print_type):
        """Fall back to direct printing via JS"""
        return {
            'type': 'ir.actions.client',
            'tag': 'direct_print_action',
            'name': 'Print Receipt',
            'context': {
                'report_name': 'hospital_base.report_receipt',
                'data': data,
                'clinic_visit_id': self.id,
                'print_type': print_type,
            }
        }
    def print_receipt_accountant(self):
        """Print receipt marked as accountant copy"""
        self.ensure_one()
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'name': self.name,
                'print_type': 'accountant',
                'print_count': self.print_count + 1
            },
        }

        if self.env['ir.module.module'].sudo().search([
            ('name', '=', 'omni_print'),
            ('state', '=', 'installed')
        ]):
            return self._print_with_omniprint(data, 'accountant')
        else:
            return self._print_with_direct_js(data, 'accountant')
    def update_print_status(self, status):
        """Update print status - called from JS"""
        self.ensure_one()
        self.write({'last_print_status': status})
        return True
    @api.onchange('deposit_amount')
    def _onchange_deposit_amount(self):
        for rec in self:
            if rec.deposit_amount < 0:
                raise ValidationError(_('قيمة الدفع اكبر من صفر'))
            else:
                if rec.patient_account == 'contract':
                    rec.amount = rec.service_id.amount
                    rec.doctor_amount = rec.service_id.doctor_amount
                    rec.service_exp_amount = rec.service_id.exp_amount
                    rec.service_tax_amount = rec.service_id.tax_amount
                    rec.total_amount = rec.amount + rec.service_exp_amount + rec.service_tax_amount
                    rec.patient_per = rec.service_id.amount
                    rec.patient_amount = rec.service_id.amount
                    rec.deposit_amount = rec.service_id.amount
    @api.depends('service_id', 'patient_account', 'patient_contract_company')
    def _compute_show_deposit(self):
        for rec in self:
            rec.show_deposit = False
            if rec.service_id and rec.patient_account == 'contract':
                service = rec.service_id.service_id.id
                approve = self.env['insurance.contractor.lines'].search([('partner_id', '=', rec.patient_contract_company.id),
                                                                         ('service_id', '=', service),
                                                                         ('approval', '=', True),
                                                                         ('active', '=', True)], limit=1)
                if approve:
                    rec.show_deposit = approve.approval
    @api.depends('doctor_id', 'patient_per', 'patient_account', 'patient_contract_company', 'service_id',
                 'pay_deposit', 'patient_file', 'nursing_service', 'nursing_service.total', 'lab_services',
                 'lab_services.product_id', 'lab_services.total')
    def compute_amount(self):
        for rec in self:
            total_nursing = 0
            rec.doctor_amount = 0
            rec.amount = 0
            rec.service_exp_amount = 0
            rec.service_tax_amount = 0
            rec.total_amount = 0
            if rec.nursing_service:
                total_nursing = sum(rec.nursing_service.mapped('total'))
                rec.amount = total_nursing
                rec.doctor_amount = 0
                rec.service_exp_amount = self.env.company.nursing_exp
                rec.service_tax_amount = self.env.company.nursing_tax
                rec.total_amount = rec.amount + rec.service_exp_amount + rec.service_tax_amount
                rec.patient_per = rec.total_amount
                rec.patient_amount = rec.patient_per
            if rec.lab_services:
                total_nursing = sum(rec.lab_services.mapped('total'))
                rec.amount = total_nursing
                rec.doctor_amount = (total_nursing * rec.doctor_id.lab_amount)/100
                rec.service_exp_amount = self.env.company.nursing_exp
                rec.service_tax_amount = self.env.company.nursing_tax
                rec.total_amount = rec.amount + rec.service_exp_amount + rec.service_tax_amount
                rec.patient_per = rec.total_amount
                rec.patient_amount = rec.patient_per
            if rec.patient_account == 'cash' and rec.service_id and not rec.patient_file:
                rec.deposit_amount = 0
                if rec.service_id.amount and rec.service_id.amount > 0:
                    rec.amount = rec.service_id.amount
                    rec.doctor_amount = rec.service_id.doctor_amount
                    rec.service_exp_amount = rec.service_id.exp_amount
                    rec.service_tax_amount = rec.service_id.tax_amount
                    rec.total_amount = rec.amount + rec.service_exp_amount + rec.service_tax_amount
                    rec.patient_per = rec.total_amount
                    rec.patient_amount = rec.patient_per
                else:
                    rec.amount = rec.service_id.service_id.list_price
                    rec.service_exp_amount = rec.service_id.service_id.exp_amount
                    rec.service_tax_amount = rec.service_id.service_id.tax_amount
                    rec.total_amount = rec.amount + rec.service_exp_amount + rec.service_tax_amount
                    rec.patient_amount = rec.patient_per
            elif rec.patient_account == 'contract' and rec.service_id and not rec.patient_file:
                if rec.patient_contract_company:
                    contract = self.env['insurance.contractor.lines'].search([('partner_id', '=', rec.patient_contract_company.id),
                                                                              ('service_id', '=', rec.service_id.service_id.id),
                                                                              ('active', '=', True)], limit=1)
                    if contract:
                        if not rec.pay_deposit:
                            rec.amount = contract.price + total_nursing
                            rec.doctor_amount = rec.service_id.doctor_amount
                            rec.service_exp_amount = contract.contract_id.exp_amount
                            rec.service_tax_amount = contract.contract_id.tax_amount
                            rec.total_amount = rec.amount + rec.service_exp_amount + rec.service_tax_amount
                            rec.patient_amount = rec.patient_per
                        else:
                            rec.amount = rec.service_id.amount + total_nursing
                            rec.patient_per = rec.service_id.amount
                            rec.doctor_amount = rec.service_id.doctor_amount
                            rec.service_exp_amount = rec.service_id.exp_amount
                            rec.service_tax_amount = rec.service_id.tax_amount
                            rec.total_amount = rec.amount + rec.service_exp_amount + rec.service_tax_amount
                            rec.deposit_amount = rec.total_amount
                            rec.patient_amount = rec.total_amount
    def patient_queue_number(self):
        self.ensure_one()
        queue = self.doctor_id.start_from
        max_queue = self.doctor_id.max_num
        doctor = self.doctor_id
        shift = self.shift
        date = self.date
        current_queue = self.env["clinic.visit"].search([('doctor_id', '=', doctor.id),
                                                         ('date', '=', date),
                                                         ('shift', '=', shift)])
        if current_queue:
            check = max(current_queue.mapped('queue_number')) + 1
            if max_queue > 0:
                if check < max_queue:
                    return check
                else:
                    raise ValidationError(_("تم الوصول لاقصي رقم ممكن"))
            else:
                return check
        return queue
    @api.depends('doctor_id', 'date', 'shift','patient_id','service_id')
    @api.onchange('doctor_id', 'date', 'shift','patient_id','service_id')
    def onchange_doctor_date(self):
        self.queue_number = self.patient_queue_number()
    @api.onchange('template_id')
    def onchange_template_id(self):
        if self.template_id:
            self.diagnosis = self.template_id.diagnosis
            self.notes = self.template_id.notes
            medicament_lines = [(5, 0, 0)]
            laboratory_lines = [(5, 0, 0)]
            radiology_lines = [(5, 0, 0)]
            for rec in self.template_id.medicament_lines:
                val = (0, 0, {
                    'medicament_id': rec.medicament_id.id,
                    'notes': rec.notes,
                    'dosage': rec.dosage,
                })
                medicament_lines.append(val)
            for rec in self.template_id.laboratory_lines:
                val = (0, 0, {
                    'laboratory_id': rec.laboratory_id,
                    'notes': rec.notes
                })
                laboratory_lines.append(val)
            for rec in self.template_id.radiology_lines:
                val = (0, 0, {
                    'radiology_id': rec.radiology_id,
                    'notes': rec.notes
                })
                radiology_lines.append(val)
            self.medicament_lines = medicament_lines
            self.laboratory_lines = laboratory_lines
            self.radiology_lines = radiology_lines
        else:
            self.medicament_lines = False
            self.laboratory_lines = False
            self.radiology_lines = False

    def action_done(self):
        for rec in self:

            if not rec.lab_request_id:
                labs = rec.laboratory_lines
                val = {
                    'date': rec.date,
                    'patient_id': rec.patient_id.id,
                    'doctor_id': rec.doctor_id.id,
                    'clinic_visit_id': rec.id,
                }
                lab_req = self.env['lab.request'].create(val)
                for lab in labs:
                    lab_test = self.env['lab.test'].search([('product_id', '=', lab.laboratory_id.id)], limit=1)
                    lab_test_line = {
                        'lab_test_id': lab_test.id,
                        'lab_request_id': lab_req.id
                    }
                    self.env['lab.request.lines'].create(lab_test_line)
                rec.lab_request_id = lab_req.id
                self.env.cr.commit()
            if not rec.radiology_request_id:
                rads = rec.radiology_lines
                for rad in rads:
                    val = {
                        'date': rec.date,
                        'patient_id': rec.patient_id.id,
                        'doctor_id': rec.doctor_id.id,
                        'clinic_visit_id': rec.id,
                        'service_id': rad.radiology_id.id,
                        'note': rad.notes
                    }
                    rad_req = self.env['radiology.request'].create(val)
                    rec.radiology_request_id = rad_req.id
                    self.env.cr.commit()
            if rec.sales_order:
                items = rec.medicament_lines
                val = {
                    'partner_id': rec.patient_id.id,
                    'doctor': rec.doctor_id.id,
                    'clinic_visit': rec.id,
                    'date_order': fields.Datetime.now()
                }
                sale_order = self.env['sale.order'].sudo().create(val)
                for item in items:
                    line = {
                        'order_id': sale_order.id,
                        'product_id': item.medicament_product_id.id,
                        'product_template_id': item.medicament_id.id,
                        'name': item.medicament_id.name,
                        'dosage': item.dosage,
                        'product_uom_qty': item.qty
                    }
                    sale_order_line = self.env['sale.order.line'].sudo().create(line)
                rec.sales_order = sale_order.id
                self.env.cr.commit()
            rec.state = 'done'
    def create_sale_order_confirm(self):
        for rec in self:
            if not rec.sales_order:
                items = rec
                val = {
                    'partner_id': rec.patient_id.id,
                    'doctor': rec.doctor_id.id,
                    'clinic_visit': rec.id,
                    'date_order': fields.Datetime.now(),
                    'is_cash_payment': rec.patient_account == 'cash',
                }
                sale_order = self.env['sale.order'].sudo().create(val)
                for item in items:
                    line = {
                        'order_id': sale_order.id,
                        'product_id': item.product_id.product_variant_id.id,
                        'product_template_id': item.product_id.id,
                        'name': item.product_id.name,
                        'dosage': 0,
                        'product_uom_qty': 1,
                        'price_unit':item.patient_amount,
                    }
                    sale_order_line = self.env['sale.order.line'].sudo().create(line)
                rec.sales_order = sale_order.id
                self.env.cr.commit()
                rec.sales_order.action_confirm()
                self.env.cr.commit()

    def create_sale_order(self):
        for rec in self:
            if rec.sales_order:
                items = rec
                val = {
                    'partner_id': rec.patient_id.id,
                    'doctor': rec.doctor_id.id,
                    'clinic_visit': rec.id,
                    'is_cash_payment': rec.patient_account == 'cash',
                    'date_order': fields.Datetime.now()
                }
                sale_order = self.env['sale.order'].sudo().create(val)
                for item in items:
                    line = {
                        'order_id': sale_order.id,
                        'product_id': item.product_id.product_variant_id.id,
                        'product_template_id': item.product_id.id,
                        'name': item.product_id.name,
                        'dosage': 0,
                        'product_uom_qty': 1,
                        'price_unit':item.patient_amount,
                    }
                    sale_order_line = self.env['sale.order.line'].sudo().create(line)
                rec.sales_order = sale_order.id
                self.env.cr.commit()
    def create_sale_order_nursing(self):
        for rec in self:
            if not rec.sales_order:
                items = rec
                val = {
                    'partner_id': rec.patient_id.id,
                    'doctor': rec.doctor_id.id,
                    'clinic_visit': rec.id,
                    'is_cash_payment': True,
                    'date_order': fields.Datetime.now()
                }
                sale_order = self.env['sale.order'].sudo().create(val)
                for item in items.nursing_service:
                    line = {
                        'order_id': sale_order.id,
                        'product_id': item.product_id.product_variant_id.id,
                        'product_template_id': item.product_id.id,
                        'name': item.product_id.name,
                        'product_uom_qty': 1,
                        'price_unit':item.total,
                    }
                    sale_order_line = self.env['sale.order.line'].sudo().create(line)
                rec.sales_order = sale_order.id
                self.env.cr.commit()

    def print_clinic_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'name': 'name'
            },
        }
        return self.env.ref('hospital_base.report_clinic_print_report').report_action(self)

    def create_sale_order_lab_services(self):
        for rec in self:
            if not rec.sales_order:
                val = {
                    'partner_id': rec.patient_id.id,
                    'doctor': rec.doctor_id.id,
                    'clinic_visit': rec.id,
                    'is_cash_payment': True,
                    'date_order': fields.Datetime.now()
                }
                sale_order = self.env['sale.order'].sudo().create(val)

                # إنشاء بنود أمر البيع
                for item in rec.lab_services:
                    if item.product_id:
                        # الحصول على معلومات المنتج
                        product = item.product_id.product_variant_id or item.product_id

                        line_vals = {
                            'order_id': sale_order.id,
                            'product_id': product.id,
                            'product_template_id': item.product_id.id,
                            'name': item.product_id.name,
                            'product_uom_qty': 1,
                            'product_uom': product.uom_id.id,  # إضافة وحدة القياس
                            'price_unit': item.total,
                            'customer_lead': 0.0,  # إضافة المهلة الزمنية
                        }

                        # إنشاء البند باستخدام create بدلاً من sudo().create
                        sale_order.write({
                            'order_line': [(0, 0, line_vals)]
                        })

                # ربط أمر البيع بالزيارة
                rec.sales_order = sale_order.id
                self.env.cr.commit()

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'

    def action_waiting(self):
        for rec in self:
            rec.state = 'waiting'

    def request_approve(self, values, labs=None):
        get_approve = False
        if values.get('product_id'):
            get_approve = values.get('product_id')
            check = self.env['service.approval'].search([('service_id', '=', int(values.get('product_id'))),
                                                         ('patient_id', '=', int(values.get('patient_id'))),
                                                         ('state', '=', 'waiting')], limit=1)
        if labs:
            lines = [int(lab[2]['product_id']) for lab in labs]
            get_approve = lines[0]
            check = self.env['service.approval'].search([('service_id', 'in', lines),
                                                         ('patient_id', '=', int(values.get('patient_id'))),
                                                         ('state', '=', 'waiting')], limit=1)
        if not check:
            section = self.env['res.sections'].search([('type', '=', 'clinic')], limit=1)

            val = {
                "service_id": get_approve,
                "doctor_id": values.get('doctor_id'),
                "patient_id": values.get('patient_id'),
                "patient_account": values.get('patient_account'),
                "patient_employer": values.get('patient_employer'),
                "patient_contract_company": values.get('patient_contract_company'),
                "deposit_amount": values.get('deposit_amount'),
                "section_id": section.id,
            }
            result = self.env['service.approval'].create(val)
            return result
        else:
            return False

    def print_receipt_confirm_lab(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'name': 'name'
            },
        }
        self.create_sale_order_lab_services()

        return self.env.ref('hospital_base.report_receipt_report').report_action(self)
    def print_receipt_confirm_lab_services(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'name': 'name'
            },
        }
        self.create_sale_order_lab_services()

        return self.env.ref('hospital_base.report_receipt_report').report_action(self)
    def action_doctor_post_serv(self):
        if self.env.context.get('params', {}):
            ids = self.env.context.get('active_ids')
            doctor = self.env.context.get('params', {}).get('active_id')
            min_id = min(ids)
            max_id = max(ids)
            total = sum(self.env['clinic.visit'].browse(ids).mapped('doctor_amount'))
            return {
                'name': _('Doctor Post'),
                'type': 'ir.actions.act_window',
                'res_model': 'doctor.post.visits',
                'view_mode': 'form',
                'view_id': self.env.ref('hospital_base.doctor_post_visits_form').id,
                'target': 'new',
                'context': dict(self._context, **{
                    'default_doctor_id': doctor,
                    'default_from_rec': min_id,
                    'default_to_rec': max_id,
                    'default_total_amount': total,
                    'visit_post_ids': ids
                })
            }
        else:
            return False
    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            values['name'] = self.env['ir.sequence'].next_by_code('reception.cash')
        if 'date' in values:
            service_date = values.get('date')
            if fields.Date.from_string(service_date) < fields.Date.today():
                raise ValidationError(_('Check Date Please'))
        if 'patient_account' in values:
            service = values.get('product_id')
            labs = values.get('lab_services')
            patient_account = values.get('patient_account')
            approve_id = values.get('approve_id') if 'approve_id' in values else False
            if patient_account == 'contract' and not approve_id:
                company = values.get('patient_contract_company')
                check = self.env['insurance.contractor.lines'].search([('partner_id', '=', company),
                                                                       ('service_id', '=', service),
                                                                       ('approval', '=', True),
                                                                       ('active', '=', True)], limit=1)
                if labs:
                    lines = [int(lab[2]['product_id']) for lab in labs]
                    check = self.env['insurance.contractor.lines'].search([('partner_id', '=', company),
                                                                           ('service_id', 'in', lines),
                                                                           ('approval', '=', True),
                                                                           ('active', '=', True)], limit=1)
                if check:
                    approve = self.request_approve(values, labs=labs)
                    if not approve:
                        raise ValidationError(_('تم طلب موافقة للخدمة بالفعل'))
                    else:
                        self.env.cr.commit()
                        if 'deposit_amount' in values:
                            deposit_amount = values.get('deposit_amount')
                            if deposit_amount > 0:
                                values['approve_id'] = approve.id
                                result = super(ClinicVisit, self).create(values)
                                return result
                            else:
                                raise ValidationError(_('تم ارسال موافقة لقسم التعاقدات برقم  %s', approve.id))
                        else:
                            return False
                else:
                    result = super(ClinicVisit, self).create(values)
                    return result
            elif patient_account == 'contract' and approve_id:
                approve = self.env['service.approval'].browse(approve_id)
                result = super(ClinicVisit, self).create(values)
                approve.state = 'done'
                approve.visit_id = result.id
                return result
            else:
                result = super(ClinicVisit, self).create(values)
                return result
        else:
            result = super(ClinicVisit, self).create(values)
            return result

    def print_receipt_confirm(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'name': 'name'
            },
        }
        self.create_sale_order_confirm()

        return self.env.ref('hospital_base.report_receipt_report').report_action(self)
    def print_receipt_confirm_nursing(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'name': 'name'
            },
        }
        self.create_sale_order_nursing()

        return self.env.ref('hospital_base.report_receipt_report').report_action(self)

    def print_receipt(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'name': 'name'
            },
        }
        self.create_sale_order()

    def open_nursing_rec(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _("Nursing Service"),
            'res_model': 'clinic.visit',
            'view_mode': 'form',
            'res_id': self.env.context.get('clinic_visit_id'),
            'views': [[self.env.ref('hospital_base.clinic_visit_nursing_service_form').id, "form"]],
            'target': 'new',
            'context': {'create': False, 'edit': False, 'delete': False, 'duplicate': False}
        }
    def open_lab_rec(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _("Laboratory Service"),
            'res_model': 'clinic.visit',
            'view_mode': 'form',
            'res_id': self.env.context.get('clinic_visit_id'),
            'views': [[self.env.ref('hospital_base.clinic_visit_lab_services_form').id, "form"]],
            'target': 'new',
            'context': {'create': False, 'edit': False, 'delete': False, 'duplicate': False}
        }

    def request_cancel_move(self):
        self.ensure_one()
        if self.doctor_posted:
            raise ValidationError(_("Move already posted to doctor account"))
        move_lines = [(5, 0, 0)]
        journal = self.env.company.main_cash_journal
        debit_line = (0, 0, {
            "account_id": self.account_id.id,
            "partner_id": self.patient_id.id,
            "debit": self.patient_amount
        })
        credit_line = (0, 0, {
            "account_id": journal.default_account_id.id,
            "partner_id": self.patient_id.id,
            "credit": self.patient_amount
        })
        move_lines.append(debit_line)
        move_lines.append(credit_line)
        cash_entry = {
            'date': fields.Date.today(),
            'journal_id': journal.id,
            'ref': _('Cancel Move %s') % self.name,
            'line_ids': move_lines
        }
        entry_cash = self.env["account.move"].create(cash_entry)
        entry_cash.action_post()
        self.refund_move = entry_cash.id
        self.canceled = True
class VisitLines(models.Model):
    _name = 'visit.lines'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Visit Lines'

    name = fields.Char(required=False)
    clinic_visit_id = fields.Many2one('clinic.visit', tracking=True, string="الخدمة")
    medicament_id = fields.Many2one('product.template', domain=[('hospital_product_type', '=', 'medicament')], string="الصنف")
    medicament_product_id = fields.Many2one('product.product', related="medicament_id.product_variant_id")
    notes = fields.Char(string="ملاحظات")
    dosage = fields.Char(string="الجرعة")
    dosage_id = fields.Many2one('visit.dosage',string="Dosage")
    duration_id = fields.Many2one('visit.duration', string="Duration")
    qty = fields.Float(default=1, digits='Product Unit of Measure', string="الكمية")
    active = fields.Boolean(default=True, string="الحالة")
class Dosage(models.Model):
    _name = 'visit.dosage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Dosage'

    name = fields.Char(required=True,translate=True,string="الاسم")
    active = fields.Boolean(default=True, string="الحالة")
class Duration(models.Model):
    _name = 'visit.duration'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'visit duration'

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
class LaboratoryVisitLines(models.Model):
    _name = 'laboratory.visit.lines'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Laboratory Visit Lines'

    name = fields.Char(required=False)
    clinic_visit_id = fields.Many2one('clinic.visit', tracking=True, string="الخدمة")
    laboratory_id = fields.Many2one('product.template', domain=[('available_in', '=', 'laboratory')], string="التحليل")
    medicament_product_id = fields.Many2one('product.product', related="laboratory_id.product_variant_id")
    notes = fields.Char(string="ملاحظات")
    active = fields.Boolean(default=True, string="الحالة")
class RadiologyVisitLines(models.Model):
    _name = 'radiology.visit.lines'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Laboratory Visit Lines'

    name = fields.Char(required=False)
    clinic_visit_id = fields.Many2one('clinic.visit', tracking=True, string="الخدمة")
    radiology_id = fields.Many2one('product.template', domain=[('available_in', '=', 'radiology')])
    medicament_product_id = fields.Many2one('product.product', related="radiology_id.product_variant_id")
    notes = fields.Char(string="ملاحظات")
    active = fields.Boolean(default=True, string="الحالة")
class NursingServicesLine(models.Model):
    _name = 'nursing.services.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Nursing Services line'

    name = fields.Char(string="الاسم")
    clinic_visit_id = fields.Many2one('clinic.visit', tracking=True, string="الخدمة")
    patient_account = fields.Selection(related="clinic_visit_id.patient_account", default="cash" ,store=True, string="نوع الحساب")
    contract_company = fields.Many2one(related="clinic_visit_id.patient_contract_company", store=True, string="شركة التعاقد")
    account_id = fields.Many2one('account.account', string="الحساب")
    product_id = fields.Many2one('product.template', domain="product_domain", string="الصنف")
    doctor_id = fields.Many2one('res.partner', domain=[('is_doctor', '=', True)], string="الطبيب")
    date = fields.Date(default=lambda self: fields.Date.context_today(self), string="التاريخ")
    hospital_product_type = fields.Selection(related='product_id.hospital_product_type', store=True)
    available_in = fields.Selection(related='product_id.available_in', store=True)
    description = fields.Char(string="بيان")
    quantity = fields.Float(default=1, digits='Product Unit of Measure', string="الكمية")
    amount = fields.Float(default=0, digits='Product Price', compute="get_amount", store=True, compute_sudo=True, string="القيمة")
    total = fields.Float(default=0, digits='Product Price', compute="compute_total_line_amount", store=True, string="اجمالي")
    section_id = fields.Many2one('res.sections', string="القسم")
    state = fields.Selection(selection=[('draft', 'draft'), ('confirmed', 'confirmed'), ('cancelled', 'cancelled')],
                             default="draft",
                             required=False, string="الحالة")
    # Compute domain for product_id based on filter selection
    product_domain = fields.Char(
        compute='_compute_product_domain',
        readonly=True,
        store=False,
    )

    @api.depends('clinic_visit_id.product_filter')
    def _compute_product_domain(self):
        for record in self:
            base_domain = ['|', ('available_in', '=', 'nursing'), ('detailed_type', '=', 'service')]

            if record.clinic_visit_id and record.clinic_visit_id.product_filter != 'all':
                # Filter by specific hospital_product_type
                domain = base_domain + [('hospital_product_type', '=', record.clinic_visit_id.product_filter)]
            else:
                # Show all products with base domain
                domain = base_domain

            record.product_domain = str(domain)

    def _onchange_product_filter(self):
        """Clear product_id when filter changes"""
        #if self.product_filter:
        #    self.product_id = False
        pass

    @api.depends('product_id', 'hospital_product_type', 'doctor_id', 'patient_account', 'contract_company')
    def get_amount(self):
        for rec in self:
            rec.amount = 0
            if rec.hospital_product_type in ('medicament', 'consumable'):
                rec.amount = rec.product_id.list_price
            else:
                if rec.patient_account == 'cash':
                    doc_service = self.env['doctor.services'].search([('service_id', '=', rec.product_id.id),
                                                                      ('doctor_id', '=', rec.doctor_id.id),
                                                                      ('patient_account', '=', 'cash')], limit=1)
                    rec.amount = doc_service.amount if doc_service else rec.product_id.list_price
                if rec.patient_account == 'contract':
                    service = self.env['insurance.contractor.lines'].search([('service_id', '=', rec.product_id.id),
                                                                      ('partner_id', '=', rec.contract_company.id)], limit=1)
                    rec.amount = service.price if service else rec.product_id.list_price

    @api.onchange('product_id')
    def onchange_product(self):
        self.ensure_one()
        account = self.env['product.template'].sudo().browse(self.product_id.id)._get_product_accounts()
        self.account_id = account["income"].id
        self.doctor_id = self.clinic_visit_id.doctor_id.id if self.product_id.hospital_product_type not in ('medicament', 'consumable') else False

    @api.depends('quantity', 'amount')
    def compute_total_line_amount(self):
        for rec in self:
            rec.total = 0
            if rec.quantity and rec.amount:
                rec.total = rec.amount * rec.quantity
class LabServicesLine(models.Model):
    _name = 'lab.services.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Lab Services line'

    name = fields.Char(string="الاسم")
    clinic_visit_id = fields.Many2one('clinic.visit', tracking=True, string="الخدمة")
    patient_account = fields.Selection(related="clinic_visit_id.patient_account",default="cash" , store=True, string="نوع الحساب")
    contract_company = fields.Many2one(related="clinic_visit_id.patient_contract_company", store=True, string="شركة التعاقد")
    account_id = fields.Many2one('account.account', string="الحساب")
    product_id = fields.Many2one('product.template', domain=[('available_in', '=', 'laboratory')], string="الصنف")
    doctor_id = fields.Many2one('res.partner', domain=[('is_doctor', '=', True)], string="الطبيب")
    date = fields.Date(default=lambda self: fields.Date.context_today(self), string="التاريخ")
    hospital_product_type = fields.Selection(related='product_id.hospital_product_type', store=True)
    available_in = fields.Selection(related='product_id.available_in', store=True)
    description = fields.Char(string="بيان")
    quantity = fields.Float(default=1, digits='Product Unit of Measure', string="الكمية")
    amount = fields.Float(default=0, digits='Product Price', store=True,string="القيمة")
    total = fields.Float(default=0, digits='Product Price', compute="compute_total_line_amount", store=True, string="اجمالي")
    section_id = fields.Many2one('res.sections', string="القسم" )

    @api.depends('product_id', 'hospital_product_type', 'doctor_id', 'patient_account', 'contract_company')
    def get_amount(self):
        for rec in self:
            rec.amount = 0
            if rec.available_in == 'laboratory':
                if rec.patient_account == 'cash':
                    doc_service = self.env['doctor.services'].search([('service_id', '=', rec.product_id.id),
                                                                      ('doctor_id', '=', rec.doctor_id.id),
                                                                      ('patient_account', '=', 'cash')], limit=1)
                    rec.amount = doc_service.amount if doc_service else rec.product_id.list_price
                elif rec.patient_account == 'contract':
                    service = self.env['insurance.contractor.lines'].search([('service_id', '=', rec.product_id.id),
                                                                      ('partner_id', '=', rec.contract_company.id)], limit=1)
                    rec.amount = service.price if service else rec.product_id.list_price

    @api.onchange('product_id')
    def onchange_product(self):
        account = self.env['product.template'].sudo().browse(self.product_id.id)._get_product_accounts()
        self.account_id = account["income"].id
        self.doctor_id = self.clinic_visit_id.doctor_id.id if self.product_id.hospital_product_type not in ('medicament', 'consumable') else False

    @api.depends('quantity', 'amount')
    def compute_total_line_amount(self):
        for rec in self:
            rec.total = 0
            if rec.quantity and rec.amount:
                rec.total = rec.amount * rec.quantity