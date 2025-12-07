
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResRooms(models.Model):
    _name = 'res.rooms'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Rooms'

    name = fields.Char(required=True, string="الاسم")
    no_of_beds = fields.Integer(default=1, required=True, string="عدد الاسرة")
    floor = fields.Char(string='الدور')
    room_type = fields.Selection([
        ('general', 'عام'),
        ('surgeries', 'جراحة'),
        ('catheterization', 'قسطرة'),
        ('icu', 'وحدة عناية مركزة')],
        string='نوع الغرفة', required=True, default='general')
    room_capacity = fields.Selection([
        ('single', 'فردي'),
        ('double', 'مزدوج'),
        ('triple', 'ثلاثي')],
        string='سعة الغرفة', required=True, default='single')
    active = fields.Boolean(default=True)
    current_patients_count = fields.Integer(string="عدد المرضى الحاليين", compute="_compute_current_patients",
                                            store=True)
    is_available = fields.Boolean(string="متاحة", compute="_compute_is_available", store=True)
    bed_ids = fields.One2many('res.beds', 'room_id', string="الأسرة")

    @api.constrains('room_capacity', 'no_of_beds')
    def _check_capacity_and_beds(self):
        for room in self:
            if room.room_capacity == 'single' and room.no_of_beds < 1:
                raise ValidationError(_("Single rooms must have at least 1 bed."))
            elif room.room_capacity == 'double' and room.no_of_beds < 2:
                raise ValidationError(_("Double rooms must have at least 2 beds."))
            elif room.room_capacity == 'triple' and room.no_of_beds < 3:
                raise ValidationError(_("Triple rooms must have at least 3 beds."))

    @api.depends('bed_ids.state')
    def _compute_current_patients(self):
        for room in self:
            room.current_patients_count = len(room.bed_ids.filtered(lambda b: b.state == 'full'))

    @api.depends('room_capacity', 'current_patients_count')
    def _compute_is_available(self):
        for room in self:
            if room.room_capacity == 'single':
                room.is_available = room.current_patients_count < 1
            elif room.room_capacity == 'double':
                room.is_available = room.current_patients_count < 2
            elif room.room_capacity == 'triple':
                room.is_available = room.current_patients_count < 3
            else:
                room.is_available = False

    def action_view_beds(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Beds',
            'res_model': 'res.beds',
            'view_mode': 'kanban,list,form',
            'domain': [('room_id', '=', self.id)],
            'context': {'default_room_id': self.id},
            'target': 'current',
        }

class ResBeds(models.Model):
    _name = 'res.beds'
    _rec_name = 'name'
    _description = 'Beds'

    name = fields.Char(required=True, string="الاسم")
    room_id = fields.Many2one('res.rooms', required=True, string="الغرفة")
    service_id = fields.Many2one('product.template', required=True,
                                 domain=[('hospital_product_type', '=', 'accommodation')], string="الخدمة")
    state = fields.Selection([
        ('not_available', 'محجوز'),
        ('available', 'متاح'),
        ('full', 'ممتليء')], string='الحالة', default="available", copy=False)
    active = fields.Boolean(default=True)
    patient_id = fields.Many2one('res.partner', string="المريض الحالي", readonly=True)
    patient_file_id = fields.Many2one('patient.file', string="ملف المريض", readonly=True)

    _sql_constraints = [
        ('bed_room_uid_unique', 'unique (room_id, name)', 'لا يمكن تكرار رقم السرير داخل نفس الغرفة'),
    ]

    def add_new_patient(self):
        bed = self.env.context.get('bed_id')
        room = self.env.context.get('room_id')

        # Check if the bed is available
        bed_obj = self.browse(bed)
        if bed_obj.state != 'available':
            raise ValidationError(_("This bed is not available for new patients."))

        # Check if the room has reached its capacity

        #room_obj = self.env['res.rooms'].browse(room)
        #if not room_obj.is_available:
        #    raise ValidationError(_("This room has reached its capacity. Please choose another room."))

        return {
            'type': 'ir.actions.act_window',
            'name': _("New Inpatient"),
            'res_model': 'patient.file',
            'view_mode': 'form',
            'views': [[self.env.ref('hospital_base.inpatient_form').id, "form"]],
            'target': 'target',
            'context': {
                'default_bed_id': bed,
                'default_room_id': room,
                'default_type': 'inpatient'
            }
        }

    def mark_as_available(self):
        for bed in self:
            bed.state = 'available'
            bed.patient_id = False
            bed.patient_file_id = False

    def mark_as_not_available(self):
        for bed in self:
            bed.state = 'not_available'
            bed.patient_id = False
            bed.patient_file_id = False

