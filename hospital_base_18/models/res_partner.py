
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    patient_code = fields.Char(
        string='كود المريض',
        copy=False,
        readonly=True,
        index=True,
        tracking=True,
        help="Unique patient code"
    )
    old_patient_id = fields.Integer(default=1,string="old id furkan")
    company_type = fields.Selection(selection_add=[('insurance', 'شركة تعاقد'),
                                                   ('doctor', 'طبيب'),
                                                   ('patient', 'مريض'),
                                                   ('service_provider', 'مقدم خدمة')],
                                    ondelete={'insurance': 'cascade', 'doctor': 'cascade', 'patient': 'cascade'})
    is_doctor = fields.Boolean(string='طبيب', default=False,
                               help="Check if the contact is a doctor", tracking=True)
    is_patient = fields.Boolean(string='مريض', default=False,
                                help="Check if the contact is a patient", tracking=True)
    is_nurse = fields.Boolean(string='تمريض', default=False,
                                help="Check if the contact is a patient", tracking=True)
    is_worker = fields.Boolean(string='عامل', default=False,
                              help="Check if the contact is a patient", tracking=True)
    is_insurance = fields.Boolean(string='شركة تعاقد', default=False,
                                help="Check if the contact is Insurance Company", tracking=True)
    is_service_provider = fields.Boolean(string='مقدم خدمات', default=False,
                                  help="Check if the contact is Service Provider")
    is_laboratory = fields.Boolean(string='معمل خارجي',default=False,
                                  help="Check if the contact is laboratory Provider")
    code = fields.Char(compute="_compute_company_type",  tracking=True, string="كود")
    degree = fields.Many2one('doctor.degrees', tracking=True, string="الدرجة")
    surgery_tax = fields.Boolean(default=False, tracking=True, string="مصاريف ادارية")
    inpatient_discount = fields.Float(default=0, digits='Product Price', tracking=True, string="خصم الداخلي")
    clinic = fields.Many2one('res.clinics', tracking=True, string="التخصص")
    age = fields.Integer(string="العمر")
    gender = fields.Selection([('1', 'ذكر'),
                                        ('0', 'انثي')], tracking=True, string="الجنس")
    matstate = fields.Selection([('m', 'متزوج'),
                               ('s', 'اعزب')], tracking=True, string="الحالة الاجتماعية")
    patient_account = fields.Selection([('cash', 'Cash'),
                                        ('contract', 'Contract')],default="cash" , tracking=True, string="نوع الحساب")
    nat_id = fields.Char(size=14, tracking=True, string="الرقم القومي")
    work_at = fields.Char(string="العمل", tracking=True)
    job = fields.Char(string="العمل", tracking=True)
    hide_peppol_fields = fields.Boolean(string="hide_peppol_fields")
    employer = fields.Many2one('res.partner', domain="[('is_company', '=', True)]", tracking=True, string="الشركة التابع لها")
    contract_company = fields.Many2one('res.partner', domain="[('is_insurance', '=', True)]", tracking=True, string="شركة التعاقد")
    is_shift = fields.Boolean(default=False, tracking=True, string="شيفت")
    start_from = fields.Integer(default=1, tracking=True, string="بداية التسلسل")
    max_num = fields.Integer(default=0, tracking=True, string="أقصي تسلسل")
    state_id = fields.Many2one("res.country.state", string='المحافظة', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]",
                               default=lambda self: self.env.company.state_id, tracking=True)
    country_id = fields.Many2one('res.country', string='الدولة', ondelete='restrict',
                                 default=lambda self: self.env.company.country_id, tracking=True)
    lab_amount = fields.Float(default=0, digits='Product Price', tracking=True, string="نسبة التحاليل")
    rad_amount = fields.Float(default=0, digits='Product Price', tracking=True, string="نسبة الاشعة")
    in_amount = fields.Float(default=0, digits='Product Price', tracking=True, string="نسبة الداخلي")

    @api.depends('is_company')
    def _compute_company_type(self):
        for partner in self:
            partner.code = False
            if partner.is_company:
                partner.company_type = 'company'
            elif partner.is_doctor:
                partner.company_type = 'doctor'
            elif partner.is_patient:
                partner.code = self.env['ir.sequence'].next_by_code('pat')
                partner.company_type = 'patient'
            elif partner.is_insurance:
                partner.company_type = 'insurance'
            elif partner.is_service_provider:
                partner.company_type = 'service_provider'
            else:
                partner.company_type = 'person'

    def _write_company_type(self):
        for partner in self:
            if partner.is_company:
                partner.company_type = 'company'
            elif partner.is_doctor:
                partner.company_type = 'doctor'
            elif partner.is_patient:
                if not partner.code:
                    partner.code = self.env['ir.sequence'].next_by_code('pat')
                partner.company_type = 'patient'
            elif partner.is_insurance:
                partner.company_type = 'insurance'
            elif partner.is_service_provider:
                partner.company_type = 'service_provider'
            else:
                partner.company_type = 'person'

    @api.onchange('company_type')
    def onchange_company_type(self):
        if self.company_type == 'company':
            self.is_company = True
            self.is_doctor = False
            self.is_patient = False
            self.is_insurance = False
            self.is_service_provider = False
        elif self.company_type == 'doctor':
            self.is_company = False
            self.is_doctor = True
            self.is_patient = False
            self.is_insurance = False
            self.is_service_provider = False
        elif self.company_type == 'patient':
            self.is_company = False
            self.is_doctor = False
            self.is_patient = True
            self.is_insurance = False
            self.is_service_provider = False
        elif self.company_type == 'insurance':
            self.is_company = False
            self.is_doctor = False
            self.is_patient = False
            self.is_insurance = True
            self.is_service_provider = False
        elif self.company_type == 'service_provider':
            self.is_company = False
            self.is_doctor = False
            self.is_patient = False
            self.is_insurance = False
            self.is_service_provider = True
        else:
            self.is_company = False
            self.is_doctor = False
            self.is_patient = False
            self.is_insurance = False
            self.is_service_provider = False

    def open_doctor_services(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("hospital_base.doctor_service_action")
        action['domain'] = [('doctor_id', '=', self.id)]
        action['context'] = {'default_doctor_id': self.id,
                             'search_doctor_id': self.id}
        return action

    def open_services_list(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("hospital_base.accounting_clinic_visit_action")
        action['domain'] = [('doctor_id', '=', self.id)]
        action['context'] = {'default_doctor_id': self.id,
                             'search_doctor_id': self.id}
        return action

    def open_request_approves_list(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("hospital_base.service_approval_action")
        action['domain'] = [('patient_contract_company', '=', self.id)]
        action['context'] = {'default_patient_contract_company': self.id,
                             'search_patient_contract_company': self.id,
                             'create': False}
        return action


    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate patient code"""
        for vals in vals_list:
            if vals.get('is_patient') and not vals.get('patient_code'):
                vals['patient_code'] = self._generate_patient_code()
        return super().create(vals_list)

    def write(self, vals):
        """Override write to generate patient code when becoming a patient"""
        # If setting is_patient to True and no patient_code exists
        if vals.get('is_patient'):
            for record in self:
                if not record.patient_code:
                    vals['patient_code'] = self._generate_patient_code()

        # If setting is_patient to False, optionally clear patient_code
        elif vals.get('is_patient') is False:
            # Uncomment if you want to clear patient_code when not a patient
            # vals['patient_code'] = False
            pass

        return super().write(vals)

    def _generate_patient_code(self):
        """Generate unique patient code"""
        # Get the next sequence
        sequence = self.env['ir.sequence'].next_by_code('res.partner.patient') or '0001'

        # Format: PAC + sequence (e.g., PAC0001, PAC0002)
        patient_code = f"{sequence}"

        # Ensure uniqueness
        while self.search_count([('patient_code', '=', patient_code)]) > 0:
            sequence = self.env['ir.sequence'].next_by_code('res.partner.patient') or '0001'
            patient_code = f"{sequence}"

        return patient_code

    def name_get(self):
        """Override name_get to show patient_code + name for patients"""
        result = []
        for partner in self:
            if partner.is_patient and partner.patient_code:
                # Format: PAC0001 - Ahmed Hassan
                name = f"{partner.name}"
            else:
                name = partner.name
            result.append((partner.id, name))
        return result

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, order=None):
        """Override _name_search to search by multiple fields for patients"""
        if name and operator in ('ilike', 'like', '=', '=like', '=ilike'):
            args = args or []
            domain = args + [
                '|', '|', '|', '|', '|',
                ('name', operator, name),
                ('patient_code', operator, name),
                ('nat_id', operator, name),
                ('phone', operator, name),
                ('mobile', operator, name),
                ('email', operator, name),
            ]
            return self._search(domain, limit=limit, order=order, access_rights_uid=None)
        return super()._name_search(name, args, operator, limit, order=order)

    @api.depends('is_patient')
    def _compute_display_name(self):
        """Compute display name including patient code"""
        for partner in self:
            if partner.is_patient and partner.patient_code:
                partner.display_name = f"{partner.name}"
            else:
                super(ResPartner, partner)._compute_display_name()

    def action_generate_patient_code(self):
        """Action to generate patient code for existing patients without code"""
        for record in self:
            if record.is_patient and not record.patient_code:
                record.patient_code = self._generate_patient_code()
            elif not record.is_patient:
                raise ValidationError(_("Can only generate patient code for patients!"))
            elif record.patient_code:
                raise ValidationError(_("Patient already has a code: %s") % record.patient_code)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Patient code generated successfully!'),
                'type': 'success',
                'sticky': False,
            }
        }
