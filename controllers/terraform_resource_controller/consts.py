import os

JOB_FINALIZER = 'easyaas.dev/job-finalizer'

WATCHED_RESOURCE_GROUP = os.environ.get('EASYAAS_WATCHED_RESOURCE_GROUP', 'easyaas.dev')
WATCHED_RESOURCE_NAME = os.environ.get('EASYAAS_WATCHED_RESOURCE_NAME', 'dnsrecords')
RESOURCE_CONFIG_FILE = os.environ.get('EASYAAS_RESOURCE_CONFIG_FILE', 'resources/dns-record/terraformresource.yaml')

MANAGED_BY = '{}.{}'.format(WATCHED_RESOURCE_NAME, WATCHED_RESOURCE_GROUP)
