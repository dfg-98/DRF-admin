def register(*models, site=None):
    """
    Register the given model(s) classes and wrapped ModelAdmin class with
    admin site:

    @register(Author)
    class AuthorAdmin(admin.ModelAdmin):
        pass

    The `site` kwarg is an admin site to use instead of the default admin site.
    """
    from rest_framework.serializers import ModelSerializer

    from .restmodeladmin import RestModelAdmin
    from .sites import AdminSite
    from .sites import site as default_site

    def _model_admin_wrapper(admin_class):
        if not models:
            raise ValueError("At least one model must be passed to register.")

        admin_site = site or default_site

        if not isinstance(admin_site, AdminSite):
            raise ValueError("site must subclass AdminSite")

        if not issubclass(admin_class, (RestModelAdmin, ModelSerializer)):
            raise ValueError(
                "Wrapped class must subclass RestModelAdmin or ModelSerializer."
            )

        admin_site.register(models, serializer_or_modeladmin=admin_class)

        return admin_class

    return _model_admin_wrapper
