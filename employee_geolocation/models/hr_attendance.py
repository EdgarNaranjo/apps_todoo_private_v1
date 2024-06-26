# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.http import request
import geocoder
import folium
from folium import plugins
from device_detector import DeviceDetector
from odoo.exceptions import UserError


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    latitude_check_in = fields.Char('Latitude', readonly=True)
    latitude_check_out = fields.Char('Latitude', readonly=True)
    longitude_check_in = fields.Char('Longitude', readonly=True)
    location_check_in = fields.Char('Location in')
    longitude_check_out = fields.Char('Longitude', readonly=True)
    location_check_out = fields.Char('Location out')
    location_ip_check_in = fields.Char('IP address')
    location_ip_check_out = fields.Char('IP address')
    city_check_in = fields.Char('City')
    city_check_out = fields.Char('City')
    type_disp_check_in = fields.Selection([
        ('mobile', 'Mobile'),
        ('pc', 'PC')], 'Device', default='pc')
    type_disp_check_out = fields.Selection([
        ('mobile', 'Mobile'),
        ('pc', 'PC')], 'Device', default='pc')
    user_os_check_in = fields.Char('Operative System')
    user_os_check_out = fields.Char('Operative System')
    browser_name_check_in = fields.Char('Browser')
    browser_name_check_out = fields.Char('Browser')
    show_checkout = fields.Boolean("Show Check Out", default=False, compute='show_check_out')
    code_country_out = fields.Many2one('res.country', 'Country')
    code_country_in = fields.Many2one('res.country', 'Country')
    device_type_in = fields.Char('Device Type')
    device_type_out = fields.Char('Device Type')

    def show_check_out(self):
        self.show_checkout = self.check_out is not False

    def get_country_id(self, code_country):
        if code_country:
            obj_country_id = self.env['res.country'].search([('code', '=', code_country)], limit=1)
            if obj_country_id:
                return obj_country_id.id
        return self.env.user.partner_id.country_id

    def get_geocoder_osm_location(self, attendance=False):
        ip = geocoder.ipinfo('me')
        conexion = ip.geojson['features'][-1]
        if not conexion['properties']:
            return
        code_country = conexion['properties']['country']
        city = conexion['properties']['city']
        lat = ip.lat
        lng = ip.lng
        location = ip.latlng
        host = conexion['properties']['ip']
        agent = request.httprequest.environ.get('HTTP_USER_AGENT')
        device = DeviceDetector(agent).parse()
        device_os = device.os_name()
        device_type = device.device_type()
        browser_name = device.client_name()
        if attendance:
            if attendance.check_in and not attendance.check_out:
                attendance.location_ip_check_in = host
                attendance.city_check_in = city
                attendance.latitude_check_in = lat
                attendance.longitude_check_in = lng
                attendance.location_check_in = location
                attendance.user_os_check_in = device_os
                attendance.device_type_in = device_type
                attendance.browser_name_check_in = browser_name
                attendance.code_country_in = attendance.get_country_id(code_country)
            if attendance.check_out:
                attendance.location_ip_check_out = host
                attendance.city_check_out = city
                attendance.latitude_check_out = lat
                attendance.longitude_check_out = lng
                attendance.location_check_out = location
                attendance.user_os_check_out = device_os
                attendance.device_type_out = device_type
                attendance.browser_name_check_out = browser_name
                attendance.code_country_out = attendance.get_country_id(code_country)

    @api.constrains('check_in', 'check_out')
    def get_check_in_values(self):
        env_log = self.env['hr.employee.log']
        for record in self:
            self.get_geocoder_osm_location(record)
            if record.check_in:
                if not record.check_out:
                    obj_geo_employee_id = {
                        'check_in': record.check_in,
                        'check_out': fields.Datetime.now(),
                        'name': 'Morning Attendance ' + '[' + str(record.employee_id.name) + ']',
                        'check_type': 'mning',
                        'attendance_id': record.id,
                    }
                    employee_log = env_log.create(obj_geo_employee_id)
                    employee_log.location_ip_check_in = record.location_ip_check_in
                    employee_log.city_check_in = record.city_check_in
                    employee_log.latitude_check_in = record.latitude_check_in
                    employee_log.longitude_check_in = record.longitude_check_in
                    employee_log.location_check_in = record.location_check_in
                    employee_log.user_os_check_in = record.user_os_check_in
                    employee_log.browser_name_check_in = record.browser_name_check_in
                    employee_log.code_country_in = record.code_country_in
                    employee_log.device_type_in = record.device_type_in
                    employee_log.create_map()
                    employee_log.message_post()
                    message = _("Map created from Attendance: {}".format(record._get_html_link()))
                    employee_log.message_post(body=message)

                if record.check_out:
                    obj_geo_employee_id = {
                        'check_in': fields.Datetime.now(),
                        'check_out': record.check_out,
                        'name': 'Afternoon Attendance ' + '[' + str(record.employee_id.name) + ']',
                        'check_type': 'anoon',
                        'attendance_id': record.id,
                        's_check_out': True
                    }
                    employee_log = env_log.create(obj_geo_employee_id)
                    employee_log.location_ip_check_in = record.location_ip_check_out
                    employee_log.city_check_in = record.city_check_out
                    employee_log.latitude_check_in = record.latitude_check_out
                    employee_log.longitude_check_in = record.longitude_check_out
                    employee_log.location_check_in = record.location_check_out
                    employee_log.user_os_check_in = record.user_os_check_out
                    employee_log.browser_name_check_in = record.browser_name_check_out
                    employee_log.code_country_in = record.code_country_out
                    employee_log.device_type_in = record.device_type_out
                    employee_log.create_map()
                    message = _("Map created from Attendance: {}".format(record._get_html_link()))
                    employee_log.message_post(body=message)


class HrEmployeeLog(models.Model):
    _name = 'hr.employee.log'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Hr Employee Log'

    name = fields.Char('Name Document', tracking=1, required=True, index=True)
    attendance_id = fields.Many2one('hr.attendance', 'Attendance', tracking=1, index=True)
    employee_id = fields.Many2one('hr.employee', related='attendance_id.employee_id')
    check_in = fields.Datetime('Check in', help='Timestamp check in')
    check_out = fields.Datetime('Check out', help='Timestamp check out')
    hostname = fields.Char('Name host')
    type_disp = fields.Selection([
        ('mobile', 'Mobile'),
        ('pc', 'PC')], 'Device', tracking=1, default='pc')
    code_country = fields.Char('Code country')
    location = fields.Char('Location')
    postal_code = fields.Char('Zip code')
    state = fields.Selection([
        ('not_processed', 'Not processed'),
        ('processed', 'Processed')], 'State', tracking=1, default='not_processed')
    data_map = fields.Text('Map')
    check_type = fields.Selection([
        ('mning', 'Morning'),
        ('anoon', 'Afternoon')], 'Type attendace', tracking=1, default='mning')
    latitude_check_in = fields.Char('Latitude', readonly=True)
    longitude_check_in = fields.Char('Longitude', readonly=True)
    location_check_in = fields.Char('Location in')
    location_ip_check_in = fields.Char('IP address')
    city_check_in = fields.Char('City')
    user_os_check_in = fields.Char('Operative System')
    browser_name_check_in = fields.Char('Browser')
    show_checkout = fields.Boolean(string="Show Check Out", default=False, compute='show_check_out')
    s_check_out = fields.Boolean(string="Check Out", default=False)
    code_country_in = fields.Many2one('res.country', 'Country')
    device_type_in = fields.Char('Device Type')

    def show_check_out(self):
        self.show_checkout = self.s_check_out is not False

    def create_map(self):
        if self.state == 'not_processed':
            location = geocoder.ip(self.location_ip_check_in).latlng
            if location:
                map = folium.Map(location=location, zoom_start=11)
                folium.CircleMarker(location=location, radius=55, color='red').add_to(map)
                folium.Marker(location=location, popup='Hello, working here!').add_to(map)
                plugins.Geocoder().add_to(map)
                map_html = map._repr_html_()
                self.write({'data_map': map_html})
                self.state = 'processed'

    def compare_create_map(self):
        location = geocoder.ip(self.location_ip_check_in).latlng
        location_before = False
        obj_log = self.env['hr.employee.log'].search([('id', '!=', self.id), ('employee_id', '=', self.employee_id.id), ('attendance_id', '=', self.attendance_id.id)], limit=1)
        if obj_log:
            location_before = geocoder.ip(obj_log.location_ip_check_in).latlng
        if location and location_before:
            map = folium.Map(location=location, zoom_start=8)
            folium.Marker(location=location, popup='Hello, working here!').add_to(map)
            folium.Marker(location=location_before, popup='Previous attendance', icon=folium.Icon(color="red")).add_to(map)
            plugins.Geocoder().add_to(map)
            map_html = map._repr_html_()
            self.write({'data_map': map_html})
            self.state = 'processed'
            message = _("Map generated from the log: {}".format(obj_log._get_html_link()))
            self.message_post(body=message)
        else:
            self.message_post(body='Maps not generated')
            self.env.cr.commit()
            raise UserError(_('A minimum of two logs are required to compare two maps.\n Contact an Administrator.'))

    def set_draft(self):
        self.state = 'not_processed'
