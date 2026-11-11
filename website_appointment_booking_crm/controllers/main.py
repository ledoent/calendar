# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import urllib.request
from datetime import datetime, timedelta, timezone

import pytz
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request
from odoo.tools.mail import email_normalize, plaintext2html

from odoo.addons.website_appointment_booking.controllers.main import (
    WebsiteAppointmentBooking,
)

_logger = logging.getLogger(__name__)

RECAPTCHA_ACTION_REQUEST = "website_appointment_booking_request"
# ir.config_parameter keys of the optional ntfy push notification
ICP_NTFY_BASE_URL = "website_appointment_booking_crm.ntfy_base_url"
ICP_NTFY_TOPIC = "website_appointment_booking_crm.ntfy_topic"
ICP_NTFY_TOKEN = "website_appointment_booking_crm.ntfy_token"


class WebsiteAppointmentBookingCrm(WebsiteAppointmentBooking):
    # Visitor-local window used to decide whether the published slots are
    # reachable: at least one slot between these hours over the next N days.
    _visitor_hours = (9, 17)
    _visitor_days = 7

    def _get_error_message(self, code):
        if code == "missing_contact":
            return request.env._("Name and email are required.")
        return super()._get_error_message(code)

    def _has_slots_in_visitor_window(self, slots, visitor_tz):
        """Does any slot fall in the visitor's local working hours soon?

        ``slots`` are tz-aware datetimes per day (the page's padded slots).
        Bails out at the first match.
        """
        try:
            tz = pytz.timezone(visitor_tz)
        except pytz.UnknownTimeZoneError:
            return True  # never show the banner on a tz the page did not accept
        hours_start, hours_end = self._visitor_hours
        now = datetime.now(timezone.utc).astimezone(tz)
        cutoff = now + timedelta(days=self._visitor_days)
        for day_slots in slots.values():
            for slot_dt in day_slots:
                local = slot_dt.astimezone(tz)
                if now <= local < cutoff and hours_start <= local.hour < hours_end:
                    return True
        return False

    def _prepare_booking_page_values(self, booking_type, year=None, month=None, **kw):
        values = super()._prepare_booking_page_values(booking_type, year, month, **kw)
        effective_tz = values["effective_tz"]
        # Visitors in the resource's own timezone never see the banner.
        values["show_request_banner"] = effective_tz != values[
            "resource_tz"
        ] and not self._has_slots_in_visitor_window(
            values["padded_slots"], effective_tz
        )
        values["request_success"] = kw.get("request_success") == "1"
        return values

    # ------------------------------------------------------------------
    # Lead creation
    # ------------------------------------------------------------------

    def _prepare_lead_vals(self, booking_type, partner, visitor_tz, preferred, note):
        description = request.env._(
            "Visitor requested an out-of-hours slot.\n\n"
            "For: %(type)s\n"
            "Visitor timezone: %(tz)s\n"
            "Preferred window: %(window)s\n\n"
            "Notes:\n%(note)s",
            type=booking_type.name,
            tz=visitor_tz,
            window=preferred or request.env._("(none specified)"),
            note=note or request.env._("(none)"),
        )
        tag = request.env.ref(
            "website_appointment_booking_crm.crm_tag_out_of_hours_request",
            raise_if_not_found=False,
        )
        return {
            "name": request.env._(
                "Out-of-hours request: %(type)s - %(name)s",
                type=booking_type.name,
                name=partner.name,
            ),
            "type": "lead",
            "contact_name": partner.name,
            "email_from": partner.email,
            "partner_id": partner.id,
            # The public user must not become the salesperson.
            "user_id": False,
            "description": plaintext2html(description),
            "tag_ids": [(4, tag.id)] if tag else False,
        }

    def _get_ntfy_config(self):
        """Return (url, token) of the ntfy topic, or None when not configured."""
        icp = request.env["ir.config_parameter"].sudo()
        base_url = (icp.get_param(ICP_NTFY_BASE_URL) or "").strip().rstrip("/")
        topic = (icp.get_param(ICP_NTFY_TOPIC) or "").strip().strip("/")
        if not base_url or not topic:
            return None
        return f"{base_url}/{topic}", icp.get_param(ICP_NTFY_TOKEN)

    @staticmethod
    def _safe_header(value, max_len=200):
        """Strip control characters from text flowing into an HTTP header."""
        if not value:
            return ""
        cleaned = "".join(c if c >= " " else " " for c in str(value)).strip()
        return cleaned[:max_len]

    def _publish_ntfy(self, lead, booking_type, visitor_tz, preferred_window):
        """Best-effort push notification about a new request.

        Silent no-op when the ntfy parameters are not set. Failures are
        logged and swallowed: the visitor-facing flow never depends on it.
        """
        config = self._get_ntfy_config()
        if not config:
            return
        url, token = config
        body = (
            f"{lead.contact_name or '(no name)'} <{lead.email_from}>\n"
            f"For: {booking_type.name}\n"
            f"Visitor TZ: {visitor_tz}\n"
            f"Preferred window: {preferred_window or '(none)'}"
        )
        base_url = request.httprequest.host_url.rstrip("/")
        click = f"{base_url}/odoo/crm.lead/{lead.id}"
        headers = {
            "Title": self._safe_header(
                f"Out-of-hours request: {lead.contact_name or lead.email_from}", 100
            ),
            "Tags": "earth_asia,inbox_tray",
            "Priority": "4",
            "Click": self._safe_header(click, 512),
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            req = urllib.request.Request(
                url, data=body.encode("utf-8"), headers=headers, method="POST"
            )
            urllib.request.urlopen(req, timeout=3)  # noqa: S310
        except Exception:  # pylint: disable=broad-except
            _logger.warning("ntfy publish failed for lead %s", lead.id, exc_info=True)

    def _send_request_confirmation(self, lead):
        template = request.env.ref(
            "website_appointment_booking_crm.mail_template_booking_request_confirmation",
            raise_if_not_found=False,
        )
        if not template:
            return
        try:
            template.sudo().send_mail(lead.id, force_send=False)
        except Exception:  # pylint: disable=broad-except
            _logger.warning(
                "booking-request confirmation email failed for lead %s",
                lead.id,
                exc_info=True,
            )

    @http.route(
        "/book/<slug>/request",
        auth="public",
        type="http",
        website=True,
        methods=["POST"],
        csrf=True,
        sitemap=False,
    )
    def booking_request(self, slug, **kwargs):
        """Submit an out-of-hours booking request.

        Creates a tagged ``crm.lead`` (no booking: the team opens a slot
        manually and replies), pushes an optional ntfy notification, sends
        a confirmation email to the visitor, and redirects back to the
        booking page with a success banner.
        """
        booking_type = self._get_booking_type(slug)
        if not booking_type:
            raise NotFound()
        rejection = self._check_submission(kwargs, RECAPTCHA_ACTION_REQUEST)
        if rejection:
            return self._redirect_error(slug, rejection)
        name = (kwargs.get("name") or "").strip()
        email = (kwargs.get("email") or "").strip()
        preferred = (kwargs.get("preferred_window") or "").strip()
        note = (kwargs.get("note") or "").strip()
        visitor_tz = self._validate_tz(kwargs.get("visitor_tz")) or "UTC"
        if not name or not email:
            return self._redirect_error(slug, "missing_contact")
        email = email_normalize(email)
        if not email:
            return self._redirect_error(slug, "invalid_email")

        partner = self._get_or_create_partner(name, email)
        lead = (
            request.env["crm.lead"]
            .sudo()
            .create(
                self._prepare_lead_vals(
                    booking_type, partner, visitor_tz, preferred, note
                )
            )
        )
        self._publish_ntfy(lead, booking_type, visitor_tz, preferred)
        self._send_request_confirmation(lead)
        return request.redirect(f"/book/{slug}?request_success=1")
