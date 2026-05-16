import json
import logging

from odoo import http, SUPERUSER_ID
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class EstimatorSaveController(http.Controller):

    @http.route(
        '/todoo_task_estimator/api/save',
        type='http', auth='none', methods=['POST'],
        cors='*', csrf=False,
    )
    def api_save(self, **kwargs):
        """Receives estimation result from task-estimator server (server-to-server).

        Authentication: X-Estimator-Key header must match
        'todoo_task_estimator.api_key' system parameter.
        Called only by task-estimator proxy — never directly from browser.
        """
        expected_key = request.env['ir.config_parameter'].sudo().get_param(
            'todoo_task_estimator.api_key', ''
        )
        received_key = request.httprequest.headers.get('X-Estimator-Key', '')
        if not expected_key:
            _logger.warning(
                'todoo_task_estimator.api_key is not configured — '
                '/todoo_task_estimator/api/save is unauthenticated!'
            )
        elif received_key != expected_key:
            return Response(
                json.dumps({'error': 'Unauthorized'}),
                content_type='application/json', status=401,
            )

        try:
            body = json.loads(request.httprequest.data.decode('utf-8'))
        except (json.JSONDecodeError, TypeError, ValueError):
            return Response(
                json.dumps({'error': 'Invalid JSON body'}),
                content_type='application/json', status=400,
            )

        task_id = body.get('task_id')
        data = body.get('data')
        if not task_id or not isinstance(data, dict):
            return Response(
                json.dumps({'error': 'task_id and data are required'}),
                content_type='application/json', status=400,
            )
        try:
            task_id = int(task_id)
        except (TypeError, ValueError):
            return Response(
                json.dumps({'error': 'task_id must be an integer'}),
                content_type='application/json', status=400,
            )

        try:
            request.env['project.task'].with_user(SUPERUSER_ID).save_estimation(
                task_id, data
            )
        except Exception:
            _logger.exception('Error saving estimation for task_id %s', task_id)
            return Response(
                json.dumps({'error': 'Internal server error saving estimation'}),
                content_type='application/json', status=500,
            )

        return Response(
            json.dumps({'ok': True}),
            content_type='application/json',
        )
