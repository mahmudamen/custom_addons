from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class PatientExitWizard(models.TransientModel):
    _name = 'patient.exit.wizard'
    _description = 'Patient Exit Report Wizard'

    patient_file_id = fields.Many2one('patient.file', string='Patient File', required=True)

    # Discharge Information
    date_out = fields.Date(string="تاريخ الخروج", required=True, default=fields.Date.today())
    discharge_condition = fields.Selection([
        ('improved', 'تحسن'),
        ('cured', 'شفي'),
        ('stable', 'مستقر'),
        ('transferred', 'محول'),
        ('deceased', 'متوفي'),
        ('against_advice', 'خروج ضد المشورة الطبية')
    ], string="حالة المريض عند الخروج", required=True)

    discharge_doctor = fields.Many2one('res.partner',
                                       domain=[('is_doctor', '=', True)],
                                       string="طبيب الخروج")

    discharge_summary = fields.Text(string="التوصيات الطبية",
                                    help="Summary of patient's treatment and recommendations")

    medications_on_discharge = fields.Text(string="الأدوية عند الخروج",
                                           help="Medications prescribed at discharge")

    follow_up_instructions = fields.Text(string="تعليمات المتابعة",
                                         help="Follow-up care instructions")

    next_appointment_date = fields.Date(string="موعد المتابعة التالي")

    discharge_notes = fields.Text(string="ملاحظات الخروج")

    # Display fields
    patient_name = fields.Char(related='patient_file_id.patient_id.name', string="اسم المريض", readonly=True)
    date_in = fields.Date(related='patient_file_id.date_in', string="تاريخ الدخول", readonly=True)
    doctor_name = fields.Char(related='patient_file_id.doctor_id.name', string="الطبيب المعالج", readonly=True)
    diagnosis = fields.Text(related='patient_file_id.diagnosis', string="التشخيص", readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        patient_file_id = self.env.context.get('active_id')
        if patient_file_id:
            patient_file = self.env['patient.file'].browse(patient_file_id)
            res.update({
                'patient_file_id': patient_file_id,
                'discharge_doctor': patient_file.doctor_id.id,
                'date_out': patient_file.date_out or fields.Date.today(),
            })
        return res

    def action_confirm_discharge(self):
        """Update patient file with discharge information and generate report"""
        self.ensure_one()

        if self.patient_file_id.state == 'closed':
            raise ValidationError("الملف مغلق بالفعل")

        # Update patient file with discharge information
        self.patient_file_id.write({
            'date_out': self.date_out,
            'discharge_condition': self.discharge_condition,
            'discharge_doctor': self.discharge_doctor.id,
            'discharge_summary': self.discharge_summary,
            'medications_on_discharge': self.medications_on_discharge,
            'follow_up_instructions': self.follow_up_instructions,
            'next_appointment_date': self.next_appointment_date,
            'discharge_notes': self.discharge_notes,
        })

        # Close the patient file
        self.patient_file_id.action_close()

        # Generate and return the exit report
        return self.env.ref('hospital_base.action_report_patient_exit').report_action(self.patient_file_id)

    def action_cancel(self):
        """Cancel the wizard without making changes"""
        return {'type': 'ir.actions.act_window_close'}