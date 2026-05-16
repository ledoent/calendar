# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from datetime import timedelta

from psycopg2 import IntegrityError

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from odoo.addons.resource_booking.tests.common import create_test_data


@tagged("post_install", "-at_install")
class TestResourceBookingTypeWebsite(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_test_data(cls)

    def test_slug_auto_generated(self):
        """Slug is computed from name when not set."""
        self.rbt.website_slug = False
        self.rbt.name = "30-min Consultation"
        self.rbt._compute_website_slug()
        self.assertEqual(self.rbt.website_slug, "30-min-consultation")

    def test_slug_not_overwritten(self):
        """Existing slug is not overwritten on name change."""
        self.rbt.website_slug = "custom-slug"
        self.rbt.name = "Changed Name"
        self.rbt._compute_website_slug()
        self.assertEqual(self.rbt.website_slug, "custom-slug")

    def test_slug_unique_constraint(self):
        """Two booking types cannot share the same slug."""
        self.rbt.website_slug = "unique-slug"
        rbt2 = self.env["resource.booking.type"].create(
            {
                "name": "Another Type",
                "resource_calendar_id": self.r_calendars[2].id,
                "combination_rel_ids": [],
            }
        )
        with (
            self.assertRaises(IntegrityError),
            self.env.cr.savepoint(),
            mute_logger("odoo.sql_db"),
        ):
            rbt2.website_slug = "unique-slug"
            rbt2.flush_recordset()

    def test_website_published_default(self):
        """Website published defaults to False."""
        self.assertFalse(self.rbt.website_published)

    def test_slug_special_characters(self):
        """Slug strips special characters."""
        self.rbt.website_slug = False
        self.rbt.name = "Meeting (30 min) & Coffee!"
        self.rbt._compute_website_slug()
        self.assertEqual(self.rbt.website_slug, "meeting-30-min-coffee")

    def test_unpublishing_does_not_clear_website_slug(self):
        """Published flag controls visibility without mutating existing slug."""
        self.rbt.write({"website_published": True, "website_slug": "keep-me"})
        self.rbt.website_published = False
        self.assertEqual(self.rbt.website_slug, "keep-me")

    def test_card_display_fields_are_computed_from_combinations(self):
        """Card avatars are auto-computed from user-linked resources in combinations."""
        self.rbt.write(
            {
                "website_card_image": base64.b64encode(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4//8/AAX+Av4N70a4AAAAAElFTkSuQmCC")),
            }
        )
        self.assertTrue(self.rbt.website_card_image)
        # All user resources from all combinations should appear
        self.assertEqual(self.rbt.website_card_resource_ids, self.r_users)
        # Material resources (no user_id) should be excluded
        self.assertFalse(any(r in self.rbt.website_card_resource_ids for r in self.r_materials))

    def test_upfront_payment_fields_can_be_configured(self):
        """Published booking types can require checkout with product pricing."""
        product = self.env["product.product"].create(
            {
                "name": "Booking Deposit",
                "type": "service",
                "sale_ok": True,
                "list_price": 50.0,
            }
        )
        self.rbt.write(
            {
                "website_published": True,
                "require_upfront_payment": True,
                "payment_product_id": product.id,
                "payment_price": 25.0,
                "payment_hold_expiry_hours": 0.5,
            }
        )
        self.assertTrue(self.rbt.require_upfront_payment)
        self.assertEqual(self.rbt.payment_product_id, product)
        self.assertEqual(self.rbt.payment_price, 25.0)
        self.assertEqual(self.rbt.website_payment_price, 25.0)
        self.rbt.payment_price = 0.0
        self.assertEqual(self.rbt.website_payment_price, 50.0)
        self.assertEqual(self.rbt.payment_hold_expiry_hours, 0.5)

    def _create_scheduled_payment_booking(self):
        product = self.env["product.product"].create(
            {
                "name": "Booking Deposit",
                "type": "service",
                "sale_ok": True,
                "list_price": 50.0,
            }
        )
        self.rbt.write(
            {
                "website_published": True,
                "require_upfront_payment": True,
                "payment_product_id": product.id,
                "payment_price": 25.0,
            }
        )
        booking = self.env["resource.booking"].create(
            {
                "type_id": self.rbt.id,
                "partner_ids": [(4, self.partner.id)],
                "combination_auto_assign": False,
                "combination_id": self.rbcs[0].id,
            }
        )
        booking.start = fields.Datetime.to_datetime("2021-03-01 10:00:00")
        order = self.env["sale.order"].create({"partner_id": self.partner.id})
        self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": product.id,
                "product_uom_qty": 1.0,
                "product_uom": product.uom_id.id,
                "price_unit": 25.0,
            }
        )
        booking.write(
            {
                "website_payment_required": True,
                "website_payment_sale_order_id": order.id,
                "website_payment_expires_at": fields.Datetime.now() + timedelta(hours=1),
            }
        )
        return booking, order

    def test_sale_confirmation_confirms_paid_booking(self):
        """A checkout-confirmed sale order confirms the linked booking attendance."""
        booking, order = self._create_scheduled_payment_booking()
        self.assertEqual(booking.state, "scheduled")
        order.action_confirm()
        self.assertEqual(booking.state, "confirmed")
        self.assertFalse(booking.website_payment_required)

    def test_expired_checkout_cleanup_releases_slot(self):
        """Abandoned checkout cancels the booking hold so the slot is released."""
        booking, order = self._create_scheduled_payment_booking()
        booking.website_payment_expires_at = fields.Datetime.now() - timedelta(minutes=1)
        self.env["resource.booking"]._cron_cleanup_expired_website_payment_bookings()
        self.assertEqual(booking.state, "canceled")
        self.assertEqual(order.state, "cancel")
