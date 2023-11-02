#!/usr/bin/env python3
import sys
import yaml
from os import listdir
from os.path import isfile, join

opa_dir = sys.argv[1]

files = [f for f in listdir(opa_dir) if isfile(join(opa_dir, f))]
cm = {
    'apiVersion': 'v1',
    'kind': 'ConfigMap',
    'metadata': {
        'name': 'opa-policy',
        'namespace': 'easyaas-dns-record',
        'labels': {
            'openpolicyagent.org/policy': 'rego',
        }

    },
    'data': {},
}

# Configure yaml to use multiline strings
def str_presenter(dumper, data):
    if data.count('\n') > 0:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)
yaml.add_representer(str, str_presenter)
yaml.representer.SafeRepresenter.add_representer(str, str_presenter) # to use with safe_dump

for file in files:
    with open(join(opa_dir, file), 'r') as f:
        cm['data'][file] = f.read()
print(yaml.dump(cm))
