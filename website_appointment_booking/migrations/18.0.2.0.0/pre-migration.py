# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""``website_published`` became the related field of ``website.published.mixin``;
the stored flag now lives in ``is_published``. Carry the values over."""


def migrate(cr, version):
    cr.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'resource_booking_type'
          AND column_name IN ('website_published', 'is_published')
        """
    )
    columns = {row[0] for row in cr.fetchall()}
    if "website_published" in columns and "is_published" not in columns:
        cr.execute(
            "ALTER TABLE resource_booking_type "
            "RENAME COLUMN website_published TO is_published"
        )
