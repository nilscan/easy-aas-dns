from controllers.helpers import load_from_yaml, add_annotations, update_array

def test_load_from_yaml(): 
    yaml = """
        apiVersion: batch/v1
        kind: Job
        metadata:
            name: terraform
        spec:
            template:
                spec:
                    containers:
                        - name: test
    """
    # Test with explicit type
    obj = load_from_yaml(yaml, 'V1Job')
    assert type(obj).__name__ == 'V1Job'
    assert obj.spec.template.spec.containers[0].name == 'test'

    # Test with autodetected type
    obj = load_from_yaml(yaml)
    assert obj.spec.template.spec.containers[0].name == 'test'


def test_add_annotations_on_empty_obj():
    obj = {}

    # Add root annotations
    add_annotations([obj], {'test': 'value'})
    assert obj['metadata']['annotations']['test'] == 'value' 

    # Adding abels on nested object should do nothing
    add_annotations([obj], annotations={'test': 'value'}, nested='spec.template')
    assert 'spec' not in obj


def test_add_annotations_alongside_existing_annotations():
    obj = {
        'metadata': {
            'annotations': {
                'another-annotation': 'test'
            }
        }
    }

    # Both annotations should be present
    add_annotations([obj], {'test': 'value'})
    assert obj['metadata']['annotations']['test'] == 'value' 
    assert obj['metadata']['annotations']['another-annotation'] == 'test' 

def test_add_annotations_replacing_existing_annotations():
    obj = {
        'metadata': {
            'annotations': {
                'test': 'previous-value'
            }
        }
    }

    # Both annotations should be present
    add_annotations([obj], {'test': 'value'})
    assert obj['metadata']['annotations']['test'] == 'value' 


def test_update_array():
    obj = {
        'key1': {
            'key2': [
                {
                    'type': 'not-the-type-you-re-looking-for'
                },
                {
                    'type': 'editme',
                    'another-value': True
                },
                {
                    'type': 'still-not-the-type-you-re-looking-for'
                },
            ]
        },
        'key3': 'something'
    }
    update_array(obj, '/key1/key2', {'type': 'editme'}, {'type': 'newobject', 'newfield': 'newvalue'})

    assert len(obj['key1']['key2']) == 3
    assert obj['key1']['key2'][0]['type'] == 'not-the-type-you-re-looking-for'
    assert obj['key1']['key2'][2]['type'] == 'still-not-the-type-you-re-looking-for'
    assert obj['key1']['key2'][1]['type'] == 'newobject'
    assert obj['key1']['key2'][1]['newfield'] == 'newvalue'
    assert 'another-value' not in obj['key1']['key2'][1]
