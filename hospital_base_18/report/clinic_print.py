

from odoo import models, fields, api, _
from datetime import datetime
import pytz


class ReportReceptionReceipt(models.AbstractModel):
    _name = 'report.hospital_base.report_clinic_print'
    _description = 'Print clinic report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Generate values for clinic visit report.

        This passes the clinic visit record directly as 'docs' and 'o'
        to properly support t-field directives in templates.
        """
        data = dict(data or {})

        # Get the record id from data or docids
        visit_id = data.get('ids', [False])[0] if data.get('ids') else docids[0]
        visit = self.env['clinic.visit'].browse(visit_id)

        return {
            'doc_ids': [visit.id],
            'doc_model': 'clinic.visit',
            'docs': visit,
            'o': visit,  # Add this for compatibility with both approaches
            # Keep original context variables for backward compatibility
            'clinic_id': visit.clinic_id.name,
            'doctor_id': visit.doctor_id.name if visit.doctor_id else "",
            'patient_id': visit.patient_id.name,
            'patient_code':visit.patient_code,
            'service_id': visit.service_id.service_id.name,
            'diagnosis': visit.diagnosis,
            'date': visit.date,
            'date_next_visit': visit.date_next_visit,
            'medicament_lines': visit.medicament_lines,
            'laboratory_lines': visit.laboratory_lines,
            'radiology_lines': visit.radiology_lines
        }