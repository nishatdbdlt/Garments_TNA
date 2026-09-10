from odoo import api, fields, models, _

SAMPLE_TYPES = [
    ('proto', 'Proto'), ('fit', 'Fit'), ('size_set', 'Size Set'),
    ('pp', 'PP'), ('sms', 'SMS'), ('photo', 'Photo'),
    ('counter', 'Counter'), ('top', 'TOP'), ('shipment', 'Shipment'),
    ('wash', 'Wash'), ('lab_dip', 'Lab Dip'),
    ('print_strike_off', 'Print Strike-off'), ('embroidery', 'Embroidery'),
    ('mock_up', 'Mock-up'),
]

ACTION_TYPES = [
    ('sample_request_created', 'Sample Request Created'),
    ('tech_pack_review', 'Tech Pack Review'),
    ('fabric_trim_arrange', 'Fabric/Trim Arrange'),
    ('pattern_development', 'Pattern Development'),
    ('cutting', 'Cutting'), ('sewing', 'Sewing'),
    ('printing_embroidery', 'Printing / Embroidery'), ('washing', 'Washing'),
    ('sample_preparation', 'Sample Preparation'), ('internal_qc', 'Internal QC'),
    ('send_to_buyer', 'Send to Buyer'),
    ('buyer_feedback_received', 'Buyer Feedback Received'),
    ('correction_required', 'Correction Required'),
    ('sample_resubmit', 'Sample Re-submit'), ('buyer_approved', 'Buyer Approved'),
    ('sample_rejected', 'Sample Rejected'),
    ('final_sample_archived', 'Final Sample Archived'),
]

MILESTONE_STAGES = [
    ('request', 'Request'), ('development', 'Development'),
    ('production', 'Production'), ('qc', 'QC'), ('submission', 'Submission'),
    ('feedback', 'Feedback'), ('revision', 'Revision'), ('approval', 'Approval'),
    ('closing', 'Closing'),
]

STANDARD_MILESTONES = [
    ('request', 'Request', 'sample_request_created'),
    ('development', 'Development', 'pattern_development'),
    ('production', 'Production', 'sample_preparation'),
    ('qc', 'QC', 'internal_qc'),
    ('submission', 'Submission', 'send_to_buyer'),
    ('feedback', 'Feedback', 'buyer_feedback_received'),
    ('revision', 'Revision', 'correction_required'),
    ('approval', 'Approval', 'buyer_approved'),
    ('closing', 'Closing', 'final_sample_archived'),
]


class GarmentTNATemplate(models.Model):
    _name = 'garment.tna.template'
    _description = 'Garments TNA Template'
    _order = 'name'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    note = fields.Text()
    milestone_ids = fields.One2many(
        'garment.tna.template.milestone', 'template_id', string='Milestones'
    )
    sample_type_ids = fields.One2many(
        'garment.tna.template.sample.type', 'template_id', string='Sample Types'
    )

    @api.model
    def default_get(self, field_list):
        values = super().default_get(field_list)
        if 'sample_type_ids' in field_list:
            values['sample_type_ids'] = [(0, 0, {
                'sequence': sequence,
                'sample_type': code,
                'required': False,
            }) for sequence, (code, _label) in enumerate(SAMPLE_TYPES, start=1)]
        if 'milestone_ids' in field_list:
            values['milestone_ids'] = [(0, 0, {
                'sequence': sequence,
                'stage': stage,
                'name': name,
                'action_type': action_type,
            }) for sequence, (stage, name, action_type) in enumerate(STANDARD_MILESTONES, start=1)]
        return values

    def action_load_standard_sample_types(self):
        for template in self:
            present = set(template.sample_type_ids.mapped('sample_type'))
            template.sample_type_ids = [(0, 0, {
                'sequence': sequence,
                'sample_type': code,
                'required': False,
            }) for sequence, (code, _label) in enumerate(SAMPLE_TYPES, start=1) if code not in present]
        return True

    def action_load_standard_milestones(self):
        for template in self:
            present = set(template.milestone_ids.mapped('stage'))
            template.milestone_ids = [(0, 0, {
                'sequence': sequence,
                'stage': stage,
                'name': name,
                'action_type': action_type,
            }) for sequence, (stage, name, action_type) in enumerate(STANDARD_MILESTONES, start=1)
                if stage not in present]
        return True


class GarmentTNATemplateMilestone(models.Model):
    _name = 'garment.tna.template.milestone'
    _description = 'Garments TNA Template Milestone'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    stage = fields.Selection(MILESTONE_STAGES, string='Milestone Stage')
    name = fields.Char(required=True, string='Milestone')
    activity = fields.Char(help='Work/activity to be completed for this milestone.')
    action = fields.Char(help='Required action or follow-up.')
    action_type = fields.Selection(ACTION_TYPES, string='Action')
    planned_days = fields.Integer(
        string='Plan Offset (Days)',
        help='Number of days from the buyer actual date.',
    )
    responsible_id = fields.Many2one('res.users', string='Responsible')
    template_id = fields.Many2one(
        'garment.tna.template', required=True, ondelete='cascade'
    )


class GarmentTNATemplateSampleType(models.Model):
    _name = 'garment.tna.template.sample.type'
    _description = 'TNA Template Sample Type'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    sample_type = fields.Selection(SAMPLE_TYPES, required=True)
    required = fields.Boolean(string='Tick / Required', default=True)
    template_id = fields.Many2one('garment.tna.template', required=True, ondelete='cascade')


class GarmentTNA(models.Model):
    _name = 'garment.tna'
    _description = 'Garments Time and Action Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(required=True, default=lambda self: _('New'), tracking=True)
    active = fields.Boolean(default=True)
    template_id = fields.Many2one(
        'garment.tna.template', required=True, tracking=True,
        help='Selecting a template loads its milestones below. You can edit them for this TNA.'
    )
    buyer_id = fields.Many2one('res.partner', string='Buyer', tracking=True)
    style_no = fields.Char(string='Style / Order No.', tracking=True)
    quantity = fields.Float(string='Quantity', tracking=True)
    buyer_actual_date = fields.Date(string='Buyer Actual Date', tracking=True)
    buyer_planned_date = fields.Date(string='Buyer Planned Date', tracking=True)
    material_inhouse_date = fields.Date(string='Material In-house Date', tracking=True)
    delivery_date = fields.Date(string='Delivery Date', tracking=True)
    note = fields.Text()
    milestone_ids = fields.One2many('garment.tna.milestone', 'tna_id', string='Milestones')
    sample_type_ids = fields.One2many('garment.tna.sample.type', 'tna_id', string='Sample Types')

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if not self.template_id:
            self.milestone_ids = [(5, 0, 0)]
            return
        self.milestone_ids = [(5, 0, 0)] + [(0, 0, {
            'sequence': line.sequence,
            'name': line.name,
            'stage': line.stage,
            'activity': line.activity,
            'action': line.action,
            'action_type': line.action_type,
            'planned_days': line.planned_days,
            'responsible_id': line.responsible_id.id,
        }) for line in self.template_id.milestone_ids]
        self.sample_type_ids = [(5, 0, 0)] + [(0, 0, {
            'sample_type': line.sample_type,
            'selected': line.required,
        }) for line in self.template_id.sample_type_ids]

    @api.onchange('buyer_actual_date')
    def _onchange_buyer_actual_date(self):
        for record in self:
            if record.buyer_actual_date:
                for line in record.milestone_ids:
                    line.planned_date = fields.Date.add(
                        record.buyer_actual_date, days=line.planned_days or 0
                    )

    def action_create_milestone_activities(self):
        """Create Odoo activities only for milestone lines with an owner."""
        for record in self:
            for line in record.milestone_ids.filtered(lambda item: item.responsible_id and not item.activity_created):
                summary = line.activity or line.name
                record.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=line.responsible_id.id,
                    date_deadline=line.planned_date or record.delivery_date or fields.Date.today(),
                    summary=summary,
                    note=line.action or False,
                )
                line.activity_created = True
        return True


class GarmentTNAMilestone(models.Model):
    _name = 'garment.tna.milestone'
    _description = 'Garments TNA Milestone'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    stage = fields.Selection(MILESTONE_STAGES, string='Milestone Stage')
    name = fields.Char(required=True, string='Milestone')
    activity = fields.Char()
    action = fields.Char()
    action_type = fields.Selection(ACTION_TYPES, string='Action')
    planned_days = fields.Integer(string='Plan Offset (Days)')
    start_date = fields.Date(string='Start Date')
    planned_date = fields.Date(string='Deadline')
    actual_date = fields.Date(string='Completed Date')
    responsible_id = fields.Many2one('res.users', string='Responsible')
    status = fields.Selection([
        ('pending', 'Pending'), ('in_progress', 'In Progress'),
        ('done', 'Done'), ('blocked', 'Blocked'),
    ], default='pending', required=True)
    deadline_status = fields.Selection([
        ('on_track', 'On Track'), ('overdue', 'Overdue'), ('completed', 'Completed'),
        ('blocked', 'Blocked'),
    ], string='Status', compute='_compute_deadline_status')
    late_days = fields.Integer(string='Late Days', compute='_compute_deadline_status')
    late_by = fields.Char(string='Late By', compute='_compute_deadline_status')
    remarks = fields.Text()
    buyer_comment = fields.Text()
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    activity_created = fields.Boolean(copy=False, readonly=True)
    tna_id = fields.Many2one('garment.tna', required=True, ondelete='cascade')

    @api.onchange('planned_days', 'tna_id.buyer_actual_date')
    def _onchange_planned_days(self):
        for line in self:
            if line.tna_id.buyer_actual_date and line.planned_days is not None:
                line.planned_date = fields.Date.add(line.tna_id.buyer_actual_date, days=line.planned_days)

    @api.depends('planned_date', 'actual_date', 'status')
    def _compute_deadline_status(self):
        today = fields.Date.today()
        for line in self:
            line.late_days = 0
            line.late_by = False
            if line.status == 'done':
                line.deadline_status = 'completed'
            elif line.status == 'blocked':
                line.deadline_status = 'blocked'
            elif line.planned_date and line.planned_date < today:
                line.deadline_status = 'overdue'
            else:
                line.deadline_status = 'on_track'

            # A completed item may also show how late it was completed.
            compare_date = line.actual_date if line.status == 'done' and line.actual_date else today
            if line.planned_date and compare_date and compare_date > line.planned_date:
                line.late_days = (compare_date - line.planned_date).days
                line.late_by = _('%s day(s) late') % line.late_days


class GarmentTNASampleType(models.Model):
    _name = 'garment.tna.sample.type'
    _description = 'TNA Sample Type'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    sample_type = fields.Selection(
        SAMPLE_TYPES, string='Sample Type', required=True, default='proto'
    )
    selected = fields.Boolean(string='Required')
    tna_id = fields.Many2one('garment.tna', required=True, ondelete='cascade')
