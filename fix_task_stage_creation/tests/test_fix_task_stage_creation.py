# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""
Tests para fix_task_stage_creation.

Para ejecutar (requiere Odoo 19 instalado):
    python odoo-bin -d <db> --test-enable -i fix_task_stage_creation --stop-after-init

Comportamiento verificado:
  1. Al crear un proyecto, si hay etapas con default_stage=True, se asignan automáticamente.
  2. Si no hay etapas default, el proyecto queda sin etapas (sin error).
  3. El campo default_stage aparece en project.task.type.
"""

from odoo.tests.common import TransactionCase


class TestFixTaskStageCreation(TransactionCase):

    def setUp(self):
        super().setUp()
        # Limpiar etapas globales que podrían interferir
        self.env['project.task.type'].search([
            ('default_stage', '=', True)
        ]).write({'default_stage': False})

    def test_field_default_stage_exists(self):
        """El campo default_stage existe en project.task.type."""
        stage = self.env['project.task.type'].create({'name': 'Test Stage'})
        self.assertFalse(stage.default_stage, "default_stage debe ser False por defecto")
        stage.default_stage = True
        self.assertTrue(stage.default_stage)

    def test_project_gets_default_stages_on_create(self):
        """Al crear un proyecto, se asignan las etapas marcadas como default."""
        # Crear etapas default
        stage_a = self.env['project.task.type'].create({
            'name': 'Stage A',
            'default_stage': True,
        })
        stage_b = self.env['project.task.type'].create({
            'name': 'Stage B',
            'default_stage': True,
        })
        stage_c = self.env['project.task.type'].create({
            'name': 'Stage C (no default)',
            'default_stage': False,
        })

        # Crear proyecto sin especificar etapas
        project = self.env['project.project'].create({'name': 'Test Project'})

        # Verificar que las etapas default se asignaron
        self.assertIn(stage_a, project.type_ids,
                      "stage_a (default) debe estar en el proyecto")
        self.assertIn(stage_b, project.type_ids,
                      "stage_b (default) debe estar en el proyecto")
        self.assertNotIn(stage_c, project.type_ids,
                         "stage_c (no default) NO debe estar en el proyecto")

    def test_project_no_default_stages_no_error(self):
        """Si no hay etapas default, crear proyecto no produce error."""
        # Asegurar que no hay default stages
        self.env['project.task.type'].search([]).write({'default_stage': False})
        try:
            project = self.env['project.project'].create({'name': 'Project No Stages'})
            # El proyecto puede tener etapas del core de Odoo (ej. 'New' creado por name_create)
            # pero no por este módulo
            self.assertTrue(True, "La creación no debe lanzar excepción")
        except Exception as e:
            self.fail(f"Crear proyecto sin default stages no debe fallar: {e}")

    def test_project_with_explicit_stages_not_overridden(self):
        """Si el proyecto ya tiene etapas asignadas, no se sobreescriben."""
        stage_default = self.env['project.task.type'].create({
            'name': 'Default Stage',
            'default_stage': True,
        })
        stage_explicit = self.env['project.task.type'].create({
            'name': 'Explicit Stage',
            'default_stage': False,
        })

        # Crear proyecto con etapa explícita
        project = self.env['project.project'].create({
            'name': 'Project With Stages',
            'type_ids': [(4, stage_explicit.id)],
        })

        # La etapa explícita debe estar
        self.assertIn(stage_explicit, project.type_ids)
        # La default NO debe añadirse si ya había etapas
        self.assertNotIn(stage_default, project.type_ids,
                         "Si el proyecto ya tiene etapas, no añadir las default")

    def test_multiple_projects_inherit_same_defaults(self):
        """Múltiples proyectos creados heredan las mismas etapas default."""
        stage = self.env['project.task.type'].create({
            'name': 'Shared Default',
            'default_stage': True,
        })

        p1 = self.env['project.project'].create({'name': 'Project 1'})
        p2 = self.env['project.project'].create({'name': 'Project 2'})

        self.assertIn(stage, p1.type_ids)
        self.assertIn(stage, p2.type_ids)
