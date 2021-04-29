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

    'name': 'Vantiv Refund In POS',
    'summary': """Vantiv Refund In POS""",
    'description': """
       Allows the return of payments processed by Vantiv.
   """,
    'version': '12.1.0.0.1',
    'category': 'Point of Sale',
    'license': 'LGPL-3',
    'author': "ToDOO (www.todooweb.com)",
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
        "Tatiana Rosabal <tatianarosabal@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': ['point_of_sale', 'pos_vantiv_tripos_cloud'],
    'data': [
        'security/ir.model.access.csv',
        'views/return.xml',
        'views/pos_template.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'images': [
        'static/description/screenshot_vantiv_refund.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 49.99,
    'currency': 'EUR',
}
