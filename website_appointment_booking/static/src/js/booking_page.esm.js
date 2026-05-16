/* Copyright 2025 Ledo Enterprises LLC - Don Kendall
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

/**
 * Public booking page interactivity.
 *
 * Uses Odoo's publicWidget system so that the widget initializes correctly
 * with deferred/lazy asset loading in Odoo 18. Reads slot data from a
 * hidden data attribute rendered server-side and handles day/slot
 * selection without additional network requests.
 */

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.WebsiteAppointmentBooking = publicWidget.Widget.extend({
    selector: ".o_wab_calendar",
    events: {
        "click .o_wab_day_available": "_onDayClick",
        "click .o_wab_slot_btn": "_onSlotClick",
        "change .o_wab_timezone_select": "_onTimezoneChange",
        "click .o_wab_combination_btn": "_onCombinationClick",
    },

    /**
     * @override
     */
    start() {
        this.dataEl = this.el.querySelector("#o_wab_slot_data");
        if (!this.dataEl) {
            return this._super(...arguments);
        }
        this.panel = this.el.querySelector("#o_wab_slots_panel");
        this.slotsTitle = this.panel
            ? this.panel.querySelector(".o_wab_slots_title")
            : null;
        this.slotsList = this.panel
            ? this.panel.querySelector(".o_wab_slots_list")
            : null;
        this.form = this.el.querySelector("#o_wab_form");
        this.whenInput = this.el.querySelector("#o_wab_when");
        this.selectedDisplay = this.el.querySelector("#o_wab_selected_display");
        this.slotsEmpty = this.el.querySelector("#o_wab_slots_empty");
        this.timezoneSelect = this.el.querySelector("#o_wab_timezone");
        this.timezoneInput = this.el.querySelector('input[name="tz"]');
        this.combinationInput = this.el.querySelector('input[name="combination_id"]');
        this.slotEndpoint = this.dataEl.dataset.slotEndpoint;
        this.displayedYear = this.dataEl.dataset.year;
        this.displayedMonth = this.dataEl.dataset.month;
        this._setSlotData(
            JSON.parse(this.dataEl.dataset.slots || "[]"),
            this.dataEl.dataset.selectedTz || "UTC",
            this.dataEl.dataset.selectedCombinationId || ""
        );
        return this._super(...arguments);
    },

    _setSlotData(slotData, timezone, combinationId = "") {
        this.allSlots = slotData;
        this.selectedTimezone = timezone;
        this.selectedCombinationId = combinationId ? String(combinationId) : "";
        this.slotsByDate = {};
        this.availableDates = new Set();
        for (const slot of this.allSlots) {
            if (!this.slotsByDate[slot.date]) {
                this.slotsByDate[slot.date] = [];
            }
            this.slotsByDate[slot.date].push(slot);
            this.availableDates.add(slot.date);
        }
        this.dataEl.dataset.slots = JSON.stringify(this.allSlots);
        this.dataEl.dataset.selectedTz = this.selectedTimezone;
        this.dataEl.dataset.selectedCombinationId = this.selectedCombinationId;
        this._syncCombinationButtons();
    },

    _syncCombinationButtons(disabled = false) {
        this.el.querySelectorAll(".o_wab_combination_btn").forEach((button) => {
            const combinationId = button.dataset.combinationId || "";
            const isActive = combinationId === this.selectedCombinationId;
            button.classList.toggle("active", isActive);
            button.setAttribute("aria-pressed", isActive ? "true" : "false");
            button.disabled = disabled;
        });
    },

    _resetSelection() {
        this.el.querySelectorAll(".o_wab_day_selected").forEach((el) => {
            el.classList.remove("o_wab_day_selected");
        });
        if (this.panel) {
            this.panel.classList.add("d-none");
        }
        if (this.slotsList) {
            this.slotsList.innerHTML = "";
        }
        if (this.slotsTitle) {
            this.slotsTitle.textContent = "";
        }
        if (this.slotsEmpty) {
            this.slotsEmpty.classList.remove("d-none");
        }
        if (this.form) {
            this.form.classList.add("d-none");
        }
        if (this.whenInput) {
            this.whenInput.value = "";
        }
        if (this.selectedDisplay) {
            this.selectedDisplay.textContent = "";
        }
    },

    _refreshAvailableDays() {
        this.el.querySelectorAll(".o_wab_day").forEach((dayEl) => {
            const date = dayEl.dataset.date;
            if (!date) {
                return;
            }
            dayEl.classList.toggle("o_wab_day_available", this.availableDates.has(date));
            if (!this.availableDates.has(date)) {
                dayEl.classList.remove("o_wab_day_selected");
            }
        });
    },

    _getDayElement(date) {
        return this.el.querySelector(`.o_wab_day[data-date="${date}"]`);
    },

    _getSelectedDate() {
        return this.el.querySelector(".o_wab_day_selected")?.dataset.date || null;
    },

    _restoreSelectedDate(date) {
        if (!date || !this.availableDates.has(date)) {
            return false;
        }
        return this._showDateSlots(date, {
            dayEl: this._getDayElement(date),
        });
    },

    _showDateSlots(date, {dayEl = null, scroll = false} = {}) {
        const selectedDay = dayEl || this._getDayElement(date);
        if (!date || !selectedDay || !this.slotsByDate[date]) {
            return false;
        }

        this.el.querySelectorAll(".o_wab_day_selected").forEach((el) => {
            el.classList.remove("o_wab_day_selected");
        });
        selectedDay.classList.add("o_wab_day_selected");

        const dateObj = new Date(date + "T00:00:00");
        const dateStr = dateObj.toLocaleDateString(undefined, {
            weekday: "long",
            month: "long",
            day: "numeric",
        });

        if (this.slotsTitle) {
            this.slotsTitle.textContent = dateStr;
        }
        if (this.slotsList) {
            this.slotsList.innerHTML = "";
            for (const slot of this.slotsByDate[date]) {
                const btn = this.el.ownerDocument.createElement("button");
                btn.type = "button";
                btn.className = "o_wab_slot_btn";
                btn.textContent = slot.time;
                btn.dataset.iso = slot.iso;
                btn.dataset.display = dateStr + " at " + slot.time;
                this.slotsList.appendChild(btn);
            }
        }
        if (this.panel) {
            this.panel.classList.remove("d-none");
        }
        if (this.slotsEmpty) {
            this.slotsEmpty.classList.add("d-none");
        }
        if (this.form) {
            this.form.classList.add("d-none");
        }
        if (scroll && this.panel) {
            this.panel.scrollIntoView({behavior: "smooth", block: "nearest"});
        }
        return true;
    },

    _updateSelectionLinks() {
        this.el.querySelectorAll(".o_wab_month_link").forEach((link) => {
            const url = new URL(link.href, window.location.origin);
            url.searchParams.set("tz", this.selectedTimezone);
            if (this.selectedCombinationId) {
                url.searchParams.set("combination_id", this.selectedCombinationId);
            } else {
                url.searchParams.delete("combination_id");
            }
            link.href = url.toString();
        });
    },

    async _fetchSlotData(timezone, combinationId = "") {
        const url = new URL(this.slotEndpoint, window.location.origin);
        url.searchParams.set("year", this.displayedYear);
        url.searchParams.set("month", this.displayedMonth);
        url.searchParams.set("tz", timezone);
        if (combinationId) {
            url.searchParams.set("combination_id", combinationId);
        }
        const response = await fetch(url.toString(), {
            headers: {Accept: "application/json"},
        });
        if (!response.ok) {
            throw new Error(`Failed to refresh booking slots (${response.status})`);
        }
        return response.json();
    },

    // -------------------------------------------------------------------------
    // Handlers
    // -------------------------------------------------------------------------

    /**
     * Handle click on an available calendar day.
     *
     * @param {Event} ev
     */
    _onDayClick(ev) {
        this._showDateSlots(ev.currentTarget.dataset.date, {
            dayEl: ev.currentTarget,
            scroll: true,
        });
    },

    /**
     * Handle click on a time slot button.
     *
     * @param {Event} ev
     */
    _onSlotClick(ev) {
        const btn = ev.currentTarget;

        if (this.panel) {
            this.panel.querySelectorAll(".o_wab_slot_btn").forEach((el) => {
                el.classList.remove("active");
            });
        }
        btn.classList.add("active");

        if (this.whenInput) {
            this.whenInput.value = btn.dataset.iso;
        }
        if (this.selectedDisplay) {
            this.selectedDisplay.textContent = btn.dataset.display;
        }
        if (this.form) {
            this.form.classList.remove("d-none");
            this.form.scrollIntoView({behavior: "smooth", block: "nearest"});
        }
    },

    async _applySelectionChange({timezone, combinationId, fallbackUrl}) {
        const selectedDate = this._getSelectedDate();
        try {
            const data = await this._fetchSlotData(timezone, combinationId);
            this._setSlotData(
                data.slot_data || [],
                data.selected_tz || timezone,
                data.selected_combination_id || ""
            );
            if (this.timezoneInput) {
                this.timezoneInput.value = this.selectedTimezone;
            }
            if (this.combinationInput) {
                this.combinationInput.value = this.selectedCombinationId;
            }
            this._refreshAvailableDays();
            this._updateSelectionLinks();
            this._resetSelection();
            this._restoreSelectedDate(selectedDate);
            const url = new URL(window.location.href);
            url.searchParams.set("tz", this.selectedTimezone);
            if (this.selectedCombinationId) {
                url.searchParams.set("combination_id", this.selectedCombinationId);
            } else {
                url.searchParams.delete("combination_id");
            }
            window.history.replaceState({}, "", url.toString());
        } catch (_error) {
            window.location.assign(fallbackUrl);
        }
    },

    /**
     * Refresh slot data in-place for the selected timezone.
     *
     * @param {Event} ev
     */
    async _onTimezoneChange(ev) {
        const timezone = ev.currentTarget.value;
        if (!timezone || timezone === this.selectedTimezone) {
            return;
        }
        const combinationId = this.selectedCombinationId;
        ev.currentTarget.disabled = true;
        try {
            await this._applySelectionChange({
                timezone,
                combinationId,
                fallbackUrl:
                    `${window.location.pathname}?tz=${encodeURIComponent(timezone)}` +
                    (combinationId
                        ? `&combination_id=${encodeURIComponent(combinationId)}`
                        : ""),
            });
        } finally {
            ev.currentTarget.disabled = false;
        }
    },

    /**
     * Refresh slot data in-place for the selected resource combination.
     *
     * @param {Event} ev
     */
    async _onCombinationClick(ev) {
        const combinationId = ev.currentTarget.dataset.combinationId || "";
        if (combinationId === this.selectedCombinationId) {
            return;
        }
        this._syncCombinationButtons(true);
        try {
            await this._applySelectionChange({
                timezone: this.selectedTimezone,
                combinationId,
                fallbackUrl:
                    `${window.location.pathname}?tz=${encodeURIComponent(this.selectedTimezone)}` +
                    (combinationId
                        ? `&combination_id=${encodeURIComponent(combinationId)}`
                        : ""),
            });
        } finally {
            this._syncCombinationButtons(false);
        }
    },
});
