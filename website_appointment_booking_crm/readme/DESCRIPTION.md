This module extends the public booking page of `website_appointment_booking`
for visitors whose working hours do not overlap with the published calendar:
typically people on the other side of the world.

When the visitor's display timezone has no free slot between 9:00 and 17:00
local time over the next seven days, the page shows a banner offering to
request a custom slot. The request creates a CRM lead, tagged
**Out-of-hours request**, with the visitor's timezone, preferred window and
notes, sends the visitor a confirmation email and can push a notification to
an [ntfy](https://ntfy.sh) topic.

No booking is created: the team opens a slot manually and replies.
