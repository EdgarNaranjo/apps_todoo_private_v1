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
    'version': '17.0.0.2',
    'category': 'Payment',
    'license': 'LGPL-3',
    'author': "ToDOO (www.todooweb.com)",
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
        "Antonio Ruban <antoniodavid8@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': ['web', 'barcodes', 'point_of_sale', 'pos_mercury'],
    'data': [
        'data/pos_vantiv_tripos_cloud_data.xml',
        'security/ir.model.access.csv',
        'views/pos_vantiv_tripos_cloud_views.xml',
        'views/pos_vantiv_tripos_lane_views.xml',
        'views/pos_vantiv_transactions_views.xml',
        'views/pos_config_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_vantiv_tripos_cloud/static/src/js/app/**/*',
            'pos_vantiv_tripos_cloud/static/src/js/override/**/*',
        ],
    },
    'images': [
        'static/description/screenshot_vantiv.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 229.99,
    'currency': 'EUR',
}
