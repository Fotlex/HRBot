from django.contrib import admin
from django.conf import settings
from django.urls import reverse
from django.utils.text import capfirst

class CustomAdminSite(admin.AdminSite):
    def get_app_list(self, request, app_label=None):
        app_dict = self._build_app_dict(request)
        
        app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())

        for app_config in getattr(settings, 'ADMIN_REORDER', []):
            app_label_to_find = app_config.get('app')
            for i, app in enumerate(app_list):
                if app['app_label'] == app_label_to_find:
                    app_list.insert(0, app_list.pop(i))
                    break
        
        for app in app_list:
            app['models'].sort(key=lambda x: x['name'])
            
            app_config = next((item for item in getattr(settings, 'ADMIN_REORDER', []) if item.get('app') == app['app_label']), None)
            if app_config and 'models' in app_config:
                model_order = [model.split('.')[-1].lower() for model in app_config['models']]
                app['models'].sort(key=lambda x: model_order.index(x['object_name'].lower()) if x['object_name'].lower() in model_order else float('inf'))


        return app_list

site = CustomAdminSite()