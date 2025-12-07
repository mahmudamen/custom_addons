
from odoo import models, fields, api, _


class LabTest(models.Model):
    _name = 'lab.test'
    _rec_name = 'name'
    _description = 'Lab Test'

    name = fields.Char(required=True, string="الاسم")
    product_id = fields.Many2one('product.template', required=True,
                                 domain=[('available_in', '=', 'laboratory')], string="التحليل")
    result = fields.Integer(string="النتيجة")
    active = fields.Boolean(default=True, string="الحالة")
    line_ids = fields.One2many("lab.test.lines", inverse_name="lab_test_id")


class LabTestLines(models.Model):
    _name = 'lab.test.lines'
    _rec_name = 'name'
    _description = 'Lab Test Lines'

    name = fields.Char(string="الاسم")
    note = fields.Char(string="ملاحظات")
    lab_test_id = fields.Many2one('lab.test', string="الاختبار")
    high = fields.Float(string="الحد الاعلي")
    low = fields.Float(string="الحد الادني")
    high_notes = fields.Char(string="ملاحظات تجاوز الحد الاعلي")
    low_notes = fields.Char(string="ملاحظات تجاوز الحد الادني")


class LabRequest(models.Model):
    _name = 'lab.request'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Lab Request'

    name = fields.Char(tracking=True, index=True, readonly=True, copy=False, default=lambda self: '/', string="الاسم")
    date = fields.Date(default=lambda self: fields.Date.context_today(self), tracking=True, string="التاريخ")
    patient_id = fields.Many2one('res.partner', tracking=True, string="المريض", domain=[('is_patient', '=', True)])
    doctor_id = fields.Many2one('res.partner', tracking=True, string="الطبيب", domain=[('is_doctor', '=', True)])
    laboratory_technician = fields.Many2one('res.partner', tracking=True, string="فني التحاليل")
    clinic_visit_id = fields.Many2one('clinic.visit', tracking=True, string="الخدمة")
    reception_done = fields.Boolean(default=False, tracking=True, string="تأكيد الاستقبال")
    line_ids = fields.One2many("lab.request.lines", inverse_name="lab_request_id", tracking=True)
    clinic_receipt_id = fields.Many2one('clinic.visit', tracking=True, string="الايصال")
    state = fields.Selection(selection=[('open', 'Open'),
                                        ('closed', 'Closed')], default="open", string="الحالة")

    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            values['name'] = self.env['ir.sequence'].next_by_code('lab')
            result = super(LabRequest, self).create(values)
            return result

    def create_reservation(self):
        self.ensure_one()
        section = self.env['res.sections'].search([('type', '=', 'laboratory')], limit=1)
        lines = [(5, 0, 0)]
        for rec in self.line_ids:
            val = (0, 0, {
                'product_id': rec.lab_test_id.product_id.id,
                'doctor_id': self.doctor_id.id,
                'section_id': section.id
            })
            lines.append(val)
        return {
            'type': 'ir.actions.act_window',
            'name': _("Clinic Visit"),
            'res_model': 'clinic.visit',
            'view_mode': 'form',
            'views': [[self.env.ref('hospital_base.clinic_visit_lab_form').id, "form"]],
            'target': 'new',
            'context': {
                'default_section_id': section.id if section else False,
                'default_patient_id': self.patient_id.id,
                'default_doctor_id': self.doctor_id.id,
                'default_lab_services': lines
            }
        }


class LabRequestLines(models.Model):
    _name = 'lab.request.lines'
    _description = 'Lab Request Lines'

    lab_test_id = fields.Many2one('lab.test', string="الاختبار")
    lab_request_id = fields.Many2one('lab.request', string="طلب التحليل")
    result_ids = fields.One2many("lab.request.results", inverse_name="lab_request_lines_id")


class LabRequestResults(models.Model):
    _name = 'lab.request.results'
    _description = 'Lab Request Results'

    lab_request_lines_id = fields.Many2one('lab.request.lines', string="الطلب")
    test_line_id = fields.Many2one('lab.test.lines', string="الاختبار")
    result = fields.Float(string="النتيجة")
    note = fields.Char(string="ملاحظات")
