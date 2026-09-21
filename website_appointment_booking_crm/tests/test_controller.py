# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from freezegun import freeze_time
from lxml.html import fromstring

from odoo.tests import tagged
from odoo.tests.common import HttpCase

from odoo.addons.resource_booking.tests.common import create_test_data

# The shared fixture has UTC calendars with Monday/Tuesday attendances from
# 08:00 to 17:00. Seen from Pacific/Auckland (UTC+13 in March 2021) those
# hours are 21:00 to 06:00: no overlap with a 9-to-5 working day, so a NZ
# visitor gets the request banner.


@freeze_time("2021-02-26 09:00:00", tick=True)
@tagged("post_install", "-at_install")
class TestWebsiteAppointmentBookingCrm(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_test_data(cls)
        cls.rbt.write({"is_published": True, "website_slug": "crm-test"})
        cls.tag = cls.env.ref(
            "website_appointment_booking_crm.crm_tag_out_of_hours_request"
        )

    def _url_xml(self, url, data=None, timeout=10):
        response = self.url_open(url, data, timeout=timeout)
        return fromstring(response.content)

    def _request(self, data):
        """POST the request form with a fresh CSRF token."""
        page = self._url_xml("/book/crm-test?tz=Pacific/Auckland")
        csrf = page.cssselect('input[name="csrf_token"]')[0].get("value")
        data = dict(data, csrf_token=csrf)
        return self.url_open("/book/crm-test/request", data=data, timeout=30)

    def _lead_for(self, email):
        return self.env["crm.lead"].search([("email_from", "=", email)], limit=1)

    def test_request_banner_hidden_for_resource_tz_visitor(self):
        """Domestic visitor (same tz as resource) never sees the banner."""
        page = self._url_xml("/book/crm-test/2021/3")
        self.assertFalse(page.cssselect(".o_wab_request_banner"))

    def test_request_banner_shown_for_far_tz_with_no_overlap(self):
        """A Pacific/Auckland visitor sees the banner and its (hidden) form."""
        page = self._url_xml("/book/crm-test/2021/3?tz=Pacific/Auckland")
        self.assertTrue(page.cssselect(".o_wab_request_banner"))
        forms = page.cssselect("form.o_wab_request_form")
        self.assertTrue(forms)
        self.assertIn("d-none", forms[0].get("class") or "")
        tz_inputs = page.cssselect('input[name="visitor_tz"]')
        self.assertEqual(tz_inputs[0].get("value"), "Pacific/Auckland")
        # Guard fields shared with the base module are present
        self.assertTrue(forms[0].cssselect(".o_wab_hp input[name]"))
        self.assertTrue(forms[0].cssselect("input[name='recaptcha_token_response']"))

    def test_booking_request_creates_tagged_lead(self):
        """POST /book/<slug>/request creates a tagged lead owned by nobody."""
        response = self._request(
            {
                "name": "NZ Requester",
                "email": "request-test@example.com",
                "preferred_window": "Tue/Thu 09:00-11:00 NZST",
                "note": "Need to chat about ERP migration",
                "visitor_tz": "Pacific/Auckland",
            }
        )
        self.assertIn("request_success=1", response.url)
        lead = self._lead_for("request-test@example.com")
        self.assertTrue(lead)
        self.assertEqual(lead.type, "lead")
        self.assertIn(self.tag, lead.tag_ids)
        self.assertFalse(lead.user_id, "the public user must not be the salesperson")
        self.assertEqual(lead.partner_id.email, "request-test@example.com")
        self.assertIn("Pacific/Auckland", lead.description)
        self.assertIn("Tue/Thu 09:00-11:00 NZST", lead.description)
        # plaintext2html kept the line structure
        self.assertIn("<br", lead.description)
        # Confirmation email queued for the visitor
        mails = self.env["mail.mail"].search(
            [
                ("mail_message_id.model", "=", "crm.lead"),
                ("mail_message_id.res_id", "=", lead.id),
            ]
        )
        self.assertTrue(mails)
        self.assertIn("request-test@example.com", mails[0].email_to)

    def test_booking_request_missing_name_redirects_with_error(self):
        """Submitting without name/email redirects with an error code."""
        response = self._request(
            {"name": "", "email": "incomplete@example.com", "visitor_tz": "UTC"}
        )
        self.assertIn("error=missing_contact", response.url)
        self.assertFalse(self._lead_for("incomplete@example.com"))
        page = self._url_xml("/book/crm-test?error=missing_contact")
        self.assertTrue(page.cssselect(".o_wab_error:contains('Name and email')"))

    def test_booking_request_invalid_email(self):
        response = self._request({"name": "Someone", "email": "nope"})
        self.assertIn("error=invalid_email", response.url)

    def test_booking_request_honeypot_rejected(self):
        """A filled honeypot rejects the request without creating anything."""
        response = self._request(
            {
                "name": "Bot",
                "email": "bot-request@example.com",
                "company_website": "http://spam.example.com",
            }
        )
        self.assertIn("error=rejected", response.url)
        self.assertFalse(self._lead_for("bot-request@example.com"))
        self.assertFalse(
            self.env["res.partner"].search([("email", "=", "bot-request@example.com")])
        )

    def test_booking_request_success_banner_renders(self):
        """After ?request_success=1, the success banner appears."""
        page = self._url_xml("/book/crm-test?request_success=1")
        self.assertTrue(page.cssselect(".o_wab_success_banner"))
