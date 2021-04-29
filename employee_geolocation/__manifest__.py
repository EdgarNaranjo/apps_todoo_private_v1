# -*- coding: utf-8 -*-
##############################################################################
#
#    This module allows to know the geolocation of the employees as well as
#    the electronic devices used once they make the attendance control.
#
#    Copyright (C) 2020- TODOOWEB.COM (https://www.todooweb.com)
#    @author ToDOO (https://www.linkedin.com/company/todooweb)
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': '[Attendance] Employee geolocation',
    'summary': 'Employee geolocation from attendance control',
    'description': """
        Employee geolocation from attendance control, every time I check in and out.
    """,
    'version': '10.0.0.0.1',
    'category': 'Human Resources',
    'license': 'LGPL-3',
    'author': "ToDOO (www.todooweb.com)",
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
        "Tatiana Rosabal <tatianarosabal@gmail.com>",
        'Antonio Ruban <antoniodavid8@gmail.com>',
    ],
    'support': 'devtodoo@gmail.com',
    'depends': [
        'base',
        'hr',
        'hr_attendance',
        'decimal_precision',
    ],
    'data': [
        'security/employee_geolocation_security.xml',
        'security/ir.model.access.csv',
        'views/hr_attendance_view.xml',
        'views/templates.xml',
    ],
    'images': [
        'static/description/screenshot_locatization.png'
    ],
    'live_test_url': 'https://www.youtube.com/watch?v=_ybQFK0AOpE',
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 39.99,
    'currency': 'EUR',
}
