
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResSections(models.Model):
    _inherit = 'res.sections'

    def get_doctors_action(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _("Doctors List"),
            'res_model': 'res.partner',
            'view_mode': 'list',
            'search_view_id': [self.env.ref('hospital_base.doctor_list_search_reception').id, 'search'],
            'views': [[self.env.ref('hospital_base.doctor_list_reception').id, "list"]],
            'target': 'new',
            'domain': [('is_doctor', '=', True)],
            'context': {'create': False}
        }

    def create_other_income_action(self):
        section = self.env['res.sections'].search([('type', '=', 'other')], limit=1)
        return {
            'type': 'ir.actions.act_window',
            'name': _("Other Income"),
            'res_model': 'clinic.visit',
            'view_mode': 'form',
            'views': [[self.env.ref('hospital_base.clinic_visit_other_form').id, "form"]],
            'target': 'new',
            'context': {'default_section_id': section.id if section else False}
        }
    def get_other_income_action(self):
        self.ensure_one()
        section = self.env['res.sections'].search([('type', '=', 'other')], limit=1)
        lines = self.env['clinic.visit'].search([('section_id', '=', section.id)])
        if lines:
            return {
                'type': 'ir.actions.act_window',
                'name': _("Other Income"),
                'res_model': 'clinic.visit',
                'view_mode': 'list',
                'domain': [('id', 'in', lines.ids)],
                'views': [[self.env.ref('hospital_base.clinic_visit_other_tree').id, "list"]],
                'target': 'target',
                'context': {'create': False, 'delete': False, 'duplicate': False, 'edit': False}
            }
        else:
            raise ValidationError("No Other Income")
    def create_nursing_service_action(self):
        section = self.env['res.sections'].search([('type', '=', 'nursing')], limit=1)
        return {
            'type': 'ir.actions.act_window',
            'name': _("Nursing Service"),
            'res_model': 'clinic.visit',
            'view_mode': 'form',
            'views': [[self.env.ref('hospital_base.clinic_visit_nursing_service_form').id, "form"]],
            'target': 'new',
            'context': {'default_section_id': section.id if section else False}
        }
    def create_lab_services_action(self):
        section = self.env['res.sections'].search([('type', '=', 'laboratory')], limit=1)
        return {
            'type': 'ir.actions.act_window',
            'name': _("Laboratory Service"),
            'res_model': 'clinic.visit',
            'view_mode': 'form',
            'views': [[self.env.ref('hospital_base.clinic_visit_lab_services_form').id, "form"]],
            'target': 'new',
            'context': {'default_section_id': section.id if section else False}
        }
    def get_nursing_service_action(self):
        self.ensure_one()
        section = self.env['res.sections'].search([('type', '=', 'nursing')], limit=1)
        lines = self.env['clinic.visit'].search([('section_id', '=', section.id)])
        if lines:
            return {
                'type': 'ir.actions.act_window',
                'name': _("Nursing Services"),
                'res_model': 'clinic.visit',
                'view_mode': 'list',
                'domain': [('id', 'in', lines.ids)],
                'views': [[self.env.ref('hospital_base.clinic_visit_nursing_service_tree').id, "list"]],
                'target': 'target',
                'context': {'create': False, 'delete': False, 'duplicate': False, 'edit': False}
            }
        else:
            raise ValidationError("No Nursing Services")
    def get_lab_services_action(self):
        self.ensure_one()
        section = self.env['res.sections'].search([('type', '=', 'laboratory')], limit=1)
        lines = self.env['clinic.visit'].search([('section_id', '=', section.id)])
        if lines:
            return {
                'type': 'ir.actions.act_window',
                'name': _("Laboratory Services"),
                'res_model': 'clinic.visit',
                'view_mode': 'list',
                'domain': [('id', 'in', lines.ids)],
                'views': [[self.env.ref('hospital_base.clinic_visit_lab_services_tree').id, "list"]],
                'target': 'target',
                'context': {'create': False, 'delete': False, 'duplicate': False, 'edit': False}
            }
        else:
            raise ValidationError("No Laboratory Services")
    def get_service_approves_action(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _("Approves"),
            'res_model': 'service.approval',
            'view_mode': 'list',
            'views': [[self.env.ref('hospital_base.reception_service_approval_tree').id, "list"]],
            'target': 'target',
            'domain': [('section_id', '=', self.id)],
        }
    def get_surgeries_list(self):
        date = fields.Date.context_today(self).strftime('%Y-%m-%d 00:00:00')
        action = self.env['ir.actions.act_window']._for_xml_id('hospital_base.surgeries_action')
        action['context'] = {'create': False, 'delete': False, 'duplicate': False}
        action['domain'] = [("date", ">=", date)]
        return action
    def get_catheterization_list(self):
        date = fields.Date.context_today(self).strftime('%Y-%m-%d 00:00:00')
        action = self.env['ir.actions.act_window']._for_xml_id('hospital_base.surgeries_action')
        action['context'] = {'create': False, 'delete': False, 'duplicate': False}
        action['domain'] = [("date", ">=", date)]
        return action
    def get_current_patient_action(self):
        action = self.env['ir.actions.act_window']._for_xml_id('hospital_base.reception_inpatient_action')
        action['context'] = {'create': False, 'delete': False, 'duplicate': False}
        action['domain'] = [('type', '=', 'inpatient'), ('state', '=', 'open')]
        return action
    def get_current_clinic_patient_action(self):
        action = self.env['ir.actions.act_window']._for_xml_id('hospital_base.reception_patient_clinic_action')
        action['context'] = {'create': False, 'delete': False, 'duplicate': False}
        #action['domain'] = [('type', '=', 'inpatient'), ('state', '=', 'open')]
        return action

    def get_radiology_requests_action(self):
        action = self.env['ir.actions.act_window']._for_xml_id('hospital_base.radiology_request_action')
        action['context'] = {'create': False, 'delete': False, 'duplicate': False}
        return action

    def get_beds_action(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _("Bed List"),
            'res_model': 'res.beds',
            'view_mode': 'list',
            'views': [[self.env.ref('hospital_base.reception_bed_list').id, "list"]],
            'target': 'new',
            'domain': [('state', '=', 'available')],
        }

    def get_laboratory_action(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _("Lab Service"),
            'res_model': 'lab.request',
            'view_mode': 'list',
            'views': [[self.env.ref('hospital_base.lab_request_tree').id, "list"],[self.env.ref('hospital_base.lab_request_form').id, "form"]],
            'target': 'target',
            'domain': [('reception_done', '=', False)],
        }


    def close_user_session(self):
        clinic_visit = self.env['clinic.visit']


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def clinic_reservation_action(self):
        doctor = self.env.context.get('doctor_id')
        section = self.env['res.sections'].search([('type', '=', 'clinic')], limit=1)
        return {
            'type': 'ir.actions.act_window',
            'name': _("Clinic Visit"),
            'res_model': 'clinic.visit',
            'view_mode': 'form',
            'views': [[self.env.ref('hospital_base.reception_clinic_visit_form').id, "form"]],
            'target': 'new',
            'context': {
                'default_doctor_id': doctor,
                'default_section_id': section.id if section else False
            }
        }


class CloseUserSession(models.Model):
    _name = 'close.user.session'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Close User Session'

    name = fields.Char(tracking=True, index=True, readonly=True, copy=False, default=lambda self: '/', string="الاسم")
    from_move = fields.Char(tracking=True, compute='get_from_to', store=True, string="من ايصال")
    to_move = fields.Char(tracking=True, compute='get_from_to', store=True, string="الي ايصال")
    actual_amount = fields.Float(default=0, digits='Product Price', tracking=True, required=True, string="ما تم تسليمه")
    req_amount = fields.Float(default=0, digits='Product Price', compute='get_from_to', store=True, tracking=True, required=True, string="المطلوب تسليمه")
    diff_amount = fields.Float(default=0, digits='Product Price', compute='compute_diff', store=True, tracking=True, required=True, string="الفرق")
    accounting_user_pin = fields.Char(required=True, size=5, tracking=True, string="كود مسئول الحسابات")
    reception_user_pin = fields.Char(required=True, size=5, tracking=True, string="كود الاستقبال")
    accounting_user = fields.Many2one('res.users', required=True, tracking=True, string="المحاسب")
    reception_user = fields.Many2one('res.users', required=True, tracking=True, string="مسئول الاستقبال")
    notes = fields.Char(string="ملاحظات")
    state = fields.Selection(selection=[('draft', 'Draft'), ('post', 'Posted'), ('income_posted', 'Income Posted'), ('cancel', 'Cancelled')],
                             default="draft",
                             required=False, )
    messages = fields.Char(string="الرسائل")
    show_message = fields.Boolean(default=False, string="اظهار الرسائل")
    move_id = fields.Many2one('account.move', string="رقم القيد")
    cash_id = fields.Many2one('account.move', string="قيد الخزينة")

    @api.onchange('accounting_user_pin', 'reception_user_pin')
    def onchange_user_pin(self):
        if self.accounting_user_pin:
            user = self.env['res.users'].search([('pin', '=', self.accounting_user_pin)], limit=1)
            if user:
                self.accounting_user = user.id
            else:
                self.accounting_user = False
                raise ValidationError(_('يرجي مراجعة الكود'))
        if self.reception_user_pin:
            user = self.env['res.users'].search([('pin', '=', self.reception_user_pin)], limit=1)
            if user:
                self.reception_user = user.id
            else:
                self.reception_user = False
                raise ValidationError(_('يرجي مراجعة الكود'))

    @api.depends('reception_user')
    def get_from_to(self):
        for rec in self:
            rec.from_move = False
            rec.to_move = False
            rec.req_amount = 0
            rec.diff_amount = 0
            user_moves = self.env['clinic.visit'].search([('create_uid', '=', rec.reception_user.id),
                                                          ('cash_posted', '=', False),
                                                          ('session_id', '=', False)])
            if user_moves:
                rec.from_move = str(min(user_moves.mapped('id')))
                rec.to_move = str(max(user_moves.mapped('id')))
                rec.req_amount = sum(user_moves.mapped('patient_amount'))

    @api.depends('req_amount', 'actual_amount')
    def compute_diff(self):
        for rec in self:
            rec.diff_amount = rec.actual_amount - rec.req_amount
            if rec.diff_amount < 0:
                rec.show_message = True
                rec.messages = "عجز"
            elif rec.diff_amount > 0:
                rec.messages = "زيادة"
                rec.show_message = True
            else:
                rec.messages = ""
                rec.show_message = False

    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            values['name'] = self.env['ir.sequence'].next_by_code('reception.close.session')
            result = super(CloseUserSession, self).create(values)
            return result

    def confirm_post(self):
        for rec in self:
            if rec.reception_user and rec.accounting_user:
                user_moves = self.env['clinic.visit'].search([('create_uid', '=', rec.reception_user.id),
                                                              ('cash_posted', '=', False),
                                                              ('session_id', '=', False)])
                if user_moves:
                    rec.state = 'post'
                    for move in user_moves:
                        move.cash_posted = True
                        move.session_id = rec.id
                        move.accounting_user = rec.accounting_user
                else:
                    raise ValidationError(_('لا يوجد قيد لتاكيده'))
            else:
                raise ValidationError(_('لا يوجد مستخدم'))

    def cancel_entry(self):
        for rec in self:
            if rec.reception_user and rec.accounting_user:
                user_moves = self.env['clinic.visit'].search([('create_uid', '=', rec.reception_user.id),
                                                              ('cash_posted', '=', True),
                                                              ('session_id', '=', rec.id)])
                if user_moves:
                    rec.state = 'cancel'
                    for move in user_moves:
                        move.cash_posted = False
                        move.session_id = False
                        move.accounting_user = False
                else:
                    raise ValidationError(_('لا يوجد قيد'))
            else:
                raise ValidationError(_('لا يوجد مستخدم'))

    def session_income(self):
        for rec in self:
            total_debit = 0
            total_credit = 0
            cash_total = 0
            service_exp_amount = 0
            service_tax_amount = 0
            move_lines = [(5, 0, 0)]
            cash_lines = [(5, 0, 0)]
            user_moves = self.env['clinic.visit'].search([('create_uid', '=', rec.reception_user.id),
                                                          ('cash_posted', '=', True),
                                                          ('session_id', '=', rec.id)])
            lines = user_moves.read_group([], fields=['patient_contract_company', 'product_id', 'total_amount',
                                                      'service_exp_amount', 'service_tax_amount', 'patient_amount'],
                                          groupby=['patient_contract_company', 'product_id'],lazy=False)
            for line in lines:
                service_exp_amount += line['service_exp_amount']
                service_tax_amount += line['service_tax_amount']
                cash_total += line['patient_amount']
                company = line['patient_contract_company']
                account = self.env['res.partner'].browse(company[0]).property_account_receivable_id.id if company else self.env.company.cash_receivable_acc.id
                move_val = (0, 0, {
                    "account_id": account,
                    "partner_id": self.env['res.partner'].browse(company[0]).id if company else self.env.company.cash_receivable_partner.id,
                    "debit": line['total_amount']
                })
                cash_val = (0, 0, {
                    "account_id": account,
                    "partner_id": self.env['res.partner'].browse(
                        company[0]).id if company else self.env.company.cash_receivable_partner.id,
                    "credit": line['patient_amount']
                })
                move_lines.append(move_val)
                cash_lines.append(cash_val)
                total_debit += line['total_amount']
                service = line['product_id']
                income_line = self.env['product.template'].browse(service[0])._get_product_accounts()
                income_val = (0, 0,{
                    "account_id": income_line["income"].id,
                    "credit": line['total_amount'] - line['service_exp_amount'] - line['service_tax_amount']
                })
                move_lines.append(income_val)
                total_credit += line['total_amount']

            service_exp_line = (0, 0, {
                "account_id": self.env.company.service_exp_account.id,
                "credit": service_exp_amount
            })
            move_lines.append(service_exp_line)
            service_tax_line = (0, 0, {
                "account_id": self.env.company.service_tax_account.id,
                "credit": service_tax_amount
            })
            move_lines.append(service_tax_line)
            due_entry = {
                'date': fields.Date.today(),
                'journal_id': self.env.company.reception_journal.id,
                'ref': _('قيد ايراد %s') % rec.name,
                'line_ids': move_lines
            }
            cash_lines.append((0, 0, {
                "account_id": self.env.company.main_cash.id,
                "debit": cash_total
            }))
            cash_entry = {
                'date': fields.Date.today(),
                'journal_id': self.env.company.main_cash_journal.id,
                'ref': _('قيد خزينة %s') % rec.name,
                'line_ids': cash_lines
            }
            entry_due = self.env["account.move"].create(due_entry)
            entry_due.action_post()
            rec.move_id = entry_due.id
            user_moves.write({'move_id': entry_due.id})
            entry_cash = self.env["account.move"].create(cash_entry)
            entry_cash.action_post()
            rec.cash_id = entry_cash.id





