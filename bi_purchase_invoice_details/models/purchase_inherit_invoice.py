# # -*- coding : utf-8 -*-
# # Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class PurchaseOrderUpdate(models.Model):
	_inherit = 'purchase.order'

	invoiced_amount = fields.Float(string = 'Invoiced Amount',compute ='_compute_invoiced_amount',compute_sudo=True)
	amount_due = fields.Float(string ='Amount Due', compute ='_computedue',compute_sudo=True)
	paid_amount = fields.Float(string ='Paid Amount', compute ='_computepaid',compute_sudo=True)
	amount_paid_percent = fields.Float(compute = 'action_amount_paid',compute_sudo=True)
	currency_id = fields.Many2one(
        comodel_name='res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

	@api.depends('paid_amount','invoiced_amount', 'amount_due')
	def _compute_invoiced_amount(self):
		for record in self:
			total = 0
			if self.invoice_ids:
				for bill in self.invoice_ids:
					total += bill.amount_total
					record.invoiced_amount = total
			else:
				record.invoiced_amount = total

	@api.depends('paid_amount','invoiced_amount', 'amount_due')
	def _computedue(self):
		for record in self:
			amount = 0
			if self.invoice_ids:
				for inv in self.invoice_ids:
					amount  += inv.amount_residual   
					record.amount_due = amount
			else:
				record.amount_due = amount

	@api.onchange('invoiced_amount', 'amount_due')
	def _computepaid(self):
		for record in self:
			record.paid_amount = record.invoiced_amount - record.amount_due

	@api.depends('paid_amount', 'invoiced_amount')
	def action_amount_paid(self):
		for res in self:
			if res.invoiced_amount != 0:
				res.amount_paid_percent = 100 * res.paid_amount / res.invoiced_amount
			else:
				res.amount_paid_percent = 0.0
		return res.amount_paid_percent
		