{
    'name': 'Sprint Board',
    'version': '19.0.2.2.0',
    'category': 'Project/Project',
    'summary': 'Visual sprint dashboard with KPIs, AI analysis and kiosk mode',
    'description': """
        Sprint Board transforms your Odoo project sprints into a real-time visual command centre.
        See every task at a glance, let the AI sort priorities and generate smart recommendations,
        track completion with live KPIs, share the board on any screen via kiosk mode, and close
        each sprint with an AI-generated retrospective — all without leaving Odoo.
    """,
    'license': 'LGPL-3',
    'author': "Todooweb (www.todooweb.com)",
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': [
        'project',
        'mail',
    ],
    # Optional OCA integrations — install separately to enable extra features:
    #   project_type       → task type classification (type_id field on tasks)
    #                        https://github.com/OCA/project/tree/19.0/project_type
    #   project_department → department filtering in board views
    #                        https://github.com/OCA/project/tree/19.0/project_department
    # The module works without them; these fields are accessed with getattr() fallbacks.
    'data': [
        'security/sprint_board_security.xml',
        'security/ir.model.access.csv',
        'views/project_sprint_views.xml',
        'views/report_sprint_views.xml',
        'views/project_sprint_menu.xml',
        'views/project_task_views.xml',
        'views/sprint_board_actions.xml',
        'views/res_config_settings_views.xml',
        'views/kiosk_templates.xml',
        'data/sprint_sequence.xml',
        'data/sprint_burndown_cron.xml',
        'data/cron_missing_board.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'todoo_sprint_board_project/static/src/components/SprintBoardAction/SprintBoardAction.js',
            'todoo_sprint_board_project/static/src/components/SprintBoardAction/SprintBoardAction.xml',
            'todoo_sprint_board_project/static/src/components/SprintBoardList/SprintBoardList.js',
            'todoo_sprint_board_project/static/src/components/SprintBoardList/SprintBoardList.xml',
            'todoo_sprint_board_project/static/src/components/SprintBoardDashboard/SprintBoardDashboard.js',
            'todoo_sprint_board_project/static/src/components/SprintBoardDashboard/SprintBoardDashboard.xml',
            'todoo_sprint_board_project/static/src/components/AIModelSelector/AIModelSelector.js',
            'todoo_sprint_board_project/static/src/components/AIModelSelector/AIModelSelector.xml',
            'todoo_sprint_board_project/static/src/scss/sprint_board.scss',
        ],
    },
    'images': ['static/description/screenshoot_sprint.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 49.99,
    'currency': 'EUR',
}
