
from odoo import models, fields, api, _


class ResClinics(models.Model):
    _name = 'res.clinics'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Clinics'

    name = fields.Char(required=True, translate=True, string="الاسم")
    active = fields.Boolean(default=True, string="الحالة")
