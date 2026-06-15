1. Install this module alongside ``resource_booking`` and ``sms``.
2. Ensure at least one SMS provider is configured (Odoo IAP by default,
   or a third-party gateway like Twilio via ``sms_alternative_provider``).
3. Make sure the resource users linked to your booking combinations have
   a **Mobile** or **Phone** number on their partner record.

When a booking is confirmed (via ``action_confirm()``), an SMS is
automatically sent to each resource user that has a phone number.
