from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    estimator_url = fields.Char(
        string='Estimator external',
        config_parameter='todoo_task_estimator.url',
        help='URL of the external task-estimator server '
             '(e.g. http://localhost:3000 or https://estimator.yourcompany.com)',
        placeholder='http://localhost:3000',
    )
    estimator_api_key = fields.Char(
        string='API estimator',
        config_parameter='todoo_task_estimator.api_key',
        help='API key to authenticate requests to the task-estimator server. '
             'Leave empty if the server has no API_KEY configured (open/dev mode).',
        placeholder='optional',
    )
