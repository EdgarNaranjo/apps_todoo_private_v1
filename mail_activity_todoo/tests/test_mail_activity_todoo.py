# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""
Tests para mail_activity_todoo.

Para ejecutar:
    python odoo-bin -d <db> --test-enable -i mail_activity_todoo --stop-after-init
"""

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestMailActivityTodoo(TransactionCase):

    def setUp(self):
        super().setUp()
        self.user_a = self.env['res.users'].create({
            'name': 'User A',
            'login': 'user_a_test@test.com',
            'group_ids': [(4, self.env.ref('base.group_user').id)],
        })
        self.user_b = self.env['res.users'].create({
            'name': 'User B',
            'login': 'user_b_test@test.com',
            'group_ids': [(4, self.env.ref('base.group_user').id)],
        })
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.activity_type = self.env['mail.activity.type'].search([], limit=1)

    def _create_activity(self, assigned_user=None, creator=None):
        """Helper para crear una actividad como admin con usuario asignado."""
        assigned_user = assigned_user or self.env.user
        return self.env['mail.activity'].sudo().create({
            'res_model_id': self.env['ir.model']._get('res.partner').id,
            'res_id': self.partner.id,
            'activity_type_id': self.activity_type.id,
            'user_id': assigned_user.id,
            'summary': 'Test activity',
        })

    def test_mail_channel_id_field_exists(self):
        """El campo mail_channel_id existe en mail.activity."""
        activity = self._create_activity(assigned_user=self.user_a)
        self.assertTrue(
            hasattr(activity, 'mail_channel_id'),
            "mail_channel_id debe existir en mail.activity"
        )

    def test_mail_channel_id_points_to_discuss_channel(self):
        """mail_channel_id apunta al modelo discuss.channel."""
        activity = self._create_activity()
        field = activity._fields.get('mail_channel_id')
        self.assertIsNotNone(field, "Campo mail_channel_id debe existir")
        self.assertEqual(
            field.comodel_name, 'discuss.channel',
            "mail_channel_id debe apuntar a discuss.channel"
        )

    def test_not_show_channel_field_exists(self):
        """El campo not_show_channel existe en mail.activity."""
        activity = self._create_activity()
        self.assertFalse(activity.not_show_channel, "not_show_channel default debe ser False")

    def test_owner_can_write_activity(self):
        """El propietario (user_id) puede editar su propia actividad."""
        activity = self._create_activity(assigned_user=self.user_a)
        try:
            activity.with_user(self.user_a).write({'summary': 'Updated by owner'})
        except ValidationError:
            self.fail("El propietario (user_id) debe poder editar su propia actividad")

    def test_other_user_cannot_write_activity(self):
        """Un usuario diferente no puede editar actividades ajenas."""
        activity = self._create_activity(assigned_user=self.user_a)
        with self.assertRaises(ValidationError):
            activity.with_user(self.user_b).write({'summary': 'Unauthorized edit'})

    def test_other_user_cannot_unlink_activity(self):
        """Un usuario diferente no puede eliminar actividades ajenas."""
        activity = self._create_activity(assigned_user=self.user_a)
        with self.assertRaises(ValidationError):
            activity.with_user(self.user_b).unlink()

    def test_owner_can_unlink_activity(self):
        """El propietario (user_id) puede eliminar su propia actividad."""
        activity = self._create_activity(assigned_user=self.user_a)
        try:
            activity.with_user(self.user_a).unlink()
        except ValidationError:
            self.fail("El propietario debe poder eliminar su propia actividad")
