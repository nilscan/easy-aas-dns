from datetime import datetime
from zoneinfo import ZoneInfo


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

