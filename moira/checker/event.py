from datetime import datetime
from twisted.internet import defer
from twisted.python import log

from moira import config
from moira.checker import state


@defer.inlineCallbacks
def compare_states(trigger,
                   current_state,
                   last_state,
                   timestamp,
                   value=None,
                   metric=None):
    current_state_value = current_state["state"]
    last_state_value = last_state["state"]
    last_state["state"] = current_state_value

    if current_state.get("event_timestamp") is None:
        current_state["event_timestamp"] = timestamp

    event = {
        "trigger_id": trigger.id,
        "state": current_state_value,
        "old_state": last_state_value,
        "timestamp": timestamp,
        "metric": metric
    }

    if current_state_value == last_state_value:
        remind_interval = config.BAD_STATES_REMINDER.get(current_state_value)
        if remind_interval is None or timestamp - last_state.get("event_timestamp", timestamp) < remind_interval:
            if not last_state.get("suppressed") or current_state_value == state.OK:
                raise StopIteration
        else:
            event["msg"] = "This metric has been in bad state for more than %s hours - please, fix." % \
                            (remind_interval / 3600)
    trigger.update_score = True
    current_state["event_timestamp"] = timestamp
    last_state["event_timestamp"] = timestamp
    if value is not None:
        event["value"] = value
    current_state["suppressed"] = False
    last_state["suppressed"] = False
    if trigger.isSchedAllows(timestamp):
        state_maintenance = current_state.get("maintenance", 0)
        if trigger.maintenance >= timestamp:
            current_state["suppressed"] = True
            log.msg("Event %s suppressed due to maintenance until %s." %
                    (event, datetime.fromtimestamp(trigger.maintenance)))
        elif state_maintenance >= timestamp:
            current_state["suppressed"] = True
            log.msg("Event %s suppressed due to metric %s maintenance until %s." %
                    (event, metric, datetime.fromtimestamp(state_maintenance)))
        else:
            log.msg("Writing new event: %s" % event)
            yield trigger.db.pushEvent(event)
    else:
        current_state["suppressed"] = True
        log.msg("Event %s suppressed due to trigger schedule" % str(event))
