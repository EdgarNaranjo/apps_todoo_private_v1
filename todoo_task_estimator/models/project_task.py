import json
import re
import html as html_lib
import logging
import urllib.parse

import requests as req_lib

from markupsafe import Markup, escape
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    estimator_pts_manual = fields.Integer(
        string='Manual Points',
        default=0,
        help='Story points estimated without AI',
    )
    estimator_pts_ia = fields.Integer(
        string='AI Points',
        default=0,
        help='Story points estimated with AI',
    )
    estimator_data = fields.Text(
        string='Estimation Data',
        help='Full JSON returned by task-estimator',
    )
    has_estimation = fields.Boolean(
        string='Has Estimation',
        compute='_compute_has_estimation',
        store=False,
    )

    @api.depends('estimator_pts_manual', 'estimator_pts_ia')
    def _compute_has_estimation(self):
        for rec in self:
            rec.has_estimation = bool(rec.estimator_pts_manual or rec.estimator_pts_ia)

    def action_estimate(self):
        """Calls task-estimator API directly (no browser needed)."""
        self.ensure_one()
        params = self.env['ir.config_parameter'].sudo()
        estimator_url = params.get_param(
            'todoo_task_estimator.url', 'http://localhost:3000'
        ).rstrip('/')
        api_key = params.get_param('todoo_task_estimator.api_key', '')

        description = self._get_plain_description()
        if not description:
            raise UserError(
                "The task has no description. "
                "Add a description before estimating."
            )

        headers = {'Content-Type': 'application/json'}
        if api_key:
            headers['X-API-Key'] = api_key

        try:
            response = req_lib.post(
                f"{estimator_url}/api/v1/estimate",
                json={'task': description},
                headers=headers,
                timeout=120,
            )
        except req_lib.exceptions.ConnectionError:
            raise UserError(
                f"Cannot connect to task-estimator at {estimator_url}. "
                "Check that the server is running."
            )
        except req_lib.exceptions.Timeout:
            raise UserError(
                "The server took too long to respond (timeout 120s). "
                "Please try again."
            )

        if response.status_code == 401:
            raise UserError(
                "API key incorrect or not configured. "
                "Check Settings > Task Estimator > API estimator."
            )
        if response.status_code == 422:
            try:
                detail = response.json().get('error', 'Invalid task')
            except Exception:
                detail = response.text[:200]
            raise UserError(f"Task rejected by estimator: {detail}")
        if not response.ok:
            raise UserError(
                f"task-estimator server error (HTTP {response.status_code}): "
                f"{response.text[:200]}"
            )

        try:
            data = response.json()
        except Exception:
            raise UserError(
                f"Invalid response from estimator: {response.text[:200]}"
            )
        self.save_estimation(self.id, data)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_open_estimator_ui(self):
        """Creates a UI session in task-estimator and opens it in a new tab."""
        self.ensure_one()
        params = self.env['ir.config_parameter'].sudo()
        estimator_url = params.get_param(
            'todoo_task_estimator.url', 'http://localhost:3000'
        ).rstrip('/')
        api_key = params.get_param('todoo_task_estimator.api_key', '')
        odoo_url = params.get_param('web.base.url', 'http://localhost:8069')

        description = self._get_plain_description()

        previous_data = None
        if self.estimator_data:
            try:
                previous_data = json.loads(self.estimator_data)
            except (json.JSONDecodeError, TypeError):
                pass

        headers = {'Content-Type': 'application/json'}
        if api_key:
            headers['X-API-Key'] = api_key

        try:
            response = req_lib.post(
                f"{estimator_url}/api/v1/session",
                json={
                    'task': description,
                    'previous_data': previous_data,
                    'odoo_url': odoo_url.rstrip('/'),
                    'task_id': self.id,
                    'odoo_api_key': api_key,
                },
                headers=headers,
                timeout=10,
            )
        except (req_lib.exceptions.ConnectionError, req_lib.exceptions.Timeout) as e:
            _logger.warning(
                'Could not reach task-estimator session endpoint: %s. '
                'Falling back to ?prefill=', e
            )
            ui_url = (
                f"{estimator_url}/"
                f"?prefill={urllib.parse.quote(description or '')}"
            )
        else:
            if response.status_code in (401, 403):
                raise UserError(
                    "API key incorrect or not configured. "
                    "Check Settings > Task Estimator > API estimator."
                )
            response.raise_for_status()
            ui_url = response.json()['url']

        return {
            'type': 'ir.actions.act_url',
            'url': ui_url,
            'target': 'new',
        }

    @api.model
    def save_estimation(self, task_id, data):
        """Saves estimation result to task fields and posts to chatter."""
        task = self.browse(task_id)
        if not task.exists():
            _logger.warning('save_estimation: task_id %s not found', task_id)
            return False
        if not isinstance(data, dict):
            _logger.warning('save_estimation: invalid data type %s', type(data))
            return False
        task.write({
            'estimator_pts_manual': int(data.get('manual') or 0),
            'estimator_pts_ia': int(data.get('con_ia') or 0),
            'estimator_data': json.dumps(data, ensure_ascii=False),
        })
        body = task._format_estimation_message(data)
        task.message_post(
            body=body,
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )
        return True

    def _get_plain_description(self):
        return self._strip_html(self.description or '')

    @staticmethod
    def _strip_html(html_content):
        if not html_content:
            return ''
        text = html_content
        text = re.sub(r'</p>|</div>|</h[1-6]>|<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<li[^>]*>', '• ', text, flags=re.IGNORECASE)
        text = re.sub(r'</li>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        text = html_lib.unescape(text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = '\n'.join(line.rstrip() for line in text.splitlines())
        return text.strip()

    @staticmethod
    def _clean_duration(value):
        if not value or value == '-':
            return '-'
        v = str(value).strip()
        suffix = ''
        if v.startswith('>'):
            suffix = '+'
            v = v[1:].strip()
        v = re.sub(r'semanas\b', 'weeks', v, flags=re.IGNORECASE)
        v = re.sub(r'semana\b',  'week',  v, flags=re.IGNORECASE)
        v = re.sub(r'dias\b',    'days',  v, flags=re.IGNORECASE)
        v = re.sub(r'dia\b',     'day',   v, flags=re.IGNORECASE)
        v = re.sub(r'horas\b',   'hours', v, flags=re.IGNORECASE)
        v = re.sub(r'hora\b',    'hour',  v, flags=re.IGNORECASE)
        v = re.sub(r'(\d)([a-zA-Z]{2,})', r'\1 \2', v)
        return v.strip() + suffix

    @staticmethod
    def _format_estimation_message(data):
        pts_manual    = escape(str(data.get('manual', '-')))
        pts_ia        = escape(str(data.get('con_ia', '-')))
        tiempo_manual = escape(ProjectTask._clean_duration(data.get('tiempo_manual', '-')))
        tiempo_ia     = escape(ProjectTask._clean_duration(data.get('tiempo_ia', '-')))
        razonamiento  = escape(str(data.get('razonamiento', '')))
        tipo          = escape(str(data.get('type', '')))
        from_kb       = data.get('from_kb', False)
        guia_manual   = data.get('guia_manual') or []

        kb_badge = Markup('')
        if from_kb:
            similarity = escape(str(data.get('similarity', '')))
            kb_badge = Markup(
                '<p><em>&#9889; Instant estimation from knowledge base '
                '(similarity: {}%)</em></p>'
            ).format(similarity)

        tipo_html = (
            Markup('<p><strong>Type:</strong> {}</p>').format(tipo) if tipo else Markup('')
        )

        pasos_html = Markup('')
        if guia_manual:
            items = Markup('').join(
                Markup('<li>{}</li>').format(escape(str(p))) for p in guia_manual
            )
            pasos_html = Markup(
                '<details><summary><strong>Manual Steps Guide</strong></summary>'
                '<ol>{}</ol></details>'
            ).format(items)

        return Markup("""
<div>
  <h4>&#128202; Task Estimation</h4>
  {kb_badge}
  <table border="0" cellpadding="4">
    <tr><td><strong>Manual:</strong></td><td>{pts_manual} pts &mdash; {tiempo_manual}</td></tr>
    <tr><td><strong>With AI:</strong></td><td>{pts_ia} pts &mdash; {tiempo_ia}</td></tr>
  </table>
  {tipo_html}
  <p><strong>Reasoning:</strong><br/>{razonamiento}</p>
  {pasos_html}
</div>
""").format(
            kb_badge=kb_badge,
            pts_manual=pts_manual,
            tiempo_manual=tiempo_manual,
            pts_ia=pts_ia,
            tiempo_ia=tiempo_ia,
            tipo_html=tipo_html,
            razonamiento=razonamiento,
            pasos_html=pasos_html,
        ).strip()
