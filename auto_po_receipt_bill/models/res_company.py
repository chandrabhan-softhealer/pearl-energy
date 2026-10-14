from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    auto_po_receipt_bill = fields.Boolean(
        string="Auto receive and bill on PO confirmation",
        default=True,
        help="When a Purchase Order is confirmed, automatically validate its "
             "receipt with the demanded quantity and post the vendor bill.",
    )
