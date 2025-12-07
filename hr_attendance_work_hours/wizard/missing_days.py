# -*- coding: utf-8 -*-

from odoo import models, fields, _
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from pytz import timezone

class MissingDaysWizard(models.TransientModel):
    _name = 'missing.days.wizard'
    _description = 'Missing Days Wizard'
    
    from_date = fields.Date('From', required=True)
    to_date = fields.Date('To', required=True)
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    
    def open(self):
        days_range = (self.to_date-self.from_date).days + 1
        if self.employee_ids:
            employees = self.employee_ids
        else:
            employees = self.env['hr.employee'].search([])
        vals = []
        for emp in employees:
            tz = emp.tz or emp.resource_calendar_id.tz
            user_timezone = timezone(tz)
            if emp._get_contracts(self.from_date, self.to_date):
                day_id = self.from_date - timedelta(days=1)
                for x in range(days_range):
                    day_id = day_id + timedelta(days=1)
                    day_of_week = {'Monday':0 ,'Tuesday':1 ,'Wednesday':2 ,'Thursday':3 ,'Friday':4 ,'Saturday':5 ,'Sunday':6 }
                    days = emp.resource_calendar_id.attendance_ids.filtered(lambda d:d.dayofweek == str(day_of_week[day_id.strftime('%A')])).sorted(lambda x:x.sequence)
                    for day in days:
                        day_from_hour = day.hour_from
                        day_from_minutes = int((day.hour_from-int(day.hour_from)) * 60) 
                        day_to_hour = day.hour_to
                        day_to_minutes = int((day.hour_to-int(day.hour_to)) * 60) 
                        date = self.from_date + timedelta(days=x)
                        fdate = user_timezone.localize(datetime.strptime(datetime.strftime(date, '%Y-%m-%d  00:00:00'), DEFAULT_SERVER_DATETIME_FORMAT).replace(hour=int(day_from_hour),minute=day_from_minutes))
                        tdate = user_timezone.localize(datetime.strptime(datetime.strftime(date, '%Y-%m-%d  00:00:00'), DEFAULT_SERVER_DATETIME_FORMAT).replace(hour=int(day_to_hour),minute=day_to_minutes))
                        work_hours = emp._list_work_time_per_day(fdate,tdate, emp.resource_calendar_id, domain = [('time_type', 'in', ['leave', 'other'])])
                        fdate1 = user_timezone.localize(datetime.strptime(datetime.strftime(date, '%Y-%m-%d  00:00:00'), DEFAULT_SERVER_DATETIME_FORMAT))
                        tdate1 = user_timezone.localize(datetime.strptime(datetime.strftime(date, '%Y-%m-%d  23:59:59'), DEFAULT_SERVER_DATETIME_FORMAT))
                        attendance = self.env['hr.attendance'].search([('employee_id','=',emp.id),
                                                                       ('check_in','>',fdate1),
                                                                       ('check_out','<',tdate1)])
                        flag = False
                        for att in attendance:
                            check_in = timezone('UTC').localize(att.check_in).astimezone(user_timezone)
                            check_out = timezone('UTC').localize(att.check_out).astimezone(user_timezone)
                            if (check_in >= fdate and check_in <= tdate) or \
                                (check_in <= fdate and check_out >= fdate and check_out <= tdate) or \
                                (check_in <= fdate and check_out >= tdate) or \
                                (check_in >= fdate and check_out >= tdate and check_in <= tdate):
                                flag = True
                        if work_hours and work_hours[emp.id] and not flag:
                            hours = work_hours[emp.id][0][1]
                            vals.append({'employee_id': emp.id,
                                         'date': date,
                                         'day': date.strftime("%A"),
                                         'hours': hours,
                                         'day_period': day.day_period})
                    
        if vals:
            miss_att_obj = self.env['missing.days.report']
            miss_att_obj.search([]).unlink()
            miss_att_obj.create(vals)
            return {
                    'name': _('Missing Attendance'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'list',
                    'res_model': 'missing.days.report',
                    'view_id': self.env.ref('hr_attendance_work_hours.missing_days_tree_view').id
                }
        else:
            miss_att_obj = self.env['missing.days.report']
            miss_att_obj.search([]).unlink()
            return {
                    'name': _('Missing Attendance'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'list',
                    'res_model': 'missing.days.report',
                    'view_id': self.env.ref('hr_attendance_work_hours.missing_days_tree_view').id
                }
    
    
class MissingDaysReport(models.Model):
    _name = 'missing.days.report'
    _description = 'Missing Days Report'
    _rec_name = 'employee_id'
    _order = 'date desc,employee_id , day_period asc'
    
    employee_id = fields.Many2one('hr.employee', 'Employee')
    date = fields.Date('Date')
    day = fields.Char('Day')
    hours = fields.Float('Missing Hours')
    day_period = fields.Selection([('morning', 'Morning'), ('afternoon', 'Afternoon')])
    