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
        # Give the first resource user a mobile number
        cls.users[0].partner_id.mobile = "+15551234567"

    def _create_scheduled_booking(self):
        """Create a booking with a start time so that a meeting is generated."""
        booking = self.env["resource.booking"].create(
            {
                "type_id": self.rbt.id,
                "partner_ids": [(4, self.partner.id)],
                "combination_auto_assign": True,
            }
        )
        # Set start in the future (next Monday 10:00 UTC)
        booking.start = datetime(2021, 3, 1, 10, 0, 0)
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
        self.users[0].partner_id.mobile = False
        self.users[0].partner_id.phone = False
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
        booking = self._create_scheduled_booking()
        body = booking._format_sms_body()
        # 10:00 UTC = 05:00 EST
        self.assertIn("05:00 AM", body)
