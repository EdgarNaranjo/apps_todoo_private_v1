# -*- coding: utf-'8' "-*-"
from odoo.addons.payment import setup_provider, reset_payment_provider
from . import controllers
from . import models


def post_init_hook(env):
    setup_provider(env, 'flow')


def uninstall_hook(env):
    reset_payment_provider(env, 'flow')
