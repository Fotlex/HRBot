from django.contrib.admin.apps import AdminConfig

class CoreAdminConfig(AdminConfig):
    default_site = 'web.core.admin.CustomAdminSite'