# -*- coding: utf-8 -*-
##############################################################################
#
#    This module allows customers to pay for their orders with cards credit.
#    The transactions are processed by triPOS Cloud.
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
    'name': 'Vantiv triPOS Cloud Payment Services',
    'summary': """Vantiv triPOS Cloud Payment Services""",
    'description': """
        Allow credit card POS payments with triPOS Cloud. This module allows customers to pay for their orders with credit cards. The transactions are processed by triPOS Cloud.
    """,
    'version': '12.1.0.0.1',
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
        'web',
        'barcodes',
        'point_of_sale'
    ],
    'data': [
        'data/pos_vantiv_tripos_cloud_data.xml',
        'security/ir.model.access.csv',
        'views/pos_vantiv_tripos_cloud_views.xml',
        'views/pos_vantiv_tripos_lane_views.xml',
        'views/pos_vantiv_transactions_views.xml',
        'views/pos_config_views.xml',
        'views/menus.xml',
        'views/pos_vantiv_templates.xml',
    ],
    'qweb': [
        'static/src/xml/pos_vantiv_tripos_cloud.xml',
    ],
    'images': [
        'static/description/screenshot_vantiv.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 59.99,
    'currency': 'EUR',
}
