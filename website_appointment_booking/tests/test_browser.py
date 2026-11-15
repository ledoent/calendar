# Copyright 2026 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from freezegun import freeze_time

from odoo.tests import HttpCase, tagged

from odoo.addons.resource_booking.tests.common import create_test_data


@freeze_time("2021-02-26 09:00:00", tick=True)
@tagged("post_install", "-at_install")
class TestBookingInteractions(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_test_data(cls)
        cls.rbt.write(
            {
                "is_published": True,
                "website_slug": "interaction-test",
                "website_description": (
                    '<details id="booking-about"><summary>About</summary>'
                    "<p>Consultation details</p></details>"
                    '<details id="booking-prepare"><summary>Prepare</summary>'
                    "<p>Bring your questions</p></details>"
                ),
            }
        )

    def test_description_and_calendar_start_together(self):
        """A description must not abort website interaction initialization."""
        self.browser_js(
            "/book/interaction-test/2021/3",
            """
            (async () => {
                const about = document.querySelector('#booking-about');
                const prepare = document.querySelector('#booking-prepare');
                about.open = true;
                about.dispatchEvent(new Event('toggle'));
                prepare.open = true;
                prepare.dispatchEvent(new Event('toggle'));
                if (about.open || !prepare.open) {
                    throw new Error('Description sections must close their siblings');
                }
                const day = document.querySelector('.o_wab_day_available');
                if (!day) {
                    throw new Error('Expected an available booking day');
                }
                day.click();
                // Colibri binds the newly rendered slot buttons after the handler.
                await new Promise((resolve) => requestAnimationFrame(resolve));
                const slot = document.querySelector('.o_wab_slot_btn');
                if (!slot) {
                    throw new Error('Selecting a day must display time slots');
                }
                slot.click();
                const formHidden = document.querySelector('#o_wab_form')
                    .classList.contains('d-none');
                if (!document.querySelector('#o_wab_when').value || formHidden) {
                    throw new Error('Selecting a slot must display the booking form');
                }
                console.log('test successful');
            })();
            """,
            ready="document.body.getAttribute('is-ready') === 'true'",
        )
