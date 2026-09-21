/* Copyright 2025 Ledo Enterprises LLC - Don Kendall
 * Copyright 2026 ForgeFlow S.L.
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

/**
 * Out-of-hours request banner: the "Request a custom slot" call to action
 * shown on the booking page when the visitor's timezone has no overlap with
 * the published booking hours. A sibling of the calendar widget, so its
 * toggle state is independent.
 */

/* eslint-env browser */
import {FormGuard} from "@website_appointment_booking/js/form_guard.esm";
import publicWidget from "@web/legacy/js/public/public_widget";

export const RECAPTCHA_ACTION = "website_appointment_booking_request";

publicWidget.registry.WebsiteAppointmentRequestBanner = publicWidget.Widget.extend({
    selector: ".o_wab_request_banner",
    events: {
        "click .o_wab_request_toggle": "_onToggle",
    },

    /**
     * @override
     */
    start() {
        this.guard = new FormGuard(RECAPTCHA_ACTION);
        this.guard.attach(this.el.querySelector("#o_wab_request_form"));
        return this._super(...arguments);
    },

    _onToggle(ev) {
        const form = this.el.querySelector("#o_wab_request_form");
        if (!form) {
            return;
        }
        form.classList.remove("d-none");
        // Hide the toggle once the form is open so a second click cannot
        // collapse it while the visitor is mid-fill.
        ev.currentTarget.setAttribute("disabled", "disabled");
        ev.currentTarget.classList.add("d-none");
        const nameInput = form.querySelector("#o_wab_request_name");
        if (nameInput) {
            nameInput.focus();
        }
    },
});
