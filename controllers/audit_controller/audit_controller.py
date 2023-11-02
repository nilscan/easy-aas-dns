import kopf

EVENT = 25

# @kopf.on.create("easyaas.dev", kopf.EVERYTHING)
@kopf.on.create(category="easyaas")
def audit_create(logger, meta, spec, **kwargs):
    event = {
        "event": "create",
        "objectMeta": dict(meta),
        "new": {
            "spec": dict(spec),
        },
    }
    logger.log(EVENT, event)

@kopf.on.update(category="easyaas")
def audit_update(logger, meta, old, new, diff, **kwargs):
    event = {
        "event": "update",
        "objectMeta": dict(meta),
        "old": old,
        "new": new,
        "diff": tuple(diff),
    }
    logger.info(event)

@kopf.on.delete(category="easyaas")
def audit_delete(logger, meta, spec, **kwargs):
    event = {
        "event": "delete",
        "objectMeta": dict(meta),
        "old": {
            "spec": dict(spec),
        },
    }
    logger.info(event)


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.posting.enabled = False # Do not publish k8s events
    settings.persistence.progress_storage = kopf.AnnotationsProgressStorage(prefix='easyaas.dev')
