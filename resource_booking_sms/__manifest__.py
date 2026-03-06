# Copyright 2025 Ledo Enterprises LLC - Don Kendall
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Resource Booking SMS",
    "summary": "Send SMS notifications to resource users on booking confirmation",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "category": "Appointments",
    "website": "https://github.com/OCA/calendar",
    "author": "Ledo Enterprises LLC, Odoo Community Association (OCA)",
    "maintainers": ["dnplkndll"],
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "resource_booking",
        "sms",
    ],
}
