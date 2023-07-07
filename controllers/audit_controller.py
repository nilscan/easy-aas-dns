import kopf

EVENT = 25

@kopf.on.create(category="easyaas", kopf.EVERYTHING)
def audit_create(logger, body, spec, **kwargs):
    event = {
        "event": "create",
        "new": {
            "spec": dict(spec),
        },
    }
    logger.log(EVENT, event)

@kopf.on.update(category="easyaas", kopf.EVERYTHING)
def audit_update(logger, body, old, new, diff, **kwargs):
    event = {
        "event": "update",
        "old": old,
        "new": new,
        "diff": tuple(diff),
    }
    logger.info(event)

@kopf.on.delete(category="easyaas", kopf.EVERYTHING)
def audit_delete(logger, body, spec, **kwargs):
    event = {
        "event": "delete",
        "old": {
            "spec": dict(spec),
        },
    }
    logger.info(event)


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.posting.enabled = False # Do not publish k8s events
    settings.persistence.progress_storage = kopf.AnnotationsProgressStorage(prefix='easyaas.dev')