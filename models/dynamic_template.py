from odoo import api, fields, models


class DynamicTemplate(models.Model):
    _name = 'dynamic.template'
    _description = 'Dynamic Template'
    _order = 'name'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    field_ids = fields.One2many(
        'dynamic.template.field', 'template_id', string='Fields'
    )


class DynamicTemplateField(models.Model):
    _name = 'dynamic.template.field'
    _description = 'Dynamic Template Field'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    field_type = fields.Selection([
        ('char', 'Text'),
        ('integer', 'Integer'),
        ('float', 'Decimal'),
        ('date', 'Date'),
        ('boolean', 'Yes/No'),
    ], required=True, default='char')
    required = fields.Boolean(default=False)
    template_id = fields.Many2one(
        'dynamic.template', required=True, ondelete='cascade'
    )
