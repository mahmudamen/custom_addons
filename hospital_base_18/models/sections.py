
from odoo import models, fields, api, _

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResSections(models.Model):
    _name = 'res.sections'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence'
    _description = 'Hospital Sections'

    name = fields.Char(required=True, translate=True, string="الاسم", tracking=True)
    sequence = fields.Integer(default=10, string="الترتيب", tracking=True)
    type = fields.Selection(
        selection=[
            ('clinic', 'عيادة'),
            ('inpatient', 'القسم الداخلي'),
            ('icu', 'العناية المركزة'),
            ('catheterization', 'القسطرة'),
            ('surgeries', 'العمليات'),
            ('laboratory', 'المختبر'),
            ('bloodbank', 'بنك الدم'),
            ('radiology', 'الأشعة'),
            ('nursing', 'التمريض'),
            ('pharmacy', 'الصيدلية'),
            ('other', 'أخرى')
        ],
        required=True,
        string="نوع القسم",
        tracking=True
    )
    journal_id = fields.Many2one(
        'account.journal',
        required=False,
        domain=[('type', '=', 'general')],
        string="اليومية",
        tracking=True
    )
    income_account_id = fields.Many2one(
        'account.account',
        domain=[('account_type', 'in', ('income', 'income_other'))],
        required=False,
        string="حساب الايراد",
        tracking=True
    )
    location_id = fields.Many2one(
        'stock.location',
        domain=[('usage', '=', 'internal')],
        string="المخزن",
        tracking=True
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string="مركز التكلفة",
        tracking=True
    )
    active = fields.Boolean(default=True, string="نشط", tracking=True)
    color = fields.Integer(string="Color", compute='_compute_color', store=True)

    # Additional fields for better management
    description = fields.Text(string="الوصف", tracking=True)
    manager_id = fields.Many2one('res.users', string="مدير القسم", tracking=True)
    staff_ids = fields.Many2many('res.users', string="موظفي القسم")

    # Statistics fields

    appointment_count = fields.Integer(string="عدد المواعيد", compute='_compute_statistics')
    # Computed fields for statistics
    staff_count = fields.Integer(string="عدد الموظفين", compute='_compute_staff_count')
    patient_count = fields.Integer(string="عدد المرضى", compute='_compute_patient_count')
    # Statistics fields
    current_patients_count = fields.Integer(string="المرضى الحاليين", compute='_compute_current_patients_count')
    today_patients_count = fields.Integer(string="مرضى اليوم", compute='_compute_today_patients_count')
    waiting_patients_count = fields.Integer(string="في الانتظار", compute='_compute_waiting_patients_count')
    total_revenue_today = fields.Float(string="إيرادات اليوم", compute='_compute_today_revenue')
    monthly_patients_count = fields.Integer(string="مرضى الشهر", compute='_compute_monthly_patients_count')

    _sql_constraints = [
        ('seq_name_uniq', 'unique (name)', 'لايمكن تكرار اسم القسم'),
    ]

    @api.depends('staff_ids')
    def _compute_staff_count(self):
        for record in self:
            record.staff_count = len(record.staff_ids)
    def _compute_current_patients_count(self):
        """Compute current patients based on section type"""
        for section in self:
            count = 0

            if section.type == 'clinic':
                # Current clinic patients (today's visits that are waiting or in progress)
                count = self.env['clinic.visit'].search_count([
                    #('section_id', '=', section.id),
                    ('date', '=', fields.Date.today()),
                    ('state', 'in', ['waiting', 'done']),
                    ('canceled', '=', False)
                ])

            elif section.type == 'inpatient':
                # Current inpatient files that are active
                count = self.env['patient.file'].search_count([
                    #('section_id', '=', section.id),
                    ('state', '=', 'open'),
                    ('date_out', '=', False)
                ])

            elif section.type == 'icu':
                # Current ICU patients
                count = self.env['patient.file'].search_count([
                    #('section_id', '=', section.id),
                    ('state', '=', 'open'),
                    ('date_out', '=', False),
                    ('room_id.room_type', '=', 'icu')
                ])

            elif section.type == 'laboratory':
                # Today's lab requests
                count = self.env['lab.request'].search_count([
                    #('section_id', '=', section.id),
                    ('date', '=', fields.Date.today()),
                    ('state', 'in', ['open', 'close'])
                ])

            elif section.type == 'radiology':
                # Today's radiology requests
                count = self.env['radiology.request'].search_count([
                    #('section_id', '=', section.id),
                    ('date', '=', fields.Date.today()),
                    ('state', 'in', ['waiting', 'done'])
                ])

            elif section.type == 'surgeries':
                # Today's surgeries
                count = self.env['surgeries'].search_count([
                    #('section_id', '=', section.id),
                    ('date_in', '=', fields.Date.today()),
                    ('state', 'in', ['waiting', 'confirmed'])
                ])

            elif section.type == 'nursing':
                # Today's nursing services
                count = self.env['nursing.services.line'].search_count([
                    #('section_id', '=', section.id),
                    ('date', '=', fields.Date.today()),
                    ('state', 'in', ['draft', 'confirmed'])
                ])

            section.current_patients_count = count
    def _compute_today_patients_count(self):
        """Compute today's total patients"""
        for section in self:
            count = 0

            if section.type == 'clinic':
                count = self.env['clinic.visit'].search_count([
                    #('section_id', '=', section.id),
                    ('date', '=', fields.Date.today()),
                    ('canceled', '=', False)
                ])

            elif section.type in ['inpatient', 'icu']:
                # New admissions today
                count = self.env['patient.file'].search_count([
                    #('section_id', '=', section.id),
                    ('date_in', '=', fields.Date.today())
                ])

            elif section.type == 'laboratory':
                count = self.env['lab.request'].search_count([
                    #('section_id', '=', section.id),
                    ('date', '=', fields.Date.today())
                ])

            elif section.type == 'radiology':
                count = self.env['radiology.request'].search_count([
                    #('section_id', '=', section.id),
                    ('date', '=', fields.Date.today())
                ])

            section.today_patients_count = count
    def _compute_waiting_patients_count(self):
        """Compute waiting patients count"""
        for section in self:
            count = 0

            if section.type == 'clinic':
                count = self.env['clinic.visit'].search_count([
                    #('section_id', '=', section.id),
                    ('date', '=', fields.Date.today()),
                    ('state', '=', 'waiting'),
                    ('canceled', '=', False)
                ])

            elif section.type == 'laboratory':
                count = self.env['lab.request'].search_count([
                    #('section_id', '=', section.id),
                    ('state', 'in', ['draft', 'confirmed'])
                ])

            elif section.type == 'radiology':
                count = self.env['radiology.request'].search_count([
                    #('section_id', '=', section.id),
                    ('state', 'in', ['draft', 'confirmed'])
                ])

            section.waiting_patients_count = count
    def _compute_today_revenue(self):
        """Compute today's revenue for the section"""
        for section in self:
            revenue = 0.0

            if section.type == 'clinic':
                visits = self.env['clinic.visit'].search([
                    #('section_id', '=', section.id),
                    ('date', '=', fields.Date.today()),
                    ('canceled', '=', False)
                ])
                revenue = sum(visits.mapped('total_amount'))

            # Add other section types as needed
            section.total_revenue_today = revenue
    def _compute_monthly_patients_count(self):
        """Compute this month's patients count"""
        for section in self:
            count = 0
            today = fields.Date.today()
            first_day = today.replace(day=1)

            if section.type == 'clinic':
                count = self.env['clinic.visit'].search_count([
                    #('section_id', '=', section.id),
                    ('date', '>=', first_day),
                    ('date', '<=', today),
                    ('canceled', '=', False)
                ])

            section.monthly_patients_count = count
    @api.depends('type')
    def _compute_color(self):
        color_map = {
            'clinic': 1,  # Red
            'inpatient': 2,  # Orange
            'icu': 3,  # Yellow
            'laboratory': 4,  # Light Blue
            'radiology': 5,  # Dark Blue
            'surgeries': 6,  # Magenta
            'nursing': 7,  # Cyan
            'pharmacy': 8,  # Green
            'other': 9  # Grey
        }
        for record in self:
            record.color = color_map.get(record.type, 0)
    def _compute_patient_count(self):
        for record in self:
            # Replace with actual patient count logic
            record.patient_count = 0
    def _compute_statistics(self):
        """Compute section statistics"""
        for record in self:
            # This is a placeholder - implement based on your actual models
            record.patient_count = 0
            record.appointment_count = 0
    def get_section_action(self):
        """Open section-specific views based on type"""
        self.ensure_one()

        # Define actions for each section type
        action_map = {
            'clinic': 'medical.action_clinic_appointments',
            'inpatient': 'medical.action_inpatient_admissions',
            'icu': 'medical.action_icu_patients',
            'surgeries': 'medical.action_surgery_operations',
            'laboratory': 'medical.action_lab_tests',
            'radiology': 'medical.action_radiology_scans',
            'pharmacy': 'medical.action_pharmacy_orders',
        }

        action_name = action_map.get(self.type)

        if action_name:
            action = self.env.ref(action_name, raise_if_not_found=False)
            if action:
                return action.read()[0]

        # Default action - show a list view of the section
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'res.sections',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }
    def action_view_journal(self):
        """View related journal"""
        self.ensure_one()
        if self.journal_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.journal',
                'view_mode': 'form',
                'res_id': self.journal_id.id,
                'target': 'current',
            }
    def action_view_income_account(self):
        """View income account"""
        self.ensure_one()
        if self.income_account_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.account',
                'view_mode': 'form',
                'res_id': self.income_account_id.id,
                'target': 'current',
            }
    def action_view_location(self):
        """View stock location"""
        self.ensure_one()
        if self.location_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.location',
                'view_mode': 'form',
                'res_id': self.location_id.id,
                'target': 'current',
            }
    def action_view_analytic_account(self):
        """View analytic account"""
        self.ensure_one()
        if self.analytic_account_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.analytic.account',
                'view_mode': 'form',
                'res_id': self.analytic_account_id.id,
                'target': 'current',
            }
    def toggle_active(self):
        """Toggle active status"""
        for record in self:
            record.active = not record.active
    @api.model
    def create(self, vals):
        """Override create to handle sequence"""
        if 'sequence' not in vals:
            # Get max sequence for the same type
            max_sequence = self.search([
                ('type', '=', vals.get('type', 'other'))
            ], order='sequence desc', limit=1)
            vals['sequence'] = max_sequence.sequence + 10 if max_sequence else 10

        # Log activity
        section = super(ResSections, self).create(vals)
        section.message_post(
            body=_("تم إنشاء قسم جديد: %s") % section.name,
            message_type='notification',
        )
        return section
    def write(self, vals):
        """Override write to track changes"""
        for record in self:
            old_values = {}
            if 'active' in vals:
                old_values['active'] = record.active
            if 'type' in vals:
                old_values['type'] = record.type
            if 'manager_id' in vals:
                old_values['manager_id'] = record.manager_id.name if record.manager_id else 'لا يوجد'

            result = super(ResSections, self).write(vals)

            # Log important changes
            if 'active' in vals and old_values.get('active') != vals['active']:
                status = 'تم تفعيل' if vals['active'] else 'تم إلغاء تفعيل'
                record.message_post(
                    body=_("%s القسم") % status,
                    message_type='notification',
                )

            if 'manager_id' in vals:
                new_manager = record.manager_id.name if record.manager_id else 'لا يوجد'
                record.message_post(
                    body=_("تم تغيير مدير القسم من %s إلى %s") % (old_values.get('manager_id', 'لا يوجد'), new_manager),
                    message_type='notification',
                )

        return result
    @api.constrains('sequence')
    def _check_sequence(self):
        """Check sequence is positive"""
        for record in self:
            if record.sequence < 0:
                raise ValidationError(_("الترتيب يجب أن يكون رقم موجب"))
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            # Get Arabic type name
            type_names = dict(self._fields['type'].selection)
            type_name = type_names.get(record.type, '')
            name = f"[{type_name}] {record.name}"
            result.append((record.id, name))
        return result
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None, order=None):
        """Enhanced name search"""
        args = args or []
        if name:
            # Search by name or type
            type_dict = dict(self._fields['type'].selection)
            matching_types = [k for k, v in type_dict.items() if name.lower() in v.lower()]

            if matching_types:
                args = ['|', ('name', operator, name), ('type', 'in', matching_types)] + args
            else:
                args = [('name', operator, name)] + args

        return self._search(args, limit=limit, order=order, access_rights_uid=name_get_uid)
