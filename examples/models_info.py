from oacensus.db import db
db.init(":memory:")

from oacensus.models import ModelBase
import inspect
import json
import oacensus.models

models = {}

for name, cls in inspect.getmembers(oacensus.models):
    if inspect.isclass(cls) and issubclass(cls, ModelBase) and not cls == ModelBase:
        models[name] = {}
        for field_name, field in cls._meta.fields.iteritems():
            models[name][field_name] = {
                    'field_attributes' : field.field_attributes(),
                    'verbose_name' : field.verbose_name,
                    'name' : field.name,
                    'null' : field.null,
                    'unique' : field.unique,
                    'index' : field.index,
                    'help' : field.help_text,
                    'default' : field.default
                    }

with open("models_info.json", 'wb') as f:
    json.dump(models, f, sort_keys=True, indent=4)
