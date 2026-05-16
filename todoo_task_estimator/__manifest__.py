{
    'name': 'Task Estimator Integration',
    'version': '17.0.2.0.0',
    'category': 'Project/Project',
    'summary': 'Direct API integration with task-estimator',
    'description': """
        Integrates Odoo project tasks with task-estimator via REST API.
        Click Estimate to open the estimator UI with the task pre-loaded.
        Previous estimations are shown so you can re-estimate.
        Results are sent back to Odoo and saved to the task automatically.
    """,
    'license': 'LGPL-3',
    'author': "Todooweb (www.todooweb.com)",
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': ['project', 'mail'],
    'data': [
        'data/ir_config_parameter.xml',
        'views/res_config_settings_views.xml',
        'views/project_task_views.xml',
    ],
    'images': ['static/description/screenshot_task.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 29.99,
    'currency': 'EUR',
}
