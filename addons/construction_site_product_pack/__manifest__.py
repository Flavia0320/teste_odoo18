# Copyright 2023 Dakai SoftSRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).
{
    "name": "Construction Site Product Pack",
    "summary": "Construction Site Product Pack",
    "version": "18.0.1.0.0",
    "category": "Construction",
    "website": "https://dakai.ro",
    "author": "Dakai SOFT SRL",
    "maintainers": ["adrian-dks","feketemihai"],
    "license": "OPL-1",
    "installable": True,
    "depends": [
        'construction_site',
        'product_pack_addons_stock',
    ],
    "data": [
        "views/project_task_view.xml",
    ],
}
