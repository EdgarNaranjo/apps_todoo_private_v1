# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.addons import decimal_precision as dp
import httpagentparser
from odoo.http import request
import requests
import geocoder
from shapely.geometry.point import Point
import pyproj
from device_detector import DeviceDetector

UNIT = dp.get_precision("Location")


class HrAttendance(models.Model):
    _inherit = ['hr.attendance']

    latitude_check_in = fields.Char('Latitude', readonly=True)
    latitude_check_out = fields.Char('Latitude', readonly=True)
    longitude_check_in = fields.Char('Longitude', readonly=True)
    location_check_in = fields.Char('Location')
    longitude_check_out = fields.Char('Longitude', readonly=True)
    location_check_out = fields.Char('Location')
    location_ip_check_in = fields.Char('IP address')
    location_ip_check_out = fields.Char('IP address')
    city_check_in = fields.Char('City')
    city_check_out = fields.Char('City')
    type_disp_check_in = fields.Selection([
        ('mobile', 'Mobile'),
        ('pc', 'PC')], 'Device', track_visibility='always', default='pc')
    type_disp_check_out = fields.Selection([
        ('mobile', 'Mobile'),
        ('pc', 'PC')], 'Device', track_visibility='always', default='pc')
    user_os_check_in = fields.Char('Operative System')
    user_os_check_out = fields.Char('Operative System')
    browser_name_check_in = fields.Char('Browser')
    browser_name_check_out = fields.Char('Browser')
    the_point_check_in = fields.GeoPoint('Coordinate', compute='_compute_current_point', store=True)
    the_point_check_out = fields.GeoPoint('Coordinate', compute='_compute_current_point', store=True)
    show_checkout = fields.Boolean(string="Show Check Out", default=False, compute='show_check_out')
    code_country_out = fields.Many2one('res.country', 'Country')
    code_country_in = fields.Many2one('res.country', 'Country')
    device_type_in = fields.Char('Device Type')
    device_type_out = fields.Char('Device Type')

    def show_check_out(self):
        self.show_checkout = self.check_out is not False

    def _compute_current_point(self):
        proj = pyproj.Transformer.from_crs(4326, 3857)
        if self.env.context.get('check_in'):
            lat, lon = float(self.latitude_check_in), float(self.longitude_check_in)
            self.the_point_check_in = Point(proj.transform(lat, lon))
        if self.env.context.get('check_out'):
            lat, lon = float(self.latitude_check_out), float(self.longitude_check_out)
            self.the_point_check_out = Point(proj.transform(lat, lon))

    def get_country_id(self, code_country):
        if code_country:
            obj_country_id = self.env['res.country'].search([('code', '=', code_country)], limit=1)
            if obj_country_id:
                country = obj_country_id.id
            else:
                country = self.env.user.partner_id.country_id
            return country

    def get_geocoder_osm_location(self, attendance= False):
        ip = request.httprequest.environ['REMOTE_ADDR'] if request else 'n/a'
        city = ''
        code_country = False
        url = 'http://ipinfo.io/json/'
        url1 = 'http://icanhazip.com/'
        url2 = 'https://api.ipify.org/'

        context = requests.get(url, timeout=8)
        if context.status_code == 200:
            content = context.json()
            if content:
                ip = content['ip']
                city = content['city']
                code_country = content['country']
        elif context.status_code != 200:
            context1 = requests.get(url2, timeout=5)
            if context1.status_code == 200:
                ip = context1.text
            elif context1.status_code != 200:
                context2 = requests.get(url1, timeout=5)
                if context2.status_code == 200:
                    ip = context1.text

        conexion = geocoder.ipinfo(ip)
        _osm = geocoder.osm(conexion)
        agent = request.httprequest.environ.get('HTTP_USER_AGENT')
        device = DeviceDetector(agent).parse()

        if self.env.context.get('check_in'):
            if attendance:
                attendance.location_ip_check_in = conexion.ip
                attendance.city_check_in = _osm.city
                attendance.latitude_check_in = _osm.lat
                attendance.longitude_check_in = _osm.lng
                attendance.location_check_in = _osm.latlng
                attendance.with_context(check_in=True)._compute_current_point()
                attendance.user_os_check_in = device.os_name()
                attendance.device_type_in = device.device_type()
                attendance.browser_name_check_in = device.client_name()
                attendance.code_country_in = attendance.get_country_id(code_country)

        if self.env.context.get('check_out'):
            if attendance:
                attendance.location_ip_check_out = conexion.ip
                attendance.city_check_out = _osm.city
                attendance.latitude_check_out = _osm.lat
                attendance.longitude_check_out = _osm.lng
                attendance.location_check_out = _osm.latlng
                attendance.with_context(check_out=True)._compute_current_point()
                attendance.user_os_check_out = device.os_name()
                attendance.device_type_out = device.device_type()
                attendance.browser_name_check_out = device.client_name()
                attendance.code_country_out = attendance.get_country_id(code_country)

    @api.model
    def create(self, vals):
        request = super(HrAttendance, self).create(vals)
        if vals and 'check_in' in vals:
            obj_geo_id = self.with_context(check_in=True).get_geocoder_osm_location(request)
            employee = request.employee_id

            obj_geo_employee_id = {
                'check_in': request.check_in,
                'check_out': fields.Datetime.now(),
                'name': 'Morning Attendance ' + '[' + str(request.employee_id.name) + ']',
                'check_type': 'mning',
                'attendance_id': request.id,

            }
            # if len(obj_geo_id) > 0:
            #     # eliminar los que tengan valor False
            #     obj_geo_id = dict(filter(lambda x: x[1] != False, obj_geo_id.items()))
            employee_log = self.env['hr.employee.log'].create(obj_geo_employee_id)
            employee_log.location_ip_check_in = request.location_ip_check_in
            employee_log.city_check_in = request.city_check_in
            employee_log.latitude_check_in =request.latitude_check_in
            employee_log.longitude_check_in = request.longitude_check_in
            employee_log.location_check_in = request.location_check_in
            employee_log.the_point_check_in = request.the_point_check_in
            employee_log.user_os_check_in = request.user_os_check_in
            employee_log.browser_name_check_in = request.browser_name_check_in
            employee_log.the_point_check_in = request.the_point_check_in
            employee_log.code_country_in = request.code_country_in
            employee_log.device_type_in = request.device_type_in

        return request


    def write(self, vals):
        res = super(HrAttendance, self).write(vals)
        if vals and 'check_out' in vals:
            obj_geo_id = self.with_context(check_out=True).get_geocoder_osm_location(self)
            check_out = vals.get('check_out')
            # create hr.employee.log
            obj_geo_employee_id = {
                'check_in': fields.Datetime.now(),
                'check_out': check_out,
                'name': 'Afternoon Attendance ' + '[' + str(self.employee_id.name) + ']',
                'check_type': 'anoon',
                'attendance_id': self.id,
                's_check_out': True
            }
            employee_log = self.env['hr.employee.log'].create(obj_geo_employee_id)
            employee_log.location_ip_check_in = self.location_ip_check_out
            employee_log.city_check_in = self.city_check_out
            employee_log.latitude_check_in = self.latitude_check_out
            employee_log.longitude_check_in = self.longitude_check_out
            employee_log.location_check_in = self.location_check_out
            employee_log.the_point_check_in = self.the_point_check_out
            employee_log.user_os_check_in = self.user_os_check_out
            employee_log.browser_name_check_in = self.browser_name_check_out
            employee_log.the_point_check_in = self.the_point_check_out
            employee_log.code_country_in = self.code_country_out
            employee_log.device_type_in = self.device_type_out

        return res


class HrEmployeeLog(models.Model):
    _name = 'hr.employee.log'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Hr Employee Log'

    name = fields.Char('Name Document', track_visibility='onchange', required=True, index=True)
    attendance_id = fields.Many2one('hr.attendance', 'Attendance', track_visibility='onchange', index=True)
    employee_id = fields.Many2one('hr.employee', related='attendance_id.employee_id')
    check_in = fields.Datetime('Check in', help='Timestamp check in')
    check_out = fields.Datetime('Check out', help='Timestamp check out')
    hostname = fields.Char('Name host')
    type_disp = fields.Selection([
        ('mobile', 'Mobile'),
        ('pc', 'PC')], 'Device', track_visibility='always', default='pc')
    code_country = fields.Char('Code country')
    location = fields.Char('Location')
    postal_code = fields.Char('Zip code')
    state = fields.Selection([
        ('not_processed', 'Not processed'),
        ('processed', 'Processed')], 'State', track_visibility='always', default='not_processed')
    data_mapa = fields.Html('Map')
    check_type = fields.Selection([
        ('mning', 'Morning'),
        ('anoon', 'Afternoon')], 'Type attendace', track_visibility='always', default='mning')

    latitude_check_in = fields.Char('Latitude', readonly=True)
    longitude_check_in = fields.Char('Longitude', readonly=True)
    location_check_in = fields.Char('Location')
    location_ip_check_in = fields.Char('IP address')
    city_check_in = fields.Char('City')
    user_os_check_in = fields.Char('Operative System')
    browser_name_check_in = fields.Char('Browser')
    the_point_check_in = fields.GeoPoint('Coordinate')
    the_point_check_out = fields.GeoPoint('Coordinate')
    show_checkout = fields.Boolean(string="Show Check Out", default=False, compute='show_check_out')
    s_check_out = fields.Boolean(string="Check Out", default=False )
    code_country_in = fields.Many2one('res.country', 'Country')
    device_type_in = fields.Char('Device Type')

    def show_check_out(self):
        self.show_checkout = self.s_check_out is not False


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


    def action_conect_ml(self):
        obj_setting_id = self.env['attendance.setting'].search([('credentials', '=', True)])
        if obj_setting_id:
            for obj_setting in obj_setting_id:
                obj_setting.state_partner = 'CONNECTION ERROR'
                raise UserError(_('CONNECTION ERROR: Contact your service provider.'))
