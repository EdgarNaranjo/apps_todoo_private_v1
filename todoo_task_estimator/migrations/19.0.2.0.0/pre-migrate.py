"""
Migration 19.0.2.0.0 — pre-migrate
Drop todoo_estimator_session table if it exists (model removed in v2).
"""


def migrate(cr, version):
    cr.execute("DROP TABLE IF EXISTS todoo_estimator_session CASCADE")
    cr.execute(
        "DELETE FROM ir_model WHERE model = 'todoo.estimator.session'"
    )
    cr.execute(
        "DELETE FROM ir_model_fields WHERE model = 'todoo.estimator.session'"
    )
