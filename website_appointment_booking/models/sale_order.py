# Copyright 2026 Techsystech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    website_booking_ids = fields.One2many(
        comodel_name="resource.booking",
        inverse_name="website_payment_sale_order_id",
        string="Website Bookings",
        readonly=True,
    )

    def action_confirm(self):
        result = super().action_confirm()
        self.mapped("website_booking_ids")._action_confirm_from_website_payment()
        return result
