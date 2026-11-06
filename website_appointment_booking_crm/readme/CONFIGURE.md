The feature works out of the box once a booking type is published.

Optional push notification through ntfy: set these system parameters
(**Settings > Technical > Parameters > System Parameters**):

- ``website_appointment_booking_crm.ntfy_base_url``: the ntfy server, e.g.
  ``https://ntfy.sh``
- ``website_appointment_booking_crm.ntfy_topic``: the topic to publish to
- ``website_appointment_booking_crm.ntfy_token``: optional bearer token

Nothing is pushed while the base URL or the topic is missing.

The visitor confirmation email is the template **Out-of-Hours Booking
Request: Visitor Confirmation**; it is sent from the company email address.

If the website has a reCAPTCHA v3 key configured, the request form is verified
with the action name ``website_appointment_booking_request``.
