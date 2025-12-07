
from odoo import models, fields, api

from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import UserError


class RadiologyRequest(models.Model):
    _name = 'radiology.request'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Radiology Request'

    name = fields.Char(tracking=True, index=True, readonly=True, copy=False, default=lambda self: '/', string="الاسم")
    date = fields.Date(default=lambda self: fields.Date.context_today(self), tracking=True, string="التاريخ")
    patient_id = fields.Many2one('res.partner', tracking=True, string="المريض")
    patient_account = fields.Selection(related="patient_id.patient_account",default="cash" , store=True, tracking=True,
                                       string="نوع الحساب")
    employer = fields.Many2one(related="patient_id.employer", store=True, tracking=True, string="الشركة التابع لها")
    contract_company = fields.Many2one(related="patient_id.contract_company", store=True, tracking=True,
                                       string="شركة التعاقد")
    doctor_id = fields.Many2one('res.partner', tracking=True, string="الطبيب")
    radiology_technician = fields.Many2one('res.partner', tracking=True, string="فني الاشعة")
    clinic_visit_id = fields.Many2one('clinic.visit')
    visit_id = fields.Many2one('clinic.visit')
    reception_done = fields.Boolean(default=False, tracking=True, string="تاكيد الاستقبال")
    service_id = fields.Many2one('product.template', domain=[('available_in', '=', 'radiology')], tracking=True,
                                 string="الخدمة")
    quantity = fields.Float(default=1, digits='Product Unit of Measure', string="العدد")
    state = fields.Selection(selection=[('waiting', 'Waiting'),
                                        ('done', 'Done'),
                                        ('cancelled', 'Cancelled')],
                             default="waiting", required=False, string="الحالة")
    note = fields.Text()
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', copy=False, readonly=True)

    def print_radiology_receipt(self):
        return self.env.ref('hospital_base.report_radiology_receipt_report').report_action(self)

    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            values['name'] = self.env['ir.sequence'].next_by_code('rad')
        result = super(RadiologyRequest, self).create(values)
        return result

    def action_done(self):
        for record in self:
            if not record.sale_order_id:
                # Create sale order
                record._create_sale_order()
            record.state = 'done'

    def action_cancel(self):
        self.state = 'cancelled'

    def action_reservation(self):
        self.state = 'waiting'

    def _create_sale_order(self):
        """Create a sale order from radiology request"""
        if not self.service_id:
            raise UserError('Please select a service before confirming the request')

        if not self.service_id.product_variant_id:
            raise UserError('The selected service does not have a product variant')

        # Create sale order
        sale_order_vals = {
            'partner_id': self.patient_id.id,
            'date_order': fields.Datetime.now(),
            'origin': self.name,
        }

        # Add doctor if field exists in sale order
        if hasattr(self.env['sale.order'], 'doctor'):
            sale_order_vals['doctor'] = self.doctor_id.id

        # Add clinic visit if field exists in sale order
        if hasattr(self.env['sale.order'], 'clinic_visit') and self.clinic_visit_id:
            sale_order_vals['clinic_visit'] = self.clinic_visit_id.id

        sale_order = self.env['sale.order'].sudo().create(sale_order_vals)

        # Create sale order line for the service
        line_vals = {
            'order_id': sale_order.id,
            'product_id': self.service_id.product_variant_id.id,
            'product_template_id': self.service_id.id,
            'name': self.service_id.name,
            'product_uom_qty': self.quantity,
            'product_uom': self.service_id.uom_id.id,
            # Use list price if no custom price is defined
            'price_unit': self.service_id.list_price,
        }

        self.env['sale.order.line'].sudo().create(line_vals)

        # Link the sale order to the radiology request
        self.sale_order_id = sale_order.id

        return sale_order

