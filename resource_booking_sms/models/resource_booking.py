# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

import pytz

from odoo import models

_logger = logging.getLogger(__name__)


class ResourceBooking(models.Model):
    _inherit = "resource.booking"

    def action_confirm(self):
        res = super().action_confirm()
        for booking in self:
            if booking.meeting_id:
                booking._send_booking_sms()
        return res

    def _send_booking_sms(self):
        """Send an SMS notification to every resource user with a phone number.

        The message includes the requester name, the booking type and the
        localised start time.  Sending is delegated to ``sms.sms`` so that
        whatever SMS gateway is configured (IAP, Twilio, etc.) is used
        transparently.
        """
        self.ensure_one()
        resource_partners = self.combination_id.resource_ids.filtered(
            lambda r: r.resource_type == "user"
        ).mapped("user_id.partner_id")
        if not resource_partners:
            return
        body = self._format_sms_body()
        Sms = self.env["sms.sms"].sudo()
        for partner in resource_partners:
            number = partner.phone
            if not number:
                continue
            sms = Sms.create(
                {
                    "number": number,
                    "body": body,
                    "partner_id": partner.id,
                }
            )
            sms.send(raise_exception=False)
            _logger.info(
                "SMS queued to %s for booking %s (sms.sms %s)",
                number,
                self.id,
                sms.id,
            )

    def _format_sms_body(self):
        """Build the SMS body for a booking confirmation notification."""
        self.ensure_one()
        requester = self.partner_ids[:1].name or "Someone"
        start_str = ""
        if self.start:
            tz_name = self.type_id.resource_calendar_id.tz or "UTC"
            utc_dt = pytz.utc.localize(self.start)
            local_dt = utc_dt.astimezone(pytz.timezone(tz_name))
            start_str = local_dt.strftime("%B %d at %I:%M %p %Z")
        return f"New booking: {requester} booked {self.type_id.name} on {start_str}."
