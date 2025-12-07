from odoo import fields, models, api
from datetime import date, datetime


class HrPunch(models.Model):
    _name = 'hr.punch'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'hr punch'

    emp_id = fields.Many2one('hr.employee', string="اسم الموظف", required=True, tracking=True, translate=True)
    date = fields.Date(string='تاريخ', tracking=True, translate=True)
    year = fields.Char(string='عن العام', default=datetime.now().year, tracking=True, translate=True)
    national_id = fields.Char(string="الرقم القومي", store=True, related="emp_id.national_id", tracking=True,
                              translate=True)
    job_name = fields.Char(string='المسمي الوظيفي', store=True, related="emp_id.job_name", tracking=True,
                           translate=True)
    partner_id = fields.Many2one(related='emp_id.parent_id', store=True, string='المدير', tracking=True, translate=True)
    department_id = fields.Many2one(related='emp_id.department_id', store=True, string='القسم', tracking=True,
                                    translate=True)
    qualitative_group = fields.Many2one(related='emp_id.qualitative_group', store=True, string='المجموعة النوعية',
                                        tracking=True, translate=True)
    hr_punch_line_ids = fields.One2many('hr.punch.line', 'punch_id', tracking=True, translate=True)


class HrPunchLine(models.Model):
    _name = 'hr.punch.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'type'

    punch_id = fields.Many2one('hr.punch', string="الجزاءات", tracking=True, translate=True)
    num_resolution = fields.Char('رقم القرار', tracking=True, translate=True)
    date = fields.Date('تاريخ الجزاء', tracking=True, translate=True)
    type = fields.Char(string='نوع الجزاء', tracking=True, translate=True)
    field_name = fields.Binary(string="صورة القرار", attachment=True, tracking=True, translate=True)
