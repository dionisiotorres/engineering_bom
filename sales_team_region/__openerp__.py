# -*- coding: utf-8 -*-
# Copyright 2014-2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Sales Team Regions",
    "summary": "Define sales regions.",
    "version": "9.0.1.0.0",
    "category": "Sales",
    "website": "http://www.github.com/asphaltzipper/azi-odoo-modules",
    "author": "scosist",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["crm"],
    "data": [
        'security/ir.model.access.csv',
        'views/crm_team_view.xml',
        'views/res_partner_view.xml',
        'views/sales_team_region_view.xml',
    ],
    "demo": [
    ],
}
