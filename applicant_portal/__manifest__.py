# -*- coding: utf-8 -*-
##############################################################################
#
#    This module allows your candidate(s) and applicant(s) to apply from the portal and check
#    the status of applications on my account portal of your website.
#    Improve the job recruiting form, adding other fields to the form.
#    It will process the data entered and return a message indicating whether
#    the company is eligible or not.
#
#    Copyright (C) 2020- todooweb.com (https://www.todooweb.com)
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
    'name': "Online Job Application",
    'summary': """Online Job Applicants Portal""",
    'description': """
        Online Job applicants portal. The candidate(s) and applicant(s) can to apply from the portal and check the status of applications on my account portal of your website.
    """,
    'version': '13.0.0.0.1',
    'category': 'Website',
    'license': 'LGPL-3',
    'author': "ToDOO (www.todooweb.com)",
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
        "Tatiana Rosabal <tatianarosabal@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': [
        'http_routing',
        'mail',
        'portal',
        'base',
        'crm',
        'sale',
        'auth_signup',
        'website',
        'website_hr_recruitment',
        'website_crm_partner_assign',
    ],
    'data': [
        'security/applicant_security.xml',
        'security/ir.model.access.csv',
        'views/applicant_portal_view.xml',
    ],
    'images': [
        'static/description/screenshot_applicant_index.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 29.99,
    'currency': 'EUR',
}
