import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        # Standard confirmation runs first and is never affected by the automation.
        res = super().button_confirm()
        if self.env.context.get('skip_auto_po_receipt_bill') or self.env.context.get('install_mode'):
            return res
        for order in self:
            if order.state == 'purchase' and order.company_id.auto_po_receipt_bill:
                order._run_auto_receipt_and_bill()
        return res

    # ------------------------------------------------------------------
    # Automation (isolated: failure never blocks the PO confirmation)
    # ------------------------------------------------------------------
    def _run_auto_receipt_and_bill(self):
        self.ensure_one()
        try:
            with self.env.cr.savepoint():
                message = self._auto_receive_and_bill()
        except Exception as exc:  # noqa: BLE001 - deliberately broad, see module docstring
            _logger.warning("Auto receipt/bill failed for %s: %s", self.name, exc, exc_info=True)
            self.message_post(body=_(
                "Automatic receipt validation / vendor bill was not completed: %s. "
                "The order is confirmed; please process the receipt and bill manually.",
                str(exc),
            ))
            return
        if message:
            self.message_post(body=message)

    def _auto_receive_and_bill(self):
        """Return an optional note to post in the chatter. Raise to roll back."""
        self.ensure_one()

        # 1. Receipts -----------------------------------------------------
        pickings = self.picking_ids.filtered(
            lambda p: p.picking_type_code == 'incoming'
            and p.state not in ('done', 'cancel')
        )
        tracked = pickings.move_ids.filtered(lambda m: m.product_id.tracking != 'none')
        if tracked:
            # Lots/serials need user input: leave everything manual.
            return _("Automatic receipt and bill skipped: tracked products (lot/serial) "
                     "need to be processed manually.")

        pickings.action_assign()
        for picking in pickings:
            for move in picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
                move.write({
                    'quantity': move.product_uom_qty,
                    'picked': True,
                })
            result = picking.with_context(
                skip_backorder=True,
                skip_sms=True,
                skip_immediate=True,
                picking_ids_not_to_backorder=picking.ids,
            ).button_validate()
            if picking.state != 'done':
                raise ValueError(_(
                    "receipt %(name)s was not validated (Odoo returned: %(res)s)",
                    name=picking.name, res=result,
                ))

        # 2. Vendor bill --------------------------------------------------
        existing = self.invoice_ids.filtered(
            lambda b: b.move_type == 'in_invoice' and b.state != 'cancel'
        )
        if existing:
            return False
        self.action_create_invoice()
        bills = self.invoice_ids.filtered(
            lambda b: b.move_type == 'in_invoice' and b.state == 'draft'
        )
        if not bills:
            raise ValueError(_("no vendor bill could be created"))
        for bill in bills:
            # The receipt is fully validated, so billing the ordered quantity
            # on any zero-quantity line is consistent with what was received.
            for line in bill.invoice_line_ids.filtered(
                lambda l: l.purchase_line_id and not l.display_type and not l.quantity
            ):
                line.quantity = line.purchase_line_id.product_qty
            bill.invoice_date = fields.Date.context_today(self)
            bill.action_post()
        return False
