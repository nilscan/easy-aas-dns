from datetime import datetime
import os
import inspect
from zoneinfo import ZoneInfo
import yaml, json

import kubernetes

class TerraformResourceException(Exception):
    pass


# get current datetime
def current_timestamp():
    d = datetime.now(ZoneInfo('UTC'))
    # Get current ISO 8601 datetime in string format
    return d.strftime('%Y-%m-%dT%H:%M:%SZ')

def get_condition(conditions, type: str):
    for cond in conditions:
        if cond.get('type', '') == type:
            return cond
    return None

def update_condition(conditions, condition):
    def map_condition(cond):
        # Check the existing conditions, update the current one if it exists
        if cond.get('type', '') == condition['type']:
            if cond != condition:
                # If the condition has changed, update the transition time
                condition['lastTransitionTime'] = current_timestamp()
            return condition
        else:
            return cond

    conditions = list(map(map_condition, conditions))        
    if get_condition(conditions, condition['type']) is None:
        # Condition didn't exist before, add it
        condition['lastTransitionTime'] = current_timestamp()
        conditions.append(condition)

    return conditions

def add_annotations(objs, annotations, nested=None, forced=False):
    """
    Add metatada annotations to an object and optionally to nested parts of the object
    This mimics the kopf.adopt() and similar functions
    """
    def init_metadata(obj):
        if 'metadata' not in obj:
            obj['metadata'] = {}

        if 'annotations' not in obj['metadata']:
            obj['metadata']['annotations'] = {}

    # Add annotations to the main object
    for obj in objs:
        for k, v in annotations.items():
            init_metadata(obj)
                
            obj['metadata']['annotations'][k] = v

        # Add annotations to the nested objects
        if nested is not None:
            current_obj = obj
            path_elts = nested.split('.')
            for elt in path_elts:
                if elt in current_obj:
                    current_obj = current_obj[elt]
                    init_metadata(current_obj)
                    for k, v in annotations.items():
                        current_obj['metadata']['annotations'][k] = v



def load_from_yaml(file, type: str=None):
    class K8sResponse():
        def __init__(self, data):
            if isinstance(data, str):
                self.data = data
            else:
                self.data = json.dumps(data)

    obj_dict = yaml.safe_load(file)
    obj = K8sResponse(obj_dict)

    if type is None:
        version = obj_dict.get('apiVersion', '').split('/')[-1].upper()
        kind = obj_dict.get('kind')
        type = "{}{}".format(version, kind)

    obj = kubernetes.client.ApiClient().deserialize(obj, type)
    return obj

def update_array(obj, where=None, value=None, path=None):
    current_obj = obj
    if path is not None:
        for path_elt in path.split('/'):
            if len(path_elt) > 0:
                current_obj = current_obj[path_elt]

    if not isinstance(current_obj, list):
        raise TerraformResourceException('{} is not an array (got {}'.format(path, type(path).__name__))
        
    for idx, array_elt in enumerate(current_obj):
        for cond, cond_v in where.items():
            if hasattr(array_elt, '__getitem__'):
                # If the object is subscriptable, access the item via []
                if array_elt[cond] == cond_v:
                    current_obj[idx] = value
            else:
                # Otherwise call the property
                if getattr(array_elt, cond) == cond_v:
                    current_obj[idx] = value

def b64encode(str):
    return base64.b64encode(str.encode('ascii')).decode()

def current_file_path():
    abs_path = os.path.abspath((inspect.stack()[1])[1])
    return os.path.dirname(abs_path)
