# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime
from unittest.mock import patch

from freezegun import freeze_time

from odoo.tests.common import TransactionCase

from odoo.addons.resource_booking.tests.common import create_test_data


@freeze_time("2021-02-26 09:00:00", tick=True)
class TestResourceBookingSms(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_test_data(cls)
        # Booking types auto-assign combinations randomly by default, so any
        # of the resource users may end up on a confirmed booking. Give them
        # all a phone number so the SMS path is exercised regardless of which
        # combination is picked.
        cls.users.partner_id.phone = "+15551234567"

    def _create_scheduled_booking(self, start=None):
        """Create a booking with a start time so that a meeting is generated."""
        booking = self.env["resource.booking"].create(
            {
                "type_id": self.rbt.id,
                "partner_ids": [(4, self.partner.id)],
                "combination_auto_assign": True,
            }
        )
        # Default: next Monday 10:00 UTC, inside the 8-17 UTC calendar window.
        booking.start = start or datetime(2021, 3, 1, 10, 0, 0)
        return booking

    def test_sms_created_on_confirm(self):
        """An sms.sms record is created when a booking is confirmed."""
        booking = self._create_scheduled_booking()
        self.assertTrue(booking.meeting_id, "Meeting should exist after setting start")
        with patch.object(
            type(self.env["sms.sms"]),
            "send",
        ) as mock_send:
            booking.action_confirm()
        mock_send.assert_called()

    def test_sms_body_contains_booking_info(self):
        """The SMS body includes the requester name and booking type."""
        booking = self._create_scheduled_booking()
        body = booking._format_sms_body()
        self.assertIn(self.rbt.name, body)
        self.assertIn(self.partner.name, body)

    def test_no_sms_without_phone(self):
        """No sms.sms record is created if resource user has no phone."""
        self.users.partner_id.phone = False
        booking = self._create_scheduled_booking()
        sms_before = self.env["sms.sms"].sudo().search_count([])
        with patch.object(
            type(self.env["sms.sms"]),
            "send",
        ):
            booking.action_confirm()
        sms_after = self.env["sms.sms"].sudo().search_count([])
        self.assertEqual(sms_before, sms_after)

    def test_no_sms_without_meeting(self):
        """No SMS is sent if the booking has no meeting (unscheduled)."""
        booking = self.env["resource.booking"].create(
            {
                "type_id": self.rbt.id,
                "partner_ids": [(4, self.partner.id)],
                "combination_auto_assign": True,
            }
        )
        # Don't set start — no meeting_id
        self.assertFalse(booking.meeting_id)
        with patch.object(
            type(self.env["sms.sms"]),
            "send",
        ) as mock_send:
            booking.action_confirm()
        mock_send.assert_not_called()

    def test_sms_body_localised_time(self):
        """The SMS body shows the start time in the calendar's timezone."""
        self.rbt.resource_calendar_id.tz = "US/Eastern"
        # Working hours (8-17) are now read in EST, so pick a UTC instant that
        # lands inside that window: 14:00 UTC == 09:00 EST.
        booking = self._create_scheduled_booking(start=datetime(2021, 3, 1, 14, 0, 0))
        body = booking._format_sms_body()
        # 14:00 UTC = 09:00 EST
        self.assertIn("09:00 AM", body)
