from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date



class ClinicVisitWizard(models.TransientModel):
    _name = 'clinic.visit.wizard'
    _description = 'Clinic Visit Creation Wizard'

    # Step 1: Basic Visit Information
    step = fields.Selection([
        ('step1', 'معلومات الزيارة الأساسية'),
        ('step2', 'معلومات المريض'),
        ('step3', 'معلومات الطبيب والخدمة'),
        ('step4', 'معلومات مالية'),
        ('step5', 'مراجعة وتأكيد'),
    ], default='step1', string='الخطوة')

    # Step 1 Fields
    queue_number = fields.Integer(string="رقم الدور", required=True, default=1)
    reservation_date = fields.Datetime(string="تاريخ الحجز", default=fields.Datetime.now)
    date = fields.Date(string="تاريخ الخدمة", default=fields.Date.today)
    shift = fields.Selection([('morning', 'صباحا'), ('night', 'مساءا')], string="الشيفت")
    on_site = fields.Boolean(string="داخلي/خارجي", default=False)

    # Step 2 Fields - Patient Information
    patient_id = fields.Many2one('res.partner', domain=[('is_patient', '=', True)], string="المريض")
    patient_file = fields.Many2one('patient.file', string="ملف المريض")
    patient_nat_id = fields.Char(string="الرقم القومي")
    patient_phone = fields.Char(string="تليفون 1")
    patient_mobile = fields.Char(string="تليفون 2")
    patient_account = fields.Selection([
        ('cash', 'كاش'),
        ('insurance', 'تأمين'),
        ('contract', 'تعاقد'),
        ('company', 'شركة'),
    ], string="نوع الحساب")
    patient_employer = fields.Many2one('res.partner', string="الشركة التابع لها")
    patient_contract_company = fields.Many2one('res.partner', string="شركة التعاقد")

    # Step 3 Fields - Doctor and Service
    doctor_id = fields.Many2one('res.partner', domain=[('is_doctor', '=', True)], string="الطبيب")
    clinic_id = fields.Many2one('res.clinics', string="التخصص")
    service_id = fields.Many2one('doctor.services', string="الخدمة")
    product_id = fields.Many2one('product.product', string='Product')
    template_id = fields.Many2one('visit.template', string="قالب العيادة")

    # Step 4 Fields - Financial Information
    amount = fields.Float(string="القيمة", digits='Product Price')
    doctor_amount = fields.Float(string="أجر الطبيب", digits='Product Price')
    patient_per = fields.Float(string="نسبة التحمل", digits='Product Price')
    service_exp_amount = fields.Float(string="مصروفات ادارية", digits='Product Price')
    service_tax_amount = fields.Float(string="ضريبة", digits='Product Price')
    total_amount = fields.Float(string="الاجمالي", digits='Product Price', compute='_compute_total_amount')
    patient_amount = fields.Float(string="مطلوب من المريض", digits='Product Price')
    deposit_amount = fields.Float(string="أمانات")
    pay_deposit = fields.Boolean(string="دفع أمانات")

    # Additional Fields
    diagnosis = fields.Text(string="التشخيص")
    notes = fields.Text(string="ملاحظات")
    section_id = fields.Many2one('res.sections', string="القسم")

    # Computed Fields
    can_be_installment = fields.Boolean(related='product_id.can_be_installment', string="يمكن تقسيطها")
    doctor_shift = fields.Boolean(related="doctor_id.is_shift", string="شيفت")

    # Print Fields
    created_visit_id = fields.Many2one('clinic.visit', string="الزيارة المنشأة")

    @api.onchange('doctor_id')
    def _onchange_doctor_id(self):
        if self.doctor_id:
            self.clinic_id = self.doctor_id.clinic
            # Auto calculate queue number
            self.queue_number = self.patient_queue_number()
            return {'domain': {'service_id': [
                ('doctor_id', '=', self.doctor_id.id),
                ('detailed_type', '=', 'service'),
                ('hospital_product_type', '=', 'medical_service')
            ]}}
        else:
            return {'domain': {'service_id': [
                ('detailed_type', '=', 'service'),
                ('hospital_product_type', '=', 'medical_service')
            ]}}

    @api.depends('amount', 'service_exp_amount', 'service_tax_amount')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.amount + record.service_exp_amount + record.service_tax_amount

    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        if self.patient_id:
            self.patient_nat_id = self.patient_id.nat_id
            self.patient_phone = self.patient_id.phone
            self.patient_mobile = self.patient_id.mobile
            self.patient_account = self.patient_id.patient_account
            self.patient_employer = self.patient_id.employer
            self.patient_contract_company = self.patient_id.contract_company





    def patient_queue_number(self):
        """Calculate next queue number for the doctor"""
        if not self.doctor_id:
            return 1

        queue = self.doctor_id.start_from or 1
        max_queue = self.doctor_id.max_num or 0
        doctor = self.doctor_id
        shift = self.shift
        date = self.date

        current_queue = self.env["clinic.visit"].search([
            ('doctor_id', '=', doctor.id),
            ('date', '=', date),
            ('shift', '=', shift)
        ])

        if current_queue:
            check = max(current_queue.mapped('queue_number')) + 1
            if max_queue > 0:
                if check <= max_queue:
                    return check
                else:
                    raise ValidationError(_("تم الوصول لاقصي رقم ممكن"))
            else:
                return check
        return queue

    def compute_amounts(self):
        """Compute financial amounts based on service and patient account"""
        for rec in self:
            rec.doctor_amount = 0
            rec.amount = 0
            rec.service_exp_amount = 0
            rec.service_tax_amount = 0
            rec.total_amount = 0

            if rec.patient_account == 'cash' and rec.service_id:
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

            elif rec.patient_account == 'contract' and rec.service_id:
                if rec.patient_contract_company:
                    contract = self.env['insurance.contractor.lines'].search([
                        ('partner_id', '=', rec.patient_contract_company.id),
                        ('service_id', '=', rec.service_id.service_id.id),
                        ('active', '=', True)
                    ], limit=1)

                    if contract:
                        if not rec.pay_deposit:
                            rec.amount = contract.price
                            rec.doctor_amount = rec.service_id.doctor_amount
                            rec.service_exp_amount = contract.contract_id.exp_amount
                            rec.service_tax_amount = contract.contract_id.tax_amount
                            rec.total_amount = rec.amount + rec.service_exp_amount + rec.service_tax_amount
                            rec.patient_amount = rec.patient_per
                        else:
                            rec.amount = rec.service_id.amount
                            rec.patient_per = rec.service_id.amount
                            rec.doctor_amount = rec.service_id.doctor_amount
                            rec.service_exp_amount = rec.service_id.exp_amount
                            rec.service_tax_amount = rec.service_id.tax_amount
                            rec.total_amount = rec.amount + rec.service_exp_amount + rec.service_tax_amount
                            rec.deposit_amount = rec.total_amount
                            rec.patient_amount = rec.total_amount

    def action_next_step(self):
        """Move to next step"""
        steps = ['step1', 'step2', 'step3', 'step4', 'step5']
        current_index = steps.index(self.step)

        # Validate current step
        self._validate_current_step()

        if current_index < len(steps) - 1:
            self.step = steps[current_index + 1]

        return self._reopen_wizard()

    def action_previous_step(self):
        """Move to previous step"""
        steps = ['step1', 'step2', 'step3', 'step4', 'step5']
        current_index = steps.index(self.step)

        if current_index > 0:
            self.step = steps[current_index - 1]

        return self._reopen_wizard()

    def _validate_current_step(self):
        """Validate current step data"""
        if self.step == 'step1':
            if not self.queue_number:
                raise ValidationError(_('رقم الدور مطلوب'))
            if not self.date:
                raise ValidationError(_('تاريخ الخدمة مطلوب'))

        elif self.step == 'step2':
            if not self.patient_id:
                raise ValidationError(_('يجب اختيار المريض'))

        elif self.step == 'step3':
            if not self.doctor_id:
                raise ValidationError(_('يجب اختيار الطبيب'))
            if not self.service_id:
                raise ValidationError(_('يجب اختيار الخدمة'))

    def _reopen_wizard(self):
        """Reopen wizard with current step"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.visit.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def action_create_visit(self):
        """Create the clinic visit"""
        self._validate_all_steps()

        # Generate sequence
        name = self.env['ir.sequence'].next_by_code('clinic.visit') or '/'

        # Create clinic visit
        visit_vals = {
            'name': name,
            'queue_number': self.queue_number,
            'doctor_id': self.doctor_id.id,
            'shift': self.shift,
            'clinic_id': self.clinic_id.id,
            'patient_id': self.patient_id.id,
            'patient_file': self.patient_file.id if self.patient_file else False,
            'patient_account': self.patient_account,
            'patient_employer': self.patient_employer.id if self.patient_employer else False,
            'patient_contract_company': self.patient_contract_company.id if self.patient_contract_company else False,
            'patient_nat_id': self.patient_nat_id,
            'patient_phone': self.patient_phone,
            'patient_mobile': self.patient_mobile,
            'service_id': self.service_id.id,
            'product_id': self.product_id.id if self.product_id else False,
            'reservation_date': self.reservation_date,
            'date': self.date,
            'template_id': self.template_id.id if self.template_id else False,
            'diagnosis': self.diagnosis,
            'notes': self.notes,
            'doctor_amount': self.doctor_amount,
            'deposit_amount': self.deposit_amount,
            'pay_deposit': self.pay_deposit,
            'amount': self.amount,
            'patient_per': self.patient_per,
            'service_exp_amount': self.service_exp_amount,
            'service_tax_amount': self.service_tax_amount,
            'total_amount': self.total_amount,
            'patient_amount': self.patient_amount,
            'section_id': self.section_id.id if self.section_id else False,
            'on_site': self.on_site,
            'state': 'waiting',
        }

        visit = self.env['clinic.visit'].create(visit_vals)
        self.created_visit_id = visit.id

        return {
            'type': 'ir.actions.act_window',
            'name': _('زيارة العيادة'),
            'res_model': 'clinic.visit',
            'res_id': visit.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _validate_all_steps(self):
        """Validate all steps before creating visit"""
        if not self.patient_id:
            raise ValidationError(_('يجب اختيار المريض'))
        if not self.doctor_id:
            raise ValidationError(_('يجب اختيار الطبيب'))
        if not self.service_id:
            raise ValidationError(_('يجب اختيار الخدمة'))
        if not self.queue_number:
            raise ValidationError(_('رقم الدور مطلوب'))

    # Print Functions
    def print_clinic_report(self):
        """Print clinic report"""
        if not self.created_visit_id:
            raise ValidationError(_('يجب إنشاء الزيارة أولاً'))

        data = {
            'ids': [self.created_visit_id.id],
            'model': 'clinic.visit',
            'form': {
                'name': 'name'
            },
        }
        return self.env.ref('hospital_base.report_clinic_print_report').report_action(self.created_visit_id, data=data)

    def print_receipt_confirm(self):
        """Print receipt and create sale order"""
        if not self.created_visit_id:
            raise ValidationError(_('يجب إنشاء الزيارة أولاً'))

        data = {
            'ids': [self.created_visit_id.id],
            'model': 'clinic.visit',
            'form': {
                'name': 'name'
            },
        }
        self.create_sale_order_confirm()
        return self.env.ref('hospital_base.report_receipt_report').report_action(self.created_visit_id)

    def create_sale_order_confirm(self):
        """Create sale order with confirmation"""
        if not self.created_visit_id:
            return

        visit = self.created_visit_id
        if not visit.sales_order:
            val = {
                'partner_id': visit.patient_id.id,
                'doctor': visit.doctor_id.id,
                'clinic_visit': visit.id,
                'date_order': fields.Datetime.now()
            }
            sale_order = self.env['sale.order'].sudo().create(val)

            line = {
                'order_id': sale_order.id,
                'product_id': visit.product_id.product_variant_id.id,
                'product_template_id': visit.product_id.id,
                'name': visit.product_id.name,
                'dosage': 0,
                'product_uom_qty': 1,
                'price_unit': visit.patient_amount,
            }
            sale_order_line = self.env['sale.order.line'].sudo().create(line)

            visit.sales_order = sale_order.id
            self.env.cr.commit()
            sale_order.action_confirm()
            self.env.cr.commit()

    def print_reception_receipt(self):
        """Print reception receipt"""
        if not self.created_visit_id:
            raise ValidationError(_('يجب إنشاء الزيارة أولاً'))

        data = {
            'ids': [self.created_visit_id.id],
            'model': 'clinic.visit',
            'report_type': 'reception',
        }
        return self.env.ref('hospital_base.report_reception_receipt').report_action(self.created_visit_id, data=data)

    def print_accounting_receipt(self):
        """Print accounting receipt"""
        if not self.created_visit_id:
            raise ValidationError(_('يجب إنشاء الزيارة أولاً'))

        data = {
            'ids': [self.created_visit_id.id],
            'model': 'clinic.visit',
            'report_type': 'accounting',
        }
        return self.env.ref('hospital_base.report_accounting_receipt').report_action(self.created_visit_id, data=data)

    def print_pharmacy_receipt(self):
        """Print pharmacy receipt"""
        if not self.created_visit_id:
            raise ValidationError(_('يجب إنشاء الزيارة أولاً'))

        data = {
            'ids': [self.created_visit_id.id],
            'model': 'clinic.visit',
            'report_type': 'pharmacy',
        }
        return self.env.ref('hospital_base.report_pharmacy_receipt').report_action(self.created_visit_id, data=data)

    def print_receipt_direct(self):
        """Direct print receipt without preview"""
        if not self.created_visit_id:
            raise ValidationError(_('يجب إنشاء الزيارة أولاً'))

        visit = self.created_visit_id
        visit.print_count += 1
        print_type = "original" if visit.print_count == 1 else f"copy_{visit.print_count - 1}"

        data = {
            'ids': [visit.id],
            'model': 'clinic.visit',
            'form': {
                'name': visit.name,
                'print_type': print_type,
                'print_count': visit.print_count
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
        return


class ClinicVisitQuickWizard(models.TransientModel):
    _name = 'clinic.visit.quick.wizard'
    _description = 'Quick Clinic Visit Creation'

    patient_id = fields.Many2one('res.partner', domain=[('is_patient', '=', True)], string="المريض", required=True)
    doctor_id = fields.Many2one('res.partner', domain=[('is_doctor', '=', True)], string="الطبيب", required=True)
    service_id = fields.Many2one('doctor.services', string="الخدمة", required=True)
    queue_number = fields.Integer(string="رقم الدور", required=True, default=1)
    date = fields.Date(string="تاريخ الخدمة", default=fields.Date.today, required=True)
    notes = fields.Text(string="ملاحظات")

    clinic_id = fields.Many2one('res.clinics', related="doctor_id.clinic", string="التخصص")
    amount = fields.Float(related="service_id.total_amount", string="القيمة")

    def action_create_quick_visit(self):
        """Create quick clinic visit"""
        name = self.env['ir.sequence'].next_by_code('clinic.visit') or '/'

        visit_vals = {
            'name': name,
            'queue_number': self.queue_number,
            'doctor_id': self.doctor_id.id,
            'clinic_id': self.clinic_id.id,
            'patient_id': self.patient_id.id,
            'service_id': self.service_id.id,
            'date': self.date,
            'notes': self.notes,
            'amount': self.amount,
            'state': 'waiting',
        }

        visit = self.env['clinic.visit'].create(visit_vals)

        return {
            'type': 'ir.actions.act_window',
            'name': _('زيارة العيادة'),
            'res_model': 'clinic.visit',
            'res_id': visit.id,
            'view_mode': 'form',
            'target': 'current',
        }