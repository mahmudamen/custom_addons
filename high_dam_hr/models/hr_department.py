from odoo import fields, models, api


class hr_department(models.Model):
    _inherit = 'hr.department'
    _description = 'Description'

    assigned_user_ids = fields.Many2many(
        "res.users", string="Assigned users", tracking=True, translate=True,
        help="Restrict some users to only access their assigned operation types. "
             "In order to apply the restriction, the user needs the "
             "'User: Assigned department Only' group")
