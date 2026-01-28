from django.contrib import admin
from django.conf import settings

class CustomAdminSite(admin.AdminSite):
    def get_app_list(self, request, app_label=None):
        app_dict = self._build_app_dict(request)
        
        app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())

        ordered_app_list = []
        app_order_labels = [app_config['app'] for app_config in getattr(settings, 'ADMIN_REORDER', [])]

        for app_label_to_find in app_order_labels:
            for i, app in enumerate(app_list):
                if app['app_label'] == app_label_to_find:
                    ordered_app_list.append(app_list.pop(i))
                    break
        
        ordered_app_list.extend(app_list)
        
        for app in ordered_app_list:
            app_config = next((item for item in getattr(settings, 'ADMIN_REORDER', []) if item.get('app') == app['app_label']), None)
            if app_config and 'models' in app_config:
                model_order = {model.split('.')[-1].lower(): i for i, model in enumerate(app_config['models'])}
                app['models'].sort(key=lambda x: model_order.get(x['object_name'].lower(), float('inf')))

        return ordered_app_list