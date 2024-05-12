# -*- coding: utf-'8' "-*-"
from odoo.addons.payment import setup_provider, reset_payment_provider
from . import controllers
from . import models


def post_init_hook(cr, registry):
    setup_provider(cr, registry, 'flow')


def uninstall_hook(cr, registry):
    reset_payment_provider(cr, registry, 'flow')
