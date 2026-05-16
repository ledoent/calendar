# Copyright 2026 Techsystech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResourceBooking(models.Model):
    _inherit = "resource.booking"

    website_payment_required = fields.Boolean(
        string="Website Payment Required",
        copy=False,
        help="Technical flag set for public bookings waiting on website checkout.",
    )
    website_payment_sale_order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Website Payment Order",
        copy=False,
        ondelete="set null",
    )
    website_payment_expires_at = fields.Datetime(
        string="Website Payment Hold Expires At",
        copy=False,
    )

    def _action_confirm_from_website_payment(self):
        """Confirm requester attendance after the linked website sale is confirmed."""
        pending = self.filtered(
            lambda booking: booking.website_payment_required
            and booking.website_payment_sale_order_id.state in ("sale", "done")
            and booking.state == "scheduled"
        )
        if pending:
            pending.action_confirm()
            pending.write({"website_payment_required": False})
        return True

    def _cron_cleanup_expired_website_payment_bookings(self):
        """Release slots held by abandoned website checkout orders."""
        now = fields.Datetime.now()
        expired = self.search(
            [
                ("website_payment_required", "=", True),
                ("website_payment_expires_at", "!=", False),
                ("website_payment_expires_at", "<", now),
                ("state", "in", ["pending", "scheduled"]),
            ]
        )
        for booking in expired:
            order = booking.website_payment_sale_order_id
            if order and order.state in ("draft", "sent"):
                order.action_cancel()
            booking.action_cancel()
        return True
