This module sends an SMS notification to resource users (the people
whose time is being booked) whenever a resource booking is confirmed.

The SMS includes the requester name, the booking type and the
localised start time.

Sending is delegated to Odoo's ``sms.sms`` model, so whatever SMS
provider is configured (Odoo IAP, Twilio via ``sms_alternative_provider``,
etc.) is used transparently.
