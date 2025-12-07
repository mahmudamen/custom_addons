
from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date, formatLang

class AccountPayment(models.Model):
    _name = "account.payment.cash"
    _inherit = ['mail.thread.main.attachment', 'mail.activity.mixin']
    _description = "Cash in out"
    _order = "date desc, name desc"

    name = fields.Char(required=True, string="الاسم", translate=True, tracking=True)
    date = fields.Date(default=lambda self: fields.Date.today(), tracking=True, string="تاريخ الخدمة")
    amount = fields.Monetary(currency_field='currency_id')
    payment_type = fields.Selection([
        ('outbound', 'Send'),
        ('inbound', 'Receive'),
    ], string='Payment Type', default='inbound', readonly=True,required=True, tracking=True)
    partner_type = fields.Selection([
        ('customer', 'Customer'),
        ('supplier', 'Vendor'),
    ], default='customer',readonly=True ,tracking=True , required=True)
    payment_reference = fields.Char(string="Payment Reference", copy=False, tracking=True,
        help="Reference of the document used to issue this payment. Eg. check number, file name, etc.")
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        compute='_compute_currency_id', store=True, readonly=False, precompute=True,
        help="The payment's currency.")
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer/Vendor",
        store=True, readonly=False, ondelete='restrict',
        domain="['|', ('parent_id','=', False), ('is_company','=', True)]",
        tracking=True)
    outstanding_account_id = fields.Many2one(
        comodel_name='account.account',
        string="Outstanding Account",
        store=True,
        default=lambda self: self._get_default_outstanding_account())
    destination_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Destination Account',
        store=True, readonly=False,
        domain="[('account_type', 'in', ('asset_receivable', 'liability_payable'))]",
        default=lambda self: self._get_default_destination_account())
    destination_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Destination Journal',
        domain="[('type', 'in', ('bank','cash'))]",
        default=lambda self: self._get_default_journal()
    )
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('confirmed', 'مؤكد'),
        ('settled', 'محصل'),
        ('cancelled', 'ملغي')
    ], default='draft', string='الحالة', tracking=True)
    settlement_date = fields.Datetime(
        string='تاريخ التحصيل',
        readonly=True,
        tracking=True
    )
    payment_id = fields.Many2one('account.payment', string='Related Payment', readonly=True)
    account_payment_id = fields.Many2one(
        'account.payment',
        string='الدفعة المحاسبية',
        readonly=True
    )

    def action_preview_collection(self):
        """Open wizard to preview and select items to collect"""
        self.ensure_one()

        if self.state not in ['draft']:
            raise ValidationError(_("You can only collect orders in 'Draft' state."))

        return {
            'name': _('معاينة وتجميع العناصر'),
            'type': 'ir.actions.act_window',
            'res_model': 'cash.collection.preview.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_collection_id': self.id,
            }
        }

    # Override the confirm action to prevent manual confirmation if needed
    def action_confirm(self):
        """Confirm the cash payment"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft payments can be confirmed.'))

            # Optional: Check if it should be confirmed through collection only
            # if not record.cash_collection_id and self.env.context.get('require_collection', False):
            #     raise UserError(_('This payment must be confirmed through daily cash collection.'))

            # Validate required fields
            if not record.partner_id:
                raise UserError(_('Please select a partner.'))
            if not record.destination_journal_id:
                raise UserError(_('Please select a destination journal.'))
            if not record.amount:
                raise UserError(_('Please enter an amount.'))

            record.write({'state': 'confirmed'})
        return True

    @api.depends('destination_journal_id')
    def _compute_currency_id(self):
        for pay in self:
            pay.currency_id = pay.destination_journal_id.currency_id or pay.destination_journal_id.company_id.currency_id

    def _get_default_journal(self):
        """Get default journal from settings"""
        settings = self.env['res.config.settings'].sudo().create({})
        return settings.main_cash_journal

    def _get_default_partner(self):
        """Get default partner from settings"""
        settings = self.env['res.config.settings'].sudo().create({})
        return settings.cash_receivable_partner

    def _get_default_outstanding_account(self):
        """Get default outstanding account from settings"""
        settings = self.env['res.config.settings'].sudo().create({})
        return settings.main_cash

    def _get_default_destination_account(self):
        """Get default destination account from settings"""
        settings = self.env['res.config.settings'].sudo().create({})
        return settings.cash_receivable_acc

    @api.constrains('amount')
    def _check_amount(self):
        for payment in self:
            if payment.amount <= 0:
                raise ValidationError(_('The payment amount must be positive.'))

    def action_create_payment(self):
        """Create an account.payment record with the same data"""
        self.ensure_one()

        if self.state != 'confirmed':
            raise UserError(_('Only confirmed cash payments can create account payments.'))

        if self.payment_id:
            raise UserError(_('Payment already created for this record.'))

        # Prepare payment values
        payment_vals = {
            'payment_type': self.payment_type,
            'partner_type': self.partner_type,
            'partner_id': self.partner_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'date': self.date,
            'journal_id': self.destination_journal_id.id,
            'payment_reference': self.payment_reference or self.name,
            'ref': f"Cash Payment: {self.name}",
        }

        # Create the payment
        payment = self.env['account.payment'].create(payment_vals)

        # Link the payment to this record
        self.payment_id = payment.id

        # Optionally post the payment automatically
        # payment.action_post()

        # Update state to settled
        self.write({
            'state': 'settled',
            'settlement_date': fields.Datetime.now()
        })

        # Return action to view the created payment
        return {
            'type': 'ir.actions.act_window',
            'name': _('Payment'),
            'res_model': 'account.payment',
            'res_id': payment.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_cancel(self):
        """Cancel the cash payment"""
        for record in self:
            if record.state == 'settled':
                raise UserError(_('Cannot cancel a settled payment.'))
            if record.payment_id:
                raise UserError(_('Cannot cancel a payment that has an associated account payment.'))
            record.write({'state': 'cancelled'})
        return True

    def action_reset_to_draft(self):
        """Reset to draft state"""
        for record in self:
            if record.state == 'settled':
                raise UserError(_('Cannot reset a settled payment to draft.'))
            if record.payment_id:
                raise UserError(_('Cannot reset a payment that has an associated account payment.'))
            record.write({'state': 'draft'})
        return True

    @api.depends('destination_journal_id')
    def _compute_currency_id(self):
        for pay in self:
            pay.currency_id = pay.destination_journal_id.currency_id or pay.destination_journal_id.company_id.currency_id


    def action_settle(self):
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_('Only confirmed payments can be settled.'))
        self.write({
            'state': 'settled',
            'settlement_date': fields.Datetime.now()
        })



    @api.constrains('amount')
    def _check_amount(self):
        for payment in self:
            if payment.amount <= 0:
                raise ValidationError(_('The payment amount must be positive.'))

    @api.constrains('date')
    def _check_date(self):
        for payment in self:
            if payment.date > fields.Date.today():
                raise ValidationError(_('Payment date cannot be in the future.'))

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('account.payment.cash') or _('New')
        return super(AccountPayment, self).create(vals)

class LabTestResults(models.Model):
    _name = "lab.test.results"

    name = fields.Char()