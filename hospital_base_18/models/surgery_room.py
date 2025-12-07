from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class SurgeryRoom(models.Model):
    _name = 'surgery.room'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Surgery Rooms'
    _order = 'name'

    name = fields.Char(string="Room Name", required=True, tracking=True)
    room_type = fields.Selection([
        ('general', 'General Surgery'),
        ('cardiac', 'Cardiac Surgery'),
        ('orthopedic', 'Orthopedic Surgery'),
        ('specialized', 'Specialized Surgery')
    ], string='Surgery Room Type', required=True, default='general', tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    location = fields.Char(string='Location/Floor', tracking=True)
    notes = fields.Text(string='Notes')
    color = fields.Integer(string='Color Index')
    is_available_now = fields.Boolean(
        string="Available Now",
        compute="_compute_is_available_now",
        store=False,
        help="Indicates if the room is currently free (no ongoing surgery)"
    )
    surgery_slot_ids = fields.One2many('surgery.slot', 'room_id', string='Surgery Slots')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    # For the kanban/form stat button
    surgery_slot_count = fields.Integer(compute='_compute_surgery_slot_count', string="Surgery Count")
    upcoming_surgery_count = fields.Integer(compute='_compute_surgery_slot_count', string="Upcoming Surgeries")

    def _compute_is_available_now(self):
        """Check if room is currently available (no active surgery)"""
        now = fields.Datetime.now()
        for room in self:
            active_surgery_now = room.surgery_slot_ids.filtered(
                lambda slot: slot.state in ('confirmed', 'in_progress') and
                             slot.start_datetime <= now and
                             slot.end_datetime >= now
            )
            room.is_available_now = not bool(active_surgery_now)

    @api.depends('surgery_slot_ids', 'surgery_slot_ids.state', 'surgery_slot_ids.start_datetime')
    def _compute_surgery_slot_count(self):
        """Count total and upcoming surgeries for this room"""
        for room in self:
            room.surgery_slot_count = len(room.surgery_slot_ids)

            # Count upcoming surgeries (those in draft or confirmed state that haven't started yet)
            upcoming_slots = room.surgery_slot_ids.filtered(
                lambda s: s.state in ('draft', 'confirmed') and
                          s.start_datetime >= fields.Datetime.now()
            )
            room.upcoming_surgery_count = len(upcoming_slots)

    def action_view_surgery_slots(self):
        """Action to view surgeries for this room"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Surgeries in %s') % self.name,
            'res_model': 'surgery.slot',
            'view_mode': 'calendar,list,form,kanban',
            'domain': [('room_id', '=', self.id)],
            'context': {
                'default_room_id': self.id,
                'search_default_upcoming': 1  # Show upcoming by default
            },
            'target': 'current',
        }

    @api.constrains('name', 'company_id')
    def _check_unique_room_name_per_company(self):
        """Ensure room names are unique per company"""
        for room in self:
            if self.search_count([
                ('name', '=', room.name),
                ('company_id', '=', room.company_id.id),
                ('id', '!=', room.id)
            ]) > 0:
                raise ValidationError(_("A surgery room with this name already exists in this company!"))

    def get_available_slots(self, start_date, end_date=None):
        """Get available time slots for this room between given dates"""
        self.ensure_one()
        if not end_date:
            end_date = start_date + timedelta(days=1)  # Default to next day

        # Get all surgeries in this period
        domain = [
            ('room_id', '=', self.id),
            ('state', 'not in', ['cancelled']),
            ('start_datetime', '<', end_date),
            ('end_datetime', '>', start_date)
        ]
        existing_slots = self.env['surgery.slot'].search(domain, order='start_datetime')

        # Build a list of occupied time ranges
        occupied_times = [(s.start_datetime, s.end_datetime) for s in existing_slots]

        # Find available slots (simplified logic - would need refinement for real usage)
        available_slots = []
        current_time = start_date

        for start, end in sorted(occupied_times):
            if current_time < start:
                available_slots.append((current_time, start))
            current_time = max(current_time, end)

        if current_time < end_date:
            available_slots.append((current_time, end_date))

        return available_slots


class SurgerySlot(models.Model):
    _name = 'surgery.slot'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Surgery Slot'
    _order = 'start_datetime desc, name'

    name = fields.Char(
        string='اسم الجراحة', required=True, tracking=True,
        compute='_compute_name', store=True, readonly=False
    )
    room_id = fields.Many2one(
        'surgery.room', string='غرفة العمليات', required=True, tracking=True,
        ondelete='restrict',
    )
    doctor_id = fields.Many2one('res.partner', required=False, domain=[('is_doctor', '=', True)], string="الطبيب")
    patient_id = fields.Many2one(
        'res.partner', string='Patient', required=True, tracking=True,
        domain="[('is_patient','=',True)]"  # Assumes 'is_patient' field on res.partner
    )
    partner_id = fields.Many2one(
        'res.partner', string='Partner', required=False, tracking=True,
        domain="[('is_patient','=',True)]"
    )
    start_datetime = fields.Datetime(
        string='يبداء في', required=True, tracking=True,
        default=lambda self: fields.Datetime.now() + timedelta(hours=1)  # Default to next hour
    )
    end_datetime = fields.Datetime(string='يتنتهي في', required=True, tracking=True)
    duration = fields.Float(string='المدة الزمنية بالساعة', compute='_compute_duration', store=True, readonly=True)

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('confirmed', 'مؤكد'),
        ('in_progress', 'تحت التنفيذ'),
        ('done', 'منتهي'),
        ('cancelled', 'ملغي')
    ], string='Status', default='draft', tracking=True, copy=False, index=True)

    surgery_type = fields.Selection([
        ('emergency', 'Emergency'),
        ('elective', 'Elective'),
        ('outpatient', 'Outpatient Procedure'),
        ('day_case', 'Day Case')
    ], string='نوع الجراحة', required=True, default='elective', tracking=True)

    responsible_doctor_id = fields.Many2one('res.partner', required=True, domain=[('is_doctor', '=', True)], string="الطبيب")

    notes = fields.Text(string='ملاحظات و تعليمات')
    company_id = fields.Many2one('res.company', string='شركة', required=True, default=lambda self: self.env.company)
    color = fields.Integer(related='room_id.color', string='لون الغرفة', readonly=True,
                           store=True)  # For calendar consistency

    # Integration with Odoo Planning
    planning_slot_ids = fields.One2many(
        'planning.slot', 'surgery_id',  # 'surgery_id' is the field in planning.slot that references this model
        string='فريق الجراحة',
        copy=False,
        help="Planning shifts created for the surgical team."
    )
    is_planned = fields.Boolean(compute='_compute_is_planned', string="مخطط", store=True)

    def action_mark_in_progress(self):
        for slot in self:
            slot.write({'state': 'in_progress'})

    def action_mark_done(self):
        for slot in self:
            slot.write({'state': 'done'})

    def action_cancel(self):
        for slot in self:
            slot.write({'state': 'cancelled'})
    def action_reset_to_draft(self):
        for slot in self:
            slot.write({'state': 'draft'})

    def action_confirm(self):
        self.ensure_one()
        # Create planning slots for each team member
        planning_slots = self.env['planning.slot']

        self.write({
            'state': 'confirmed',
            # No need to manually set the planning_slot_ids as the One2many handles that automatically
        })
        return

    @api.depends('planning_slot_ids')
    def _compute_is_planned(self):
        for slot in self:
            slot.is_planned = bool(slot.planning_slot_ids)

    @api.depends('patient_id', 'surgery_type', 'room_id', 'responsible_doctor_id')
    def _compute_name(self):
        """Generate a name based on surgery details if not manually specified"""
        for slot in self:
            if not slot.name and slot.patient_id:  # Only compute if name is not manually set or is empty
                name_parts = [slot.surgery_type.capitalize() if slot.surgery_type else "Surgery"]
                name_parts.append(f"for {slot.patient_id.name}")
                if slot.responsible_doctor_id:
                    name_parts.append(f"w/ Dr. {slot.responsible_doctor_id.name.split(' ')[-1]}")  # Last name
                if slot.room_id:
                    name_parts.append(f"in {slot.room_id.name}")
                slot.name = " ".join(name_parts)
            elif not slot.name:  # Default if nothing else
                slot.name = _("New Surgery")

    @api.depends('start_datetime', 'end_datetime')
    def _compute_duration(self):
        """Calculate duration in hours from start and end times"""
        for slot in self:
            if slot.start_datetime and slot.end_datetime and slot.start_datetime < slot.end_datetime:
                delta = slot.end_datetime - slot.start_datetime
                slot.duration = delta.total_seconds() / 3600.0
            else:
                slot.duration = 0.0

    @api.constrains('start_datetime', 'end_datetime')
    def _check_start_end_dates(self):
        """Ensure end time is after start time and duration is positive"""
        for slot in self:
            if slot.start_datetime and slot.end_datetime and slot.start_datetime >= slot.end_datetime:
                raise ValidationError(_('End Time must be after Start Time.'))
            if slot.duration <= 0 and slot.start_datetime and slot.end_datetime:
                raise ValidationError(_('Surgery duration must be positive.'))

    def _check_availability(self, room_id, start_datetime, end_datetime, current_slot_id=None, staff_ids=None):
        """Centralized availability check for rooms and staff"""
        # Room Availability Check
        room_domain = [
            ('room_id', '=', room_id.id),
            ('state', 'not in', ['cancelled', 'done']),
            ('start_datetime', '<', end_datetime),
            ('end_datetime', '>', start_datetime),
        ]
        if current_slot_id:
            room_domain.append(('id', '!=', current_slot_id))
        conflicting_room_slots = self.env['surgery.slot'].search(room_domain)
        if conflicting_room_slots:
            raise ValidationError(
                _("Room '%(room_name)s' is already booked from %(start_time)s to %(end_time)s by surgery '%(surgery_name)s'.") % {
                    'room_name': room_id.name,
                    'start_time': fields.Datetime.context_timestamp(self,
                                                                    conflicting_room_slots[0].start_datetime).strftime(
                        '%H:%M'),
                    'end_time': fields.Datetime.context_timestamp(self,
                                                                  conflicting_room_slots[0].end_datetime).strftime(
                        '%H:%M'),
                    'surgery_name': conflicting_room_slots[0].name,
                })

        # Staff Availability Check
        if staff_ids:
            # Against other surgery_slot
            staff_surgery_domain = [
                '|', ('responsible_doctor_id', 'in', staff_ids),
                ('state', 'not in', ['cancelled', 'done']),
                ('start_datetime', '<', end_datetime),
                ('end_datetime', '>', start_datetime),
            ]
            if current_slot_id:
                staff_surgery_domain.append(('id', '!=', current_slot_id))

            conflicting_staff_surgeries = self.env['surgery.slot'].search(staff_surgery_domain)
            if conflicting_staff_surgeries:
                busy_staff_names = []
                for surgery in conflicting_staff_surgeries:
                    if surgery.responsible_doctor_id.id in staff_ids:
                        busy_staff_names.append(surgery.responsible_doctor_id.name)


                busy_staff_names = list(set(busy_staff_names))  # Remove duplicates
                raise ValidationError(
                    _("Staff member(s) (%(staff_names)s) are already scheduled for another surgery ('%(surgery_name)s') during this time.") % {
                        'staff_names': ', '.join(busy_staff_names),
                        'surgery_name': conflicting_staff_surgeries[0].name
                    })

            # Against Odoo Planning Slots (excluding those linked to current surgery if updating)
            planning_domain = [
                ('employee_id', 'in', staff_ids),
                ('start_datetime', '<', end_datetime),
                ('end_datetime', '>', start_datetime),
            ]
            if current_slot_id:
                current_surgery = self.browse(current_slot_id)
                if current_surgery.planning_slot_ids:
                    planning_domain.append(('id', 'not in', current_surgery.planning_slot_ids.ids))

            conflicting_planning = self.env['planning.slot'].search(planning_domain)
            if conflicting_planning:
                busy_staff = self.env['hr.employee'].browse([
                    e.id for e in self.env['hr.employee'].search([('id', 'in', staff_ids)])
                    if e.id in conflicting_planning.mapped('employee_id.id')
                ])
                staff_names = ', '.join(busy_staff.mapped('name'))
                return {'warning': {
                    'title': _("تحذير "),
                    'message': "%s\n\n%s" % (staff_names)
                }}
            else:
                return None
        return None

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to check availability before creating surgeries"""
        for vals in vals_list:
            # If key fields are provided, check availability
            if all(key in vals for key in ['room_id', 'start_datetime', 'end_datetime']):
                room_id = self.env['surgery.room'].browse(vals['room_id'])
                start_dt = fields.Datetime.to_datetime(vals['start_datetime'])
                end_dt = fields.Datetime.to_datetime(vals['end_datetime'])

                # Collect staff IDs
                staff_ids = []
                if vals.get('responsible_doctor_id'):
                    staff_ids.append(vals['responsible_doctor_id'])

                self._check_availability(room_id, start_dt, end_dt, staff_ids=list(set(staff_ids)))

        records = super(SurgerySlot, self).create(vals_list)



        return records





    def write(self, vals):
        """Override write to check availability when key fields change"""
        for slot in self:
            if any(field in vals for field in
                   ['room_id', 'start_datetime', 'end_datetime', 'responsible_doctor_id']):
                room_id = self.env['surgery.room'].browse(vals.get('room_id', slot.room_id.id))
                start_dt = fields.Datetime.to_datetime(vals.get('start_datetime', slot.start_datetime))
                end_dt = fields.Datetime.to_datetime(vals.get('end_datetime', slot.end_datetime))

                # Collect staff IDs (current and new)
                staff_ids = [vals.get('responsible_doctor_id', slot.responsible_doctor_id.id)]



                # Remove None values and get unique IDs
                staff_ids = list(set(filter(None, staff_ids)))

                # Only check if the slot is not cancelled or done
                if vals.get('state', slot.state) not in ['cancelled', 'done']:
                    self._check_availability(room_id, start_dt, end_dt, current_slot_id=slot.id, staff_ids=staff_ids)

        result = super(SurgerySlot, self).write(vals)



        # If cancelled, clean

    # Add to the SurgerySlot class

    def get_unavailable_intervals(self, start_dt, end_dt, resource=None, tz=None):
        """Return unavailable time slots for the Gantt view"""
        if not resource:
            return []

        # For room-based view
        if resource._name == 'surgery.room':
            # Find all confirmed surgeries in this room excluding cancelled and done
            domain = [
                ('room_id', '=', resource.id),
                ('state', 'not in', ['cancelled', 'done']),
                ('start_datetime', '<', end_dt),
                ('end_datetime', '>', start_dt),
            ]

        # For doctor-based view
        elif resource._name == 'res.partner' and resource.is_doctor:
            # Find all confirmed surgeries with this doctor excluding cancelled and done
            domain = [
                '|',
                ('responsible_doctor_id', '=', resource.id),
                ('state', 'not in', ['cancelled', 'done']),
                ('start_datetime', '<', end_dt),
                ('end_datetime', '>', start_dt),
            ]
        else:
            return []

        # Get overlapping surgeries
        slots = self.search(domain)

        # Convert to intervals
        intervals = []
        for slot in slots:
            # Use max and min to ensure we're within view bounds
            interval_start = max(slot.start_datetime, start_dt)
            interval_end = min(slot.end_datetime, end_dt)
            intervals.append((interval_start, interval_end))

        return intervals

    def gantt_unavailability(self, start_dt, end_dt, scale, group_bys=None, rows=None):
        """Return unavailable time slots for the Gantt view"""
        if not rows:
            return []

        result = []
        if group_bys and group_bys[0] == 'room_id':
            for row in rows:
                room_id = self.env['surgery.room'].browse(row.get('resId'))
                if room_id:
                    result.append({
                        'row_id': row.get('id'),
                        'intervals': self.get_unavailable_intervals(start_dt, end_dt, room_id)
                    })

        elif group_bys and group_bys[0] == 'responsible_doctor_id':
            for row in rows:
                doctor_id = self.env['res.partner'].browse(row.get('resId'))
                if doctor_id and doctor_id.is_doctor:
                    result.append({
                        'row_id': row.get('id'),
                        'intervals': self.get_unavailable_intervals(start_dt, end_dt, doctor_id)
                    })

        return result

class PlanningSlot(models.Model):
    _inherit = "planning.slot"

    surgery_id = fields.Many2one(
        'surgery.slot',
        string='Related Surgery',
        ondelete='cascade',  # What happens to this record when the surgery is deleted
        index=True
    )