Once a booking type is published:

1. Share the URL `/book/<slug>` with your clients or embed it on your website.
2. Visitors see a monthly calendar with available days highlighted. `/book/<slug>`
   opens on the first month that has availability rather than on the current
   month, so a booking type whose slots start later — an event, or a resource
   booked solid for several weeks — does not greet visitors with an empty grid
   and leave them guessing how far forward to click. The search looks up to
   twelve months ahead; if nothing is found in that window the current month is
   shown with its empty state. A URL that names a month explicitly, such as
   `/book/<slug>/2026/10`, is always honoured as given, so the previous/next
   arrows and the browser's back button behave normally.
3. Clicking a day reveals the available time slots for that day.
4. Clicking a time slot shows a simple form asking for name and email.
5. Upon confirmation, a `resource.booking` record is created and confirmed
   automatically, and calendar invitations are sent to both parties.
6. If a slot is no longer available (race condition), the visitor is redirected
   back to the calendar with an informative error message.
