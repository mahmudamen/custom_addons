from odoo import models, fields, api, _
from odoo.exceptions import AccessError


class ResUsers(models.Model):
    _inherit = 'res.users'

    product_access_type = fields.Selection(
        selection=[
            ('all', 'All Products'),
            ('consumable', 'Consumable Products Only'),
            ('service', 'Service Products Only')
        ],
        string='Product Access Type',
        default='all'
    )


    odoobot_state = fields.Selection([
        ('not_initialized', 'Not initialized'),
        ('onboarding_emoji', 'Onboarding emoji'),
        ('onboarding_attachement', 'Onboarding attachment'),
        ('onboarding_command', 'Onboarding command'),
        ('onboarding_ping', 'Onboarding ping'),
        ('idle', 'Idle'),
        ('disabled', 'Disabled')
    ], string="OdooBot Status", default="not_initialized")




