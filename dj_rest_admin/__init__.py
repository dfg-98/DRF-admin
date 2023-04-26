from django.utils.module_loading import autodiscover_modules

from .decorators import register
from .restmodeladmin import RestModelAdmin
from .sites import AdminSite as RestAdminSite
from .sites import site

__all__ = ["site", "register", "RestAdminSite", "RestModelAdmin", "autodiscover"]


def autodiscover():
    autodiscover_modules("rest_admin", register_to=site)
