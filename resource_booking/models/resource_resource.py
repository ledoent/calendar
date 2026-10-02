# Copyright 2021 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models

from .resource_booking import _availability_is_fitting


class ResourceResource(models.Model):
    _inherit = "resource.resource"

    @api.constrains("calendar_id", "resource_type", "tz", "user_id")
    def _check_bookings_scheduling(self):
        """Scheduled bookings must have no conflicts."""
        bookings = (
            self.env["resource.booking"]
            .sudo()
            .search([("combination_id.resource_ids", "in", self.ids)])
        )
        return bookings._check_scheduling()

    def is_available(self, start_dt, end_dt, domain=None, tz=None):
        """Convenience method to check whether a resource is available within a
        time span.
        """
        self.ensure_one()
        # the `analyzing_booking` context needs to be added here, or bookings
        # are not marked as busy. Because we do not actually have a booking_id
        # available here, we set the value to -1.
        result = self.calendar_id.with_context(
            analyzing_booking=-1
        )._work_intervals_batch(
            start_dt,
            end_dt,
            # `{None: self}` would be truthy, so core's own
            # `if not resources_per_tz` fallback never fires and it ends up
            # comparing an aware start_dt.astimezone(None) with a naive
            # val[0].replace(tzinfo=None). 19.0 resolved the empty case itself
            # as `tz or timezone(resource.tz)`; 20.0 expects the caller to do
            # it, which is what _get_resources_per_tz is for.
            resources_per_tz={tz: self} if tz else self._get_resources_per_tz(),
            domain=domain,
        )[self.id]
        return _availability_is_fitting(result, start_dt, end_dt)
