
from odoo import models, fields, api, _
from datetime import datetime
import pytz


class ReportRadiologyReceipt(models.AbstractModel):
    _name = 'report.hospital_base.report_radiology_receipt'
    _description = 'Print radiology receipt'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})

        # Get radiology request record
        radiology_request = None

        # Case 1: Directly called with docids
        if docids and not data.get('model'):
            radiology_request = self.env['radiology.request'].browse(docids[0])

        # Case 2: Called from data dictionary
        elif data.get('radiology_request_id'):
            radiology_request = self.env['radiology.request'].browse(data.get('radiology_request_id'))

        # Case 3: Called with ids in data
        elif data.get('ids') and data.get('model') == 'radiology.request':
            radiology_request = self.env['radiology.request'].browse(data.get('ids')[0])

        if not radiology_request:
            raise ValueError("No radiology request found")

        # User timezone handling
        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)

        # Prepare data for the report
        result = {
            'name': radiology_request.name,
            'date': radiology_request.date,
            'patient_id': radiology_request.patient_id,
            'patient_code': radiology_request.patient_code,
            'doctor_id': radiology_request.doctor_id,
            'radiology_technician': radiology_request.radiology_technician,
            'service_id': radiology_request.service_id,
            'quantity': radiology_request.quantity,
            'state': radiology_request.state,
            'patient_account': radiology_request.patient_account,
            'employer': radiology_request.employer,
            'contract_company': radiology_request.contract_company,
            'note': radiology_request.note,
            'sale_order_id': radiology_request.sale_order_id,
            'print_date': pytz.utc.localize(fields.Datetime.now()).astimezone(local).strftime("%d/%m/%Y %I:%M %p"),
        }

        return result
