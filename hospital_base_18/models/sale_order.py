from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    doctor = fields.Many2one('res.partner', domain=[('is_doctor', '=', True)], string="الطبيب")
    clinic_visit = fields.Many2one('clinic.visit')
    pharmacy_user = fields.Many2one('res.users')

    def print_receipt_confirm(self):
        # Make sure clinic_visit is set before proceeding
        if not self.clinic_visit:
            raise ValidationError(_("No clinic visit associated with this sale order."))

        # Prepare data for the report
        data = {
            'ids': self.ids,  # Pass the sale order IDs
            'model': self._name,  # 'sale.order'
            'clinic_visit_id': self.clinic_visit.id,
            'form': {
                'name': self.name,
                'patient': self.partner_id.name,
                'doctor': self.doctor.name if self.doctor else False,

            },
        }
        for i in self:
            i.action_confirm()

        # Return the report action
        return self.env.ref('hospital_base.report_receipt_report').report_action(self)

    def print_reception_receipt(self):
        if not self.clinic_visit:
            raise ValidationError(_("No clinic visit associated with this sale order."))

        data = {
            'clinic_visit_id': self.clinic_visit.id,
            'sale_order_id': self.id,
            'model': 'sale.order',
            'report_type': 'reception',
        }
        return self.env.ref('hospital_base.report_reception_receipt').report_action(self, data=data)

    def print_accounting_receipt(self):
        if not self.clinic_visit:
            raise ValidationError(_("No clinic visit associated with this sale order."))

        data = {
            'clinic_visit_id': self.clinic_visit.id,
            'sale_order_id': self.id,
            'model': 'sale.order',
            'report_type': 'accounting',
        }
        return self.env.ref('hospital_base.report_accounting_receipt').report_action(self, data=data)

    def print_pharmacy_receipt(self):
        if not self.clinic_visit:
            raise ValidationError(_("No clinic visit associated with this sale order."))

        data = {
            'clinic_visit_id': self.clinic_visit.id,
            'sale_order_id': self.id,
            'model': 'sale.order',
            'report_type': 'pharmacy',
        }
        return self.env.ref('hospital_base.report_pharmacy_receipt').report_action(self, data=data)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    dosage = fields.Char(string="الجرعة")
    dosage_id = fields.Many2one('visit.dosage', string="Dosage")
    duration_id = fields.Many2one('visit.duration', string="Duration")
