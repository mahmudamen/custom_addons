

from odoo import models, fields, api, _
from datetime import datetime

import pytz


class ReportReceptionReceipt(models.AbstractModel):
    _name = 'report.hospital_base.report_receipt'
    _description = 'Print reception receipt'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})

        # Determine the report type (reception, accounting, etc.)
        report_type = data.get('report_type', 'reception')

        # Get clinic visit record
        visit = None

        # Case 1: Directly called from clinic.visit with docids
        if docids and not data.get('model'):
            visit = self.env['clinic.visit'].browse(docids[0])

        # Case 2: Called from data dictionary (from sale.order or elsewhere)
        elif data.get('clinic_visit_id'):
            visit = self.env['clinic.visit'].browse(data.get('clinic_visit_id'))

        # Case 3: Called with clinic.visit ids in data
        elif data.get('ids') and data.get('model') == 'clinic.visit':
            visit = self.env['clinic.visit'].browse(data.get('ids')[0])

        if not visit:
            raise ValueError("No clinic visit found")

        # Get related sale order if needed
        sale_order = None
        if data.get('sale_order_id'):
            sale_order = self.env['sale.order'].browse(data.get('sale_order_id'))
        else:
            # Try to find sale order linked to this clinic visit
            sale_order = self.env['sale.order'].search([('clinic_visit', '=', visit.id)], limit=1)

        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)

        # Common data for all report types
        result = {
            'section_id': visit.section_id.type,
            'clinic_id': visit.clinic_id.name,
            'doctor_id': visit.doctor_id.name if visit.doctor_id else "",
            'queue_number': visit.queue_number,
            'patient_code': visit.patient_code,
            'patient_id': visit.patient_id.name,
            'service_id': visit.service_id.service_id.name if visit.service_id else "",
            'name': visit.name,
            'shift': 'صباحا' if visit.shift == 'morning' else 'مساءا',
            'date': visit.date,
            'patient_amount': visit.patient_amount - visit.service_exp_amount,
            'service_exp_amount': visit.service_exp_amount,
            'total_amount': visit.patient_amount,
            'patient_account': visit.patient_contract_company.name if visit.patient_account == 'contract' else 'نقدي',
            'employee_id': visit.create_uid.login,
            'print_date': pytz.utc.localize(fields.Datetime.now()).astimezone(local).strftime("%d/%m/%Y %I:%M %p"),
            'nursing_service': visit.nursing_service,
            'lab_services': visit.lab_services,
            'report_type': report_type,
            'sale_order': sale_order.name if sale_order else "",
        }

        # Add report-type specific data
        if report_type == 'reception':
            # Add reception-specific data
            result.update({
                'is_reception_copy': True,
                'report_type' : 'reception',
            })
        if report_type == 'accounting':
            # Add accounting-specific data
            result.update({
                'is_accounting_copy': True,
                'report_type' : 'accounting',
            })

        elif report_type == 'nursing':
            # Add nursing-specific data
            result.update({
                'is_nursing_copy': True,
                'report_type': 'nursing',
                # Add any pharmacy-specific fields here
            })
        elif report_type == 'laboratory':
            # Add nursing-specific data
            result.update({
                'is_lab_copy': True,
                'report_type': 'laboratory',
                # Add any pharmacy-specific fields here
            })

        return result