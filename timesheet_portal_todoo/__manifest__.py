{
    "name": "Timesheet Portal",
    "version": "16.0.1.0.0",
    "category": "Website/Website",

    "summary": """
        Website portal for User External
    """,
    "description": """
        "Timesheet Portal" module streamlines time tracking through an intuitive interface, allowing effortless creation, editing, and deletion of timesheets.
    """,
    "license": "LGPL-3",
    "author": "Todooweb (www.todooweb.com)",
    "website": "https://todooweb.com/",
    "contributors": [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    "support": 'devtodoo@gmail.com',
    "depends": ["base", "website", "timesheet_grid", "hr_timesheet", "project",  "hr", "contacts"],
    "data": [
        'views/portal_templates_views.xml'
    ],
    "assets": {
        "web.assets_frontend": [
            "timesheet_portal_todoo/static/src/js/portal.js"
        ]
    },
    'installable': True,
    'application': False,
    'images': ['static/description/screenshot_time.png'],
    'auto_install': False,
    'price': 35,
    'currency': "EUR"
}
