# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from odoo import api, fields, models, _
from odoo.http import request

try:
    import geocoder
except ImportError:
    geocoder = None

try:
    import folium
    from folium import plugins
except ImportError:
    folium = None
    plugins = None

try:
    from device_detector import DeviceDetector
except ImportError:
    DeviceDetector = None

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    # Campos adicionales no cubiertos por el core v19
    # Core v19 ya incluye: in_latitude, in_longitude, in_location, in_ip_address
    # Core v19 ya incluye: out_latitude, out_longitude, out_location, out_ip_address
    city_check_in = fields.Char('City (In)')
    city_check_out = fields.Char('City (Out)')
    type_disp_check_in = fields.Selection([
        ('mobile', 'Mobile'), ('pc', 'PC')
    ], string='Device (In)', default='pc')
    type_disp_check_out = fields.Selection([
        ('mobile', 'Mobile'), ('pc', 'PC')
    ], string='Device (Out)', default='pc')
    user_os_check_in = fields.Char('OS (In)')
    user_os_check_out = fields.Char('OS (Out)')
    browser_name_check_in = fields.Char('Browser (In)')
    browser_name_check_out = fields.Char('Browser (Out)')
    device_type_in = fields.Char('Device Type (In)')
    device_type_out = fields.Char('Device Type (Out)')
    code_country_in = fields.Many2one('res.country', 'Country (In)')
    code_country_out = fields.Many2one('res.country', 'Country (Out)')
    show_checkout = fields.Boolean("Show Check Out", compute='_compute_show_checkout')

    def _compute_show_checkout(self):
        for rec in self:
            rec.show_checkout = bool(rec.check_out)

    @property
    def google_maps_url_in(self):
        if self.in_latitude and self.in_longitude:
            return f'https://maps.google.com?q={self.in_latitude},{self.in_longitude}'
        return False

    @property
    def google_maps_url_out(self):
        if self.out_latitude and self.out_longitude:
            return f'https://maps.google.com?q={self.out_latitude},{self.out_longitude}'
        return False

    def get_country_id(self, code_country):
        if code_country:
            country = self.env['res.country'].search([('code', '=', code_country)], limit=1)
            if country:
                return country.id
        return self.env.user.partner_id.country_id.id

    def get_geocoder_osm_location(self, attendance=False):
        if not geocoder:
            _logger.warning("geocoder not installed. Run: pip install geocoder")
            return
        try:
            ip = geocoder.ipinfo('me')
            conexion = ip.geojson['features'][-1]
            if not conexion.get('properties'):
                return
            props = conexion['properties']
            code_country = props.get('country')
            city = props.get('city')
            lat = ip.lat
            lng = ip.lng
            host = props.get('ip')
            agent = request.httprequest.environ.get('HTTP_USER_AGENT', '')
            device_os = device_type = browser_name = ''
            if DeviceDetector and agent:
                device = DeviceDetector(agent).parse()
                device_os = device.os_name()
                device_type = device.device_type()
                browser_name = device.client_name()
            if attendance:
                if attendance.check_in and not attendance.check_out:
                    attendance.write({
                        'in_ip_address': host,
                        'city_check_in': city,
                        'in_latitude': lat,
                        'in_longitude': lng,
                        'in_location': '%s,%s' % (lat, lng),
                        'user_os_check_in': device_os,
                        'device_type_in': device_type,
                        'browser_name_check_in': browser_name,
                        'code_country_in': self.get_country_id(code_country),
                    })
                elif attendance.check_out:
                    attendance.write({
                        'out_ip_address': host,
                        'city_check_out': city,
                        'out_latitude': lat,
                        'out_longitude': lng,
                        'out_location': '%s,%s' % (lat, lng),
                        'user_os_check_out': device_os,
                        'device_type_out': device_type,
                        'browser_name_check_out': browser_name,
                        'code_country_out': self.get_country_id(code_country),
                    })
        except Exception as e:
            _logger.warning("Error en geolocalización: %s" % str(e))

    @api.constrains('check_in', 'check_out')
    def get_check_in_values(self):
        env_log = self.env['hr.employee.log']
        for record in self:
            self.get_geocoder_osm_location(record)
            if record.check_in:
                if not record.check_out:
                    employee_log = env_log.create({
                        'check_in': record.check_in,
                        'check_out': fields.Datetime.now(),
                        'name': 'Morning Attendance [%s]' % record.employee_id.name,
                        'check_type': 'mning',
                        'attendance_id': record.id,
                        'location_ip_check_in': record.in_ip_address,
                        'city_check_in': record.city_check_in,
                        'latitude_check_in': str(record.in_latitude),
                        'longitude_check_in': str(record.in_longitude),
                        'location_check_in': record.in_location,
                        'user_os_check_in': record.user_os_check_in,
                        'browser_name_check_in': record.browser_name_check_in,
                        'code_country_in': record.code_country_in.id if record.code_country_in else False,
                        'device_type_in': record.device_type_in,
                    })
                    employee_log.create_map()
                    employee_log.message_post(body=_("Map created from Attendance: %s", record._get_html_link()))
                elif record.check_out:
                    employee_log = env_log.create({
                        'check_in': fields.Datetime.now(),
                        'check_out': record.check_out,
                        'name': 'Afternoon Attendance [%s]' % record.employee_id.name,
                        'check_type': 'anoon',
                        'attendance_id': record.id,
                        's_check_out': True,
                        'location_ip_check_in': record.out_ip_address,
                        'city_check_in': record.city_check_out,
                        'latitude_check_in': str(record.out_latitude),
                        'longitude_check_in': str(record.out_longitude),
                        'location_check_in': record.out_location,
                        'user_os_check_in': record.user_os_check_out,
                        'browser_name_check_in': record.browser_name_check_out,
                        'code_country_in': record.code_country_out.id if record.code_country_out else False,
                        'device_type_in': record.device_type_out,
                    })
                    employee_log.create_map()
                    employee_log.message_post(body=_("Map created from Attendance: %s", record._get_html_link()))


class HrEmployeeLog(models.Model):
    _name = 'hr.employee.log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Hr Employee Log'

    name = fields.Char('Name', tracking=True, required=True, index=True)
    attendance_id = fields.Many2one('hr.attendance', 'Attendance', tracking=True, index=True)
    employee_id = fields.Many2one(
        'hr.employee', related='attendance_id.employee_id', export_string_translation=False,
    )
    check_in = fields.Datetime('Check in')
    check_out = fields.Datetime('Check out')
    hostname = fields.Char('Name host')
    code_country = fields.Char('Code country')
    location = fields.Char('Location')
    postal_code = fields.Char('Zip code')
    state = fields.Selection([
        ('not_processed', 'Not processed'),
        ('processed', 'Processed'),
    ], string='State', tracking=True, default='not_processed')
    data_map = fields.Text('Map')
    check_type = fields.Selection([
        ('mning', 'Morning'),
        ('anoon', 'Afternoon'),
    ], string='Type attendance', tracking=True, default='mning')
    latitude_check_in = fields.Char('Latitude', readonly=True)
    longitude_check_in = fields.Char('Longitude', readonly=True)
    location_check_in = fields.Char('Location in')
    location_ip_check_in = fields.Char('IP address')
    city_check_in = fields.Char('City')
    user_os_check_in = fields.Char('Operative System')
    browser_name_check_in = fields.Char('Browser')
    show_checkout = fields.Boolean(compute='_compute_show_checkout')
    s_check_out = fields.Boolean(string="Check Out", default=False)
    code_country_in = fields.Many2one('res.country', 'Country')
    device_type_in = fields.Char('Device Type')

    def _compute_show_checkout(self):
        for rec in self:
            rec.show_checkout = rec.s_check_out

    def create_map(self):
        if self.state == 'not_processed' and folium and geocoder:
            try:
                location = geocoder.ip(self.location_ip_check_in).latlng
                if location:
                    m = folium.Map(location=location, zoom_start=11)
                    folium.CircleMarker(location=location, radius=55, color='red').add_to(m)
                    folium.Marker(location=location, popup='Working here!').add_to(m)
                    plugins.Geocoder().add_to(m)
                    self.write({'data_map': m._repr_html_(), 'state': 'processed'})
            except Exception as e:
                _logger.warning("Error creating map: %s" % str(e))

    def compare_create_map(self):
        if not (folium and geocoder):
            return
        location = geocoder.ip(self.location_ip_check_in).latlng
        obj_log = self.env['hr.employee.log'].search([
            ('id', '!=', self.id),
            ('employee_id', '=', self.employee_id.id),
            ('attendance_id', '=', self.attendance_id.id),
        ], limit=1)
        location_before = geocoder.ip(obj_log.location_ip_check_in).latlng if obj_log else False
        if location and location_before:
            m = folium.Map(location=location, zoom_start=8)
            folium.Marker(location=location, popup='Working here!').add_to(m)
            folium.Marker(
                location=location_before, popup='Previous attendance',
                icon=folium.Icon(color="red"),
            ).add_to(m)
            plugins.Geocoder().add_to(m)
            self.write({'data_map': m._repr_html_(), 'state': 'processed'})
            self.message_post(body=_("Map generated from the log: %s", obj_log._get_html_link()))
        else:
            self.message_post(body='Maps not generated')
            raise models.ValidationError(
                _('A minimum of two logs are required to compare two maps.')
            )

    def set_draft(self):
        self.state = 'not_processed'
