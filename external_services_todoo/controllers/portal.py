# -*- coding: utf-8 -*-
# Part of Todooweb. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers import portal

import binascii


class CustomerPortal(portal.CustomerPortal):

    @http.route(['/my/tasks/<int:task_id>/worksheet/sign/<string:source>'], type='json', auth="public", website=True)
    def portal_worksheet_sign(self, task_id, access_token=None, source=False, name=None, signature=None):
        # get from query string if not on json param
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            task_sudo = self._document_check_access('project.task', task_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid Task.')}
        if not signature:
            return {'error': _('Signature is missing.')}
        try:
            task_sudo.write({
                'worksheet_signature': signature,
                'worksheet_signed_by': name
            })
        except (TypeError, binascii.Error):
            return {'error': _('Invalid signature data.')}
        task_sudo.message_post(body=_('The worksheet has been signed.'))
        materials = request.env['ot.material.line'].search([('task_id', '=', task_sudo.id)])
        if materials:
            materials.write({'check_process': True})
        operations = request.env['operation.line'].search([('task_id', '=', task_sudo.id)])
        if operations:
            operations.write({'check_process': True})
        return {
            'force_refresh': True,
            'redirect_url': task_sudo.get_portal_url(query_string=f'&source={source}'),
        }
