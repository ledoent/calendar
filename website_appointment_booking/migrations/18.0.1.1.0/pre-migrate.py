# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Dropping stale manual avatar relation tables...")

    # The website_card_user_ids and website_card_resource_ids fields were
    # previously stored Many2manys with manual relation tables. They are now
    # computed fields, so the old tables are orphaned.
    tables_to_drop = [
        "resource_booking_type_website_card_user_rel",
        "resource_booking_type_website_card_resource_rel",
    ]
    for table in tables_to_drop:
        cr.execute(
            """
            SELECT tablename FROM pg_tables WHERE tablename = %s
            """,
            (table,),
        )
        if cr.fetchone():
            cr.execute(f"DROP TABLE {table} CASCADE")
            _logger.info("Dropped stale table: %s", table)
        else:
            _logger.info("Table already gone: %s", table)
