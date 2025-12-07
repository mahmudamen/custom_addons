
from odoo import models, fields, api, _
from odoo.exceptions import UserError





class ExternalLaboratoryPrice(models.Model):
    _name = 'lab.external.price'
    _description = 'External Laboratory Price List'

    laboratory_id = fields.Many2one('res.partner', domain=[('is_laboratory', '=', True)],string="المختبر", required=True)
    test_id = fields.Many2one('lab.test', string="التحليل", required=True)
    price = fields.Float(string="السعر", required=True)
    notes = fields.Text(string="ملاحظات")


class LabRequest(models.Model):
    _inherit = 'lab.request'

    is_external = fields.Boolean(string="تحويل خارجي", default=False, tracking=True)
    external_laboratory_id = fields.Many2one('res.partner', string="المختبر الخارجي", tracking=True)
    external_status = fields.Selection([
        ('draft', 'مسودة'),
        ('sent', 'تم الإرسال'),
        ('received', 'تم الاستلام'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي')
    ], string="حالة التحويل", default='draft', tracking=True)
    external_reference = fields.Char(string="الرقم المرجعي الخارجي", tracking=True)
    shipping_date = fields.Datetime(string="تاريخ الإرسال", tracking=True)
    expected_return_date = fields.Datetime(string="تاريخ الاستلام المتوقع", tracking=True)
    actual_return_date = fields.Datetime(string="تاريخ الاستلام الفعلي", tracking=True)
    shipping_notes = fields.Text(string="ملاحظات الشحن", tracking=True)
    result_notes = fields.Text(string="ملاحظات النتائج", tracking=True)
    external_cost = fields.Float(string="التكلفة الخارجية", compute='_compute_external_cost', store=True)

    @api.depends('external_laboratory_id', 'line_ids.lab_test_id')
    def _compute_external_cost(self):
        for record in self:
            total_cost = 0.0
            if record.is_external and record.external_laboratory_id:
                for line in record.line_ids:
                    price_record = self.env['lab.external.price'].search([
                        ('laboratory_id', '=', record.external_laboratory_id.id),
                        ('test_id', '=', line.lab_test_id.id)
                    ], limit=1)
                    if price_record:
                        total_cost += price_record.price
            record.external_cost = total_cost

    def send_to_external_lab(self):
        self.ensure_one()
        if not self.external_laboratory_id:
            raise UserError(_("يجب تحديد المختبر الخارجي أولاً"))

        self.write({
            'external_status': 'sent',
            'shipping_date': fields.Datetime.now(),
        })
        return True

    def receive_from_external_lab(self):
        self.ensure_one()
        if self.external_status != 'sent':
            raise UserError(_("لا يمكن استلام نتائج تحاليل لم يتم إرسالها"))

        self.write({
            'external_status': 'received',
            'actual_return_date': fields.Datetime.now(),
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _("إدخال نتائج التحاليل الخارجية"),
            'res_model': 'lab.request',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }

    def complete_external_process(self):
        self.ensure_one()
        if self.external_status != 'received':
            raise UserError(_("لا يمكن إكمال العملية قبل استلام النتائج"))

        # Verify all results are entered
        for line in self.line_ids:
            if not line.result_ids:
                raise UserError(_("يجب إدخال جميع نتائج التحاليل قبل إكمال العملية"))

        self.write({
            'external_status': 'completed',
        })
        return True

    def cancel_external_process(self):
        self.ensure_one()
        self.write({
            'external_status': 'cancelled',
        })
        return True
