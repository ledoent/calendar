# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Website Appointment Booking - CRM",
    "summary": "Turn out-of-hours booking requests from the public "
    "booking page into CRM leads",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "category": "Appointments",
    "website": "https://github.com/OCA/calendar",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "maintainers": ["JordiBForgeFlow"],
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "website_appointment_booking",
        "crm",
    ],
    "data": [
        "data/crm_tag_data.xml",
        "data/mail_template_data.xml",
        "templates/booking.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_appointment_booking_crm/static/src/scss/request_banner.scss",
            "website_appointment_booking_crm/static/src/js/request_banner.esm.js",
        ],
    },
}
