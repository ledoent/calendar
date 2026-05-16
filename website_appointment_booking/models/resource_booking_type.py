# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields, models


def _slugify(value):
    """Convert a string to a URL-friendly slug."""
    value = (value or "").lower().strip()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[-\s]+", "-", value)
    return value.strip("-")


class ResourceBookingType(models.Model):
    _inherit = "resource.booking.type"

    website_published = fields.Boolean(
        copy=False,
        help="When checked, this booking type will be available on a public "
        "booking page accessible without login.",
    )
    website_slug = fields.Char(
        compute="_compute_website_slug",
        store=True,
        readonly=False,
        copy=False,
        help="URL-friendly identifier used in the public booking page URL. "
        "Auto-generated from the name, but can be customized.",
    )
    website_description = fields.Html(
        translate=True,
        sanitize_attributes=False,
        help="Introductory text displayed on the public booking page.",
    )
    website_card_image = fields.Image(
        string="Booking Card Photo",
        max_width=1024,
        max_height=1024,
        help="Photo displayed for this booking type on the public /book landing page.",
    )
    website_card_resource_ids = fields.Many2many(
        comodel_name="resource.resource",
        compute="_compute_website_card_resource_ids",
        store=False,
        readonly=True,
        string="Card Avatars",
        help="User-linked resources from all combinations, displayed on the public /book card.",
    )
    website_url = fields.Char(
        string="Website URL",
        compute="_compute_website_url",
        help="Public booking page URL for this booking type.",
    )

    require_upfront_payment = fields.Boolean(
        string="Require Upfront Payment",
        help="When enabled for a published booking type, public visitors must "
        "complete website checkout before their attendance is confirmed.",
    )
    payment_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Payment Product",
        domain="[('sale_ok', '=', True)]",
        help="Product used to charge the upfront booking payment during checkout.",
    )
    payment_price = fields.Monetary(
        string="Payment Price",
        currency_field="currency_id",
        help="Price charged for the upfront booking payment. If empty, the "
        "product sales price is used.",
    )
    website_payment_price = fields.Monetary(
        string="Website Payment Price",
        compute="_compute_website_payment_price",
        currency_field="currency_id",
        help="Effective upfront payment shown on the website and charged at checkout.",
    )
    payment_hold_expiry_hours = fields.Float(
        string="Checkout Hold Expiry",
        default=1.0,
        help="Hours to hold a scheduled, unpaid booking before cleanup releases "
        "the slot.",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        readonly=True,
    )

    _sql_constraints = [
        (
            "website_slug_unique",
            "UNIQUE(website_slug)",
            "The website slug must be unique.",
        ),
    ]

    @api.depends("combination_rel_ids.combination_id.resource_ids")
    def _compute_website_card_resource_ids(self):
        for record in self:
            record.website_card_resource_ids = (
                record.sudo()
                .combination_rel_ids.combination_id.resource_ids.filtered(lambda r: r.user_id)
            )

    @api.depends("name")
    def _compute_website_slug(self):
        for record in self:
            if not record.website_slug and record.name:
                record.website_slug = _slugify(record.name)

    @api.depends("payment_price", "payment_product_id.lst_price")
    def _compute_website_payment_price(self):
        for record in self:
            record.website_payment_price = (
                record.payment_price or record.payment_product_id.lst_price
            )

    @api.depends("website_slug")
    def _compute_website_url(self):
        for record in self:
            record.website_url = f"/book/{record.website_slug}" if record.website_slug else "/book"

    def open_website_url(self):
        self.ensure_one()
        return self.env["website"].get_client_action(self.website_url)
