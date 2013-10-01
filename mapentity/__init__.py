import re
import inspect
from collections import namedtuple, OrderedDict

from django.conf import settings
from django.utils.importlib import import_module
from django.views.generic.base import View
from django.conf.urls import patterns

__all__ = ['app_settings', 'registry']


app_settings = dict({
    'TITLE': "",
    'HISTORY_ITEMS_MAX': 5,
    'CONVERSION_SERVER': '',
    'CAPTURE_SERVER': '',
    'INTERNAL_USER': '__internal__',
    'JS_SETTINGS_VIEW': 'mapentity:js_settings',
    'ROOT_URL': '',
    'LANGUAGES': settings.LANGUAGES,
    'LANGUAGE_CODE': settings.LANGUAGE_CODE,
    'TEMP_DIR': getattr(settings, 'TEMP_DIR', '/tmp'),
    'MAP_CAPTURE_SIZE': 800,
    'GEOM_FIELD_NAME': 'geom',
}, **getattr(settings, 'MAPENTITY_CONFIG', {}))


_MAP_STYLES = {
    'detail': {'weight': 5, 'opacity': 1, 'color': 'yellow', 'arrowColor': '#FF5E00', 'arrowSize': 8},
    'others': {'opacity': 0.9, 'fillOpacity': 0.7, 'color': 'yellow'},
    'filelayer': {'color': 'red', 'opacity': 1.0, 'fillOpacity': 1.0, 'weight': 2, 'radius': 8},
    'draw': {'color': '#35FF00', 'opacity': 0.8, 'weight': 3},
}


_LEAFLET_PLUGINS = OrderedDict([
    ('leaflet.overintent', {
        'js': 'mapentity/leaflet.overintent.js',
    }),
    ('leaflet.draw', {
        'css': 'mapentity/Leaflet.draw/leaflet.draw.css',
        'js': 'mapentity/Leaflet.draw/leaflet.draw.js',
    }),
    ('leaflet.label', {
        'css': 'mapentity/Leaflet.label/leaflet.label.css',
        'js': 'mapentity/Leaflet.label/leaflet.label.js'
    }),
    ('leaflet.spin', {
        'js': ['mapentity/spin.js',
               'mapentity/leaflet.spin.js']
    }),
    ('leaflet.layerindex', {
        'js': ['mapentity/rtree.js',
               'mapentity/leaflet.layerindex.js']
    }),
    ('leaflet.filelayer', {
        'js': ['mapentity/togeojson.js',
               'mapentity/leaflet.filelayer.js']
    }),
    ('leaflet.textpath', {
        'js': 'mapentity/leaflet.textpath.js'
    }),
    ('leaflet.geometryutil', {
        'js': 'mapentity/leaflet.geometryutil.js'
    }),
    ('leaflet.snap', {
        'js': 'mapentity/leaflet.snap.js'
    }),
    ('leaflet.measurecontrol', {
        'css': 'mapentity/leaflet.measurecontrol.css',
        'js': 'mapentity/leaflet.measurecontrol.js'
    }),
    ('mapentity.forms', {
        'js': 'mapentity/mapentity.forms.js'
    })
])

_LEAFLET_CONFIG = getattr(settings, 'LEAFLET_CONFIG', {})
_LEAFLET_PLUGINS.update(_LEAFLET_CONFIG.get('PLUGINS', {}))  # mapentity plugins first
_LEAFLET_CONFIG['PLUGINS'] = _LEAFLET_PLUGINS
setattr(settings, 'LEAFLET_CONFIG', _LEAFLET_CONFIG)


MapEntity = namedtuple('MapEntity', ['menu', 'label', 'icon', 'icon_small', 'icon_big','modelname', 'url_list'])


class Registry(object):
    def __init__(self):
        self.registry = OrderedDict()
        self.apps = {}

    def register(self, model, name='', menu=True):
        """ Register model and returns URL patterns
        """
        from .urlizor import view_classes_to_url

        # Ignore models from not installed apps
        if not model._meta.installed:
            return ()
        # Register once only
        if model in self.registry:
            return ()
        # Obtain app's views module from Model
        views_module_name = re.sub('models.*', 'views', model.__module__)
        views_module = import_module(views_module_name)
        # Filter to views inherited from MapEntity base views
        picked = []
        for name, view in inspect.getmembers(views_module):
            if inspect.isclass(view) and issubclass(view, View):
                if hasattr(view, 'get_entity_kind'):
                    try:
                        view_model = view.model or view.queryset.model
                    except AttributeError:
                        pass
                    else:
                        if view_model is model:
                            picked.append(view)

        module_name = model._meta.module_name
        app_label = model._meta.app_label

        mapentity = MapEntity(label=model._meta.verbose_name_plural,
                              modelname=module_name,
                              icon='images/%s.png' % module_name,
                              icon_small='images/%s-16.png' % module_name,
                              icon_big='images/%s-96.png' % module_name,
                              menu=menu,
                              url_list='%s:%s_%s' % (app_label, module_name, 'list'))

        self.registry[model] = mapentity
        # Returns Django URL patterns
        return patterns(name, *view_classes_to_url(*picked))

    @property
    def entities(self):
        return self.registry.values()


registry = Registry()
