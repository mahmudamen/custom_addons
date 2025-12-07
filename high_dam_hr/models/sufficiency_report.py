from odoo import fields, models, api
from datetime import date, datetime


class SufficiencyReport(models.Model):
    _name = 'hr.sufficiency.report'
    _description = 'Description'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    emp_id = fields.Many2one('hr.employee', string="اسم الموظف", required=True, tracking=True)
    sufficiency_report_id = fields.Many2one('hr.employee', string='تقرير الكفاية',
                                            index=True, readonly=True, auto_join=True, ondelete="cascade",
                                            check_company=True, tracking=True, translate=True,
                                            help="تقرير الكفاية.")
    date = fields.Date(string='تاريخ', tracking=True, translate=True)
    year = fields.Char(string='عن العام', tracking=True, default=datetime.now().year, require=True, translate=True)
    national_id = fields.Char(string="الرقم القومي", tracking=True, store=True, related="emp_id.national_id",
                              translate=True)
    job_name = fields.Char(string='المسمي الوظيفي', store=True, tracking=True, related="emp_id.job_name",
                           translate=True)
    score = fields.Float(string='درجات العام الحالي', store=True, tracking=True, readonly=True, translate=True)
    hi_level = fields.Float(string='مرتبة تقرير اداء العام السابق', tracking=True, readonly=True, defualt=0.0,
                            translate=True)
    course_id = fields.Many2many('hr.course', store=True, tracking=True, string='الدورات الحاصل عليها', translate=True)
    partner_id = fields.Many2one(related='emp_id.parent_id', translate=True, store=True, tracking=True, string='المدير')
    department_id = fields.Many2one(related='emp_id.department_id', translate=True, store=True, tracking=True,
                                    string='القسم')
    qualitative_group = fields.Many2one(related='emp_id.qualitative_group', translate=True, store=True, tracking=True,
                                        string='المجموعة النوعية')
    sufficiency_report_line_ids = fields.One2many('hr.sufficiency.report.line', 'report_id', tracking=True,
                                                  translate=True)
    behavior_report_line_ids = fields.One2many('hr.behavior.report.line', 'report_id', tracking=True, translate=True)
    emp_name = fields.Many2one('hr.employee', string="اسم الموظف", tracking=True, translate=True)
    emp_job_name = fields.Char(string='المسمي الوظيفي', store=True, tracking=True, related="emp_name.job_name",
                               translate=True)
    emp_related = fields.Char(string='العلاقة بالموظف', store=True, tracking=True, translate=True)
    emp_rate = fields.Selection([('days', 'يومي'),
                                 ('weeks', 'اسبوعي'),
                                 ('month', 'شهري'),
                                 ('year', 'كل بضعة شهور')],
                                string="معدل التعامل مع الموظف", tracking=True, translate=True)
    state = fields.Selection(selection=[
        ('draft', 'درافت'),
        ('4', 'نموذج 4'),
        ('5', 'نموذج 5'),
        ('6', 'نموذج 6'),
        ('7', 'نموذج 7'),
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft', translate=True)

    @api.onchange('sufficiency_report_line_ids', 'behavior_report_line_ids')
    def _iscore_sum(self):
        t = 0
        for statement in self.sufficiency_report_line_ids:
            total = sum([line.amount for line in statement])
            t += total
        for statement in self.behavior_report_line_ids:
            total = sum([int(line.amount) for line in statement])
            t += total
        self.write({'score': t})

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, "عن العام : " + rec.year + " - " + str(rec.score) + " درجة "))
        return res

    def formal_four_cancel(self):
        for line in self.sufficiency_report_line_ids:
            line.unlink()
        for line in self.behavior_report_line_ids:
            line.unlink()
        self.write({'state': 'draft'})

    def formal_four(self):
        if not self.sufficiency_report_line_ids:
            list = self.env['hr.report.line'].search([('formal_four', '=', True)])
            line = self.env['hr.sufficiency.report.line']
            for i in list:
                print(i.name)
                line.create({'report_id': self.id, 'name': i.id})

        if not self.behavior_report_line_ids:
            list_beh = self.env['hr.behavior.line'].search([('formal_four', '=', True)])
            line_beh = self.env['hr.behavior.report.line']
            for i in list_beh:
                print(i.name)
                line_beh.create({'report_id': self.id, 'name': i.id})
        self.message_post(body='اضافة نموذج رقم اربعة')
        self.write({'state': '4'})

    def formal_five(self):
        if not self.sufficiency_report_line_ids:
            list = self.env['hr.report.line'].search([('formal_five', '=', True)])
            line = self.env['hr.sufficiency.report.line']
            for i in list:
                print(i.name)
                line.create({'report_id': self.id, 'name': i.id})

        if not self.behavior_report_line_ids:
            list_beh = self.env['hr.behavior.line'].search([('formal_five', '=', True)])
            line_beh = self.env['hr.behavior.report.line']
            for i in list_beh:
                print(i.name)
                line_beh.create({'report_id': self.id, 'name': i.id})
        self.message_post(body='اضافة نموذج رقم خمسة ')
        self.write({'state': '5'})

    def formal_six(self):
        if not self.sufficiency_report_line_ids:
            list = self.env['hr.report.line'].search([('formal_six', '=', True)])
            line = self.env['hr.sufficiency.report.line']
            for i in list:
                print(i.name)
                line.create({'report_id': self.id, 'name': i.id})

        if not self.behavior_report_line_ids:
            list_beh = self.env['hr.behavior.line'].search([('formal_six', '=', True)])
            line_beh = self.env['hr.behavior.report.line']
            for i in list_beh:
                print(i.name)
                line_beh.create({'report_id': self.id, 'name': i.id})
        self.message_post(body='اضافة نموذج رقم ستة')
        self.write({'state': '6'})

    def formal_seven(self):
        if not self.sufficiency_report_line_ids:
            list = self.env['hr.report.line'].search([('formal_seven', '=', True)])
            line = self.env['hr.sufficiency.report.line']
            for i in list:
                print(i.name)
                line.create({'report_id': self.id, 'name': i.id})

        if not self.behavior_report_line_ids:
            list_beh = self.env['hr.behavior.line'].search([('formal_seven', '=', True)])
            line_beh = self.env['hr.behavior.report.line']
            for i in list_beh:
                print(i.name)
                line_beh.create({'report_id': self.id, 'name': i.id})
        self.message_post(body='اضافة نموذج رقم سبعة')
        self.write({'state': '7'})


class Course(models.Model):
    _name = 'hr.course'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='الكورس')


class HrReportLine(models.Model):
    _name = 'hr.report.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='التقييم', tracking=True, translate=True)
    formal_four = fields.Boolean('نموذج رقم اربعة', tracking=True, translate=True)
    formal_five = fields.Boolean('نموذج رقم خمسة', tracking=True, translate=True)
    formal_six = fields.Boolean('نموذج رقم ستة', tracking=True, translate=True)
    formal_seven = fields.Boolean('نموذج رقم سبعة', tracking=True, translate=True)


class HrSufficiencyReportLine(models.Model):
    _name = 'hr.sufficiency.report.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    report_id = fields.Many2one('hr.sufficiency.report', tracking=True, translate=True, string="الاهداف الاستراتييجية")
    name = fields.Many2one('hr.report.line', string='التقييم', tracking=True, translate=True)
    amount = fields.Float(string='الدرجة', tracking=True, translate=True)
    remark = fields.Char(string='ملاحظات', tracking=True, translate=True)


class HrBehaviorLine(models.Model):
    _name = 'hr.behavior.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='التقييم', tracking=True, translate=True)
    formal_four = fields.Boolean('نموذج رقم اربعة', tracking=True, translate=True)
    formal_five = fields.Boolean('نموذج رقم خمسة', tracking=True, translate=True)
    formal_six = fields.Boolean('نموذج رقم ستة', tracking=True, translate=True)
    formal_seven = fields.Boolean('نموذج رقم سبعة', tracking=True, translate=True)


class HrBehaviorreportLine(models.Model):
    _name = 'hr.behavior.report.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    report_id = fields.Many2one('hr.sufficiency.report', tracking=True, string="الاهداف الاستراتييجية", translate=True)
    name = fields.Many2one('hr.behavior.line', tracking=True, string='مؤشر الكفاءة السلوكية', translate=True)
    amount = fields.Selection([('1', 'ضعيف'),
                               ('2', 'متوسط'),
                               ('3', 'فوق المتوسط'),
                               ('4', 'كفء'),
                               ('5', 'ممتاز'),
                               ('0', 'لاينطبق')],
                              string="الدرجة", tracking=True, translate=True)
    remark = fields.Char(string='ملاحظات', tracking=True, translate=True)
