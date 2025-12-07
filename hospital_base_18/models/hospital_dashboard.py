
from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class HospitalDashboard(models.Model):
    _name = 'hospital.dashboard'
    _description = 'Hospital Dashboard'

    @api.model
    def get_dashboard_data(self, filter_date='today'):
        def get_date_range(filter_type):
            today = datetime.now().date()
            if filter_type == 'today':
                return today, today
            elif filter_type == 'current_week':
                week_start = today - timedelta(days=today.weekday())
                return week_start, today
            elif filter_type == 'last_week':
                week_start = today - timedelta(days=today.weekday() + 7)
                week_end = week_start + timedelta(days=6)
                return week_start, week_end
            elif filter_type == 'current_month':
                month_start = today.replace(day=1)
                return month_start, today
            elif filter_type == 'last_month':
                last_month = today - relativedelta(months=1)
                month_start = last_month.replace(day=1)
                month_end = today.replace(day=1) - timedelta(days=1)
                return month_start, month_end

        start_date, end_date = get_date_range(filter_date)

        # Get Patient Statistics
        patients = self.env['res.partner'].search_count([
            ('is_patient', '=', True),
            ('create_date', '>=', start_date),
            ('create_date', '<=', end_date)
        ])

        # Get Room Statistics
        total_rooms = self.env['res.rooms'].search_count([])
        available_rooms = self.env['res.beds'].search_count([
            ('state', '=', 'available')
        ])
        occupied_rooms = total_rooms - available_rooms

        # Get Doctor Statistics
        doctors = self.env['res.partner'].search_count([
            ('is_doctor', '=', True)
        ])

        # Get Clinic Visit Statistics
        clinic_visits = self.env['clinic.visit'].search([
            ('date', '>=', start_date),
            ('date', '<=', end_date)
        ])

        total_sales = sum(clinic_visits.mapped('total_amount'))
        total_tax = sum(clinic_visits.mapped('service_tax_amount'))

        # Get Surgery Statistics
        surgeries = self.env['surgeries'].search_count([
            ('date', '>=', start_date),
            ('date', '<=', end_date)
        ])

        # Get Laboratory Statistics
        lab_requests = self.env['lab.request'].search_count([
            ('date', '>=', start_date),
            ('date', '<=', end_date)
        ])

        # Get Monthly Trend Data
        months_data = []
        for i in range(6):
            month_start = (datetime.now() - relativedelta(months=i)).replace(day=1)
            month_end = (month_start + relativedelta(months=1) - timedelta(days=1))

            month_visits = self.env['clinic.visit'].search_count([
                ('date', '>=', month_start),
                ('date', '<=', month_end)
            ])

            months_data.append({
                'month': month_start.strftime('%B'),
                'visits': month_visits
            })

        return {
            'kpis': {
                'patients': patients,
                'total_rooms': total_rooms,
                'available_rooms': available_rooms,
                'occupied_rooms': occupied_rooms,
                'doctors': doctors,
                'clinic_visits': len(clinic_visits),
                'total_sales': total_sales,
                'total_tax': total_tax,
                'surgeries': surgeries,
                'lab_requests': lab_requests
            },
            'trends': {
                'months_data': months_data
            }
        }
