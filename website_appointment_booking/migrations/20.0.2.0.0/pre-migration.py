# Copyright 2026 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Carry the publish flag onto ``website.published.mixin``.

The addon used to declare its own stored ``website_published`` Boolean. It now
inherits ``website.published.mixin``, whose stored column is ``is_published``
(``website_published`` survives only as that mixin's related alias). Without
this rename every already-published booking type would come back unpublished,
because ``is_published`` would be created fresh and defaults to False — the
public ``/book/<slug>`` pages would start returning 404.

Runs pre-migration, i.e. before the ORM creates ``is_published``, so the guard
is column existence rather than emptiness and cannot be defeated by the new
column's default.

``rename_columns`` and not ``rename_fields``: ``website_published`` must keep
its ``ir.model.fields`` row to go on working as the mixin's related field.
"""

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(
        env.cr, "resource_booking_type", "website_published"
    ) and not openupgrade.column_exists(
        env.cr, "resource_booking_type", "is_published"
    ):
        openupgrade.rename_columns(
            env.cr,
            {"resource_booking_type": [("website_published", "is_published")]},
        )
