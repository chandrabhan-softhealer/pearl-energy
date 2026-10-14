from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_po_receipt_bill = fields.Boolean(
        related='company_id.auto_po_receipt_bill',
        readonly=False,
    )
