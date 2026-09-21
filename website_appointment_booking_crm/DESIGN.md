# website_appointment_booking_crm — design notes

## Purpose

Glue between the public booking page and CRM: visitors whose working hours never overlap
the published slots can request a custom slot, which becomes a lead. Kept apart from
`website_appointment_booking` so the booking page does not depend on `crm`.

## How it plugs in

- `WebsiteAppointmentBookingCrm` subclasses the base controller. Odoo routes through the
  most specific controller class, so the overrides below apply to the same URLs:
  - `_prepare_booking_page_values` adds `show_request_banner` (visitor tz differs from
    the resource tz **and** none of the page's `padded_slots` falls between
    `_visitor_hours` over the next `_visitor_days`) and `request_success`.
  - `_get_error_message` adds the `missing_contact` code.
  - One new route, `POST /book/<slug>/request`, reusing the base helpers
    `_check_submission` (honeypot + reCAPTCHA, action
    `website_appointment_booking_request`), `_validate_tz` and `_get_or_create_partner`.
- The banner and its form are inserted by `xpath` before `.o_wab_calendar_row`; the form
  includes the base `booking_form_guard` template so the hidden guard fields stay in one
  place.
- Frontend: a public widget on `.o_wab_request_banner` toggles the form and attaches the
  base `FormGuard` with its own action name.

## Invariants

- The public user never owns the lead: `user_id` is forced to `False`.
- The lead description is built as plain text and converted with `plaintext2html`, so
  line breaks survive in the HTML field.
- The tag is a data record (`crm_tag_out_of_hours_request`), not looked up by name; a
  missing tag (deleted by a user) degrades to an untagged lead.
- Everything after the lead creation is best effort: the ntfy push is skipped when
  unconfigured and its failures are logged, the confirmation email is queued
  (`force_send=False`) and its failures are logged. The visitor always gets the success
  redirect once the lead exists.
- No vendor-specific defaults: ntfy server, topic and token come from
  `ir.config_parameter`; the email signs with the company name.

## Extension points

- `_visitor_hours`, `_visitor_days`: class attributes defining the "working hours"
  window used for the banner decision.
- `_prepare_lead_vals(...)`: override to route leads to a team, add UTM data, etc.
- `_publish_ntfy`, `_send_request_confirmation`: replace or extend the notification side
  channels.
