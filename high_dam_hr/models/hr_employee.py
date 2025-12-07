from odoo.exceptions import UserError
from odoo import fields, models, api, _
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Employee'

    @api.depends('birthday')
    def onchange_age(self):
        for rec in self:
            if rec.birthday:
                d1 = rec.birthday
                d2 = datetime.today().date()
                rd = relativedelta(d2, d1)
                rec.age = str(rd.years) + "y" + " " + str(rd.months) + "m" + " " + str(rd.days) + "d"
            else:
                rec.age = "No Date Of Birth!!"

    national_id = fields.Char(string="الرقم القومي", tracking=True, translate=True)
    ensure_id = fields.Char(string='الرقم التاميني', tracking=True, translate=True)
    code = fields.Char(string="كود الموظف", required=True, tracking=True, translate=True)
    age = fields.Char(compute=onchange_age, string="العمر", store=True, tracking=True)
    live = fields.Char(string='الاقامة', tracking=True, translate=True)
    dept = fields.Many2one('hr.dept', string='ادارة ', tracking=True)
    dept_center = fields.Many2one('hr.dept.center', string='ادارة مركزية', tracking=True)
    start_date = fields.Date(string='بدء العمل', tracking=True)
    hiring_date = fields.Date(string='تاريخ التعيين', tracking=True)
    default_date = fields.Date(string='التاريخ الفرضي', tracking=True)
    current_status = fields.Selection([('basic', 'اساسي'),
                                       ('mandate_in', 'منتدب داخلي الي الهيئة'),
                                       ('mandate_out', 'منتدب خارجي لجهة اخري'),
                                       ('loan_in', 'اعارة الي الهيئة'),
                                       ('loan_out', 'اعارة خارج الهيئة'),
                                       ('Appendix', 'ملحق'),
                                       ('stoped', 'متوقف عن العمل'),
                                       ('end', 'معاش  ')
                                       ],
                                      string="الحالة الحالية", default='basic', tracking=True, translate=True)
    job_type = fields.Selection([('manager', 'القيادية والاشرافية'),
                                 ('specialist', 'تخصصية'),
                                 ('user', 'فنية ومكتبية'),
                                 ('worker', 'حرفية وخدمات معاونة')],
                                string="نوع الوظيفة", tracking=True, translate=True)
    qualitative_group = fields.Many2one('hr.qualitative.group', string='المجموعة النوعية', tracking=True)
    stage_id = fields.Many2one('hr.stage', string='المستوي الوظيفي', tracking=True)
    stage_date_got = fields.Date(string='تاريخ الحصول علي المستوي الوظيفي', tracking=True)
    degree = fields.Many2one('hr.degree', string='المؤهل الدراسي', tracking=True)
    hi_degree = fields.Many2one('hr.hi.degree', string='الدراسات العليا', tracking=True)
    level_id = fields.Many2one('hr.level', string='المستوي الوظيفي', tracking=True)
    level_date_got = fields.Date(string='تاريخ الحصول عليها المستوي الوظيفي', tracking=True)
    military_status = fields.Many2one('hr.milirary', string='الموقف من التجنيد', tracking=True)
    job_name = fields.Char(string='المسمي الوظيفي', tracking=True)
    sufficiency_report = fields.One2many('hr.sufficiency.report', 'sufficiency_report_id', string='تقرير الكفاية',
                                         copy=True, readonly=True, tracking=True,
                                         states={'draft': [('readonly', False)]})
    rate_ids = fields.Many2many('hr.sufficiency.report', tracking=True)
    punch_ids = fields.Many2many('hr.punch.line', tracking=True)

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '%s / %s' % (rec.name, rec.department_id.name) + ' / ' + (
                ' (%s)' % rec.dept_center.name if rec.dept_center.name else 'لا توجد ادارة مركزية')))
        return result

    @api.onchange('national_id')
    def required_digits(self):
        if self.national_id:
            if len(self.national_id) == 14 and self.national_id.isnumeric():
                return print('true')
            else:
                raise UserError(_("يجب ان يكون الرقم القومي 14 رقما  %s" % self.national_id))

    def print_report(self):
        self.write({'rate_ids': False})

        last_id = self.env['hr.sufficiency.report'].search([('emp_id', '=', self.id)])
        max_val = []
        if last_id:
            for statement in last_id:
                max_val.append(int(statement.year))
            last_year = max(max_val)
            last_last_year = last_year - 1
            first = self.env['hr.sufficiency.report'].search([('emp_id', '=', self.id), ('year', '=', last_year)])
            second = self.env['hr.sufficiency.report'].search([('emp_id', '=', self.id), ('year', '=', last_last_year)])
            if first and second:
                self.rate_ids = [(4, first.id), (4, second.id)]
            self.punch_collect()
        return self.env.ref('high_dam_hr.action_emp_id_card').report_action(self)

    def punch_collect(self):
        self.write({'punch_ids': False})
        year = datetime.now().year
        last_id = self.env['hr.punch'].search([('emp_id', '=', self.id), ('year', '=', year)])
        if last_id.hr_punch_line_ids:
            for i in last_id.hr_punch_line_ids:
                self.punch_ids = [(4, i.id)]


class QualitativeGroup(models.Model):
    _name = 'hr.qualitative.group'
    _rec_name = 'qualitative_group'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    qualitative_group = fields.Char(string='المجموعة النوعية')
    assigned_user_ids = fields.Many2many(
        "res.users", string="Assigned users", tracking=True, translate=True,
        help="Restrict some users to only access their assigned operation types. "
             "In order to apply the restriction, the user needs the "
             "'User: Assigned department Only' group")


class Degree(models.Model):
    _name = 'hr.degree'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='المؤهل الدراسي', tracking=True, translate=True)


class Degree(models.Model):
    _name = 'hr.hi.degree'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='دراسات عليا', tracking=True, translate=True)


class Level(models.Model):
    _name = 'hr.level'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='المستوي الوظيفي', tracking=True, translate=True)


class Milirary(models.Model):
    _name = 'hr.milirary'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='الموقف من التجنيد', tracking=True, translate=True)


class Stage(models.Model):
    _name = 'hr.stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='الدرجة المالية', tracking=True, translate=True)


class Dept(models.Model):
    _name = 'hr.dept'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='ادارة عامة', default='ادارة', tracking=True)


class DeptCenter(models.Model):
    _name = 'hr.dept.center'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='ادارة مركزية', default='ادارة مركزية', tracking=True, translate=True)
