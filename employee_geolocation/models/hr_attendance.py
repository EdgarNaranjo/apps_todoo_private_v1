# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.addons import decimal_precision as dp
import requests
import httpagentparser
from odoo.http import request

UNIT = dp.get_precision("Location")


class HrAttendance(models.Model):
    _inherit = ['hr.attendance']

    latitude = fields.Float("Check-in Latitude", digits=UNIT, readonly=True)
    longitude = fields.Float("Check-in Longitude", digits=UNIT, readonly=True)
    location_ip = fields.Char('IP address')
    city = fields.Char('City')
    type_disp = fields.Selection([
        ('mobile', 'Mobile'),
        ('pc', 'PC')], 'Device', track_visibility='always', default='pc')
    user_os = fields.Char('Operative System')
    browser_name = fields.Char('Browser')

    @api.model
    def create(self, vals):
        request = super(HrAttendance, self).create(vals)
        # location
        location = self.env.context.get('attendance_location', False)
        if location:
            employee = request.employee_id
            employee_id = employee.id
            obj_geo_id = self.update_geolocation(employee_id, location)
            if obj_geo_id:
                # create hr.employee.log
                obj_geo_id.update({
                    'check_in': request.check_in,
                    'name': 'Morning Attendance ' + '[' + str(request.employee_id.name) + ']'
                })
                self.env['hr.employee.log'].create(obj_geo_id)
                request.location_ip = obj_geo_id['location_ip']
                request.city = obj_geo_id['city']
                request.type_disp = obj_geo_id['type_disp']
                request.user_os = obj_geo_id['user_os']
                request.browser_name = obj_geo_id['browser_name']
        return request

    @api.multi
    def write(self, vals):
        # location
        location = self.env.context.get('attendance_location', False)
        if location:
            employee_id = self.employee_id.id
            # geolocation
            obj_geo_id = self.update_geolocation(employee_id, location)
            if obj_geo_id:
                if vals and 'check_out' in vals:
                    check_out = vals.get('check_out')
                    # create hr.employee.log
                    obj_geo_id.update({
                        'check_out': check_out,
                        'name': 'Afternoon Attendance ' + '[' + str(self.employee_id.name) + ']'
                    })
                    self.env['hr.employee.log'].create(obj_geo_id)
                    self.location_ip = obj_geo_id['location_ip']
                    self.city = obj_geo_id['city']
                    self.type_disp = obj_geo_id['type_disp']
                    self.user_os = obj_geo_id['user_os']
                    self.browser_name = obj_geo_id['browser_name']
        res = super(HrAttendance, self).write(vals)
        return res

    @api.multi
    def update_geolocation(self, employee_id, location):
        dict_add = {
            'location_ip': '',
            'city': '',
            'code_country': '',
            'postal_code': '',
            'type_disp': '',
            'employee_id': employee_id,
            'check_in': '',
            'check_out': '',
            'country_id': '',
            'user_os': '',
            'browser_name': '',
            'location': '',
        }

        # data odoo
        agent = request.httprequest.environ.get('HTTP_USER_AGENT')
        agent_details = httpagentparser.detect(agent)
        user_os = agent_details['os']['name']
        dict_add['user_os'] = user_os
        browser_name = agent_details['browser']['name']
        dict_add['browser_name'] = browser_name
        # data url
        url = 'https://ipinfo.io/json'
        context = requests.get(url)
        if context.status_code == 200:
            content = context.json()
            if content:
                location_ip = content['ip']
                dict_add['location_ip'] = location_ip
                hostname = content['hostname']
                if content['timezone']:
                    city = str(content['timezone'].split('/')[1])
                dict_add['city'] = city
                code_country = content['country']
                dict_add['code_country'] = code_country
                postal_code = content['postal']
                dict_add['postal_code'] = postal_code
                dict_add['type_disp'] = self.get_type_device(hostname, code_country)
                dict_add['country_id'] = self.get_country_id(code_country)
                # search location
                if location:
                    dict_add['location'] = location[0], location[1]
                    ','.join(map(str, dict_add['location']))
        return dict_add

    @api.multi
    def get_type_device(self, hostname, code_country):
        type_device = 'mobile'
        list_country = ['RU']
        if hostname:
            host_split = hostname.split('.')
            host = host_split[1]
            if (len(host) > 4) or (len(host) >= 3 and code_country in list_country):
                val_type = 'pc'
            else:
                val_type = 'mobile'
            type_device = val_type
        return type_device

    @api.multi
    def get_country_id(self, code_country):
        if code_country:
            obj_country_id = self.env['res.country'].search([('code', '=', code_country)], limit=1)
            if obj_country_id:
                country = obj_country_id.id
        else:
            country = self.env.user.partner_id.country_id
        return country


class HrEmployeeLog(models.Model):
    _name = 'hr.employee.log'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Hr Employee Log'

    name = fields.Char('Name Document', track_visibility='onchange', required=True, index=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', track_visibility='onchange', index=True)
    attendance_id = fields.Many2one('hr.attendance', 'Attendance', track_visibility='onchange', index=True)
    country_id = fields.Many2one('res.country', 'Country', track_visibility='onchange', index=True)
    check_in = fields.Datetime('Check in', help='Timestamp check in')
    check_out = fields.Datetime('Check out', help='Timestamp check out')
    location_ip = fields.Char('IP address')
    hostname = fields.Char('Name host')
    city = fields.Char('City')
    type_disp = fields.Selection([
        ('mobile', 'Mobile'),
        ('pc', 'PC')], 'Device', track_visibility='always', default='pc')
    code_country = fields.Char('Code country')
    location = fields.Char('Location')
    postal_code = fields.Char('Zip code')
    user_os = fields.Char('Operative System')
    browser_name = fields.Char('Browser')
    state = fields.Selection([
        ('not_processed', 'Not processed'),
        ('processed', 'Processed')], 'State', track_visibility='always', default='not_processed')
    data_mapa = fields.Html('Map')

    @api.multi
    def open_map(self):
        for log in self:
            url = "http://maps.google.com/maps?oi=map&q="
            if log.location:
                url += log.location.replace(' ', '')
            else:
                raise UserError(_('URL NOT FOUND: Employee has not location.'))
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': url
        }


class HrEmployeeLocation(models.Model):
    _name = 'hr.employee.location'
    _description = 'Hr Employee Location'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', 'Employee', track_visibility='onchange', index=True)
    location_home = fields.Char('Location Home')
    location_work = fields.Char('Location Work')
    location_home_new = fields.Char('Location Home New')
    location_work_new = fields.Char('Location Work New')


class AttendanceSetting(models.Model):
    _name = 'attendance.setting'
    _description = 'Settings'
    _rec_name = 'api_key'

    api_key = fields.Char('APIKEY', index=True, required=True)
    secret = fields.Char('SECRET', required=True)
    url = fields.Char('URL', required=True)
    state = fields.Selection([
        ('no_connect', 'Not connected'),
        ('connect', 'Connected')
    ], string='Status server', index=True, default='no_connect')
    state_partner = fields.Char('Status partner', default='NOT CONNECTED')
    credentials = fields.Boolean('Credentials',
                                 help='Indicates that the configuration is your own and only for use with ML')

    @api.multi
    def action_conect_ml(self):
        obj_setting_id = self.env['attendance.setting'].search([('credentials', '=', True)])
        if obj_setting_id:
            for obj_setting in obj_setting_id:
                obj_setting.state_partner = 'CONNECTION ERROR'
                raise UserError(_('CONNECTION ERROR: Contact your service provider.'))
