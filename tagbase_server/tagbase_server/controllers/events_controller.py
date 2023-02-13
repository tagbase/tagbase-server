from tagbase_server.models.event200 import Event200  # noqa: E501
from tagbase_server.models.event_put200 import EventPut200  # noqa: E501
from tagbase_server.models.events200 import Events200  # noqa: E501
from tagbase_server.models.response500 import Response500  # noqa: E501
from tagbase_server.utils.db_utils import connect
from tagbase_server import util

import logging

logger = logging.getLogger(__name__)


def get_event(event_id):  # noqa: E501
    """Get information about an individual event

    Get information about an individual event # noqa: E501

    :param event_id: Event UUID
    :type event_id: str
    :type event_id: str

    :rtype: Union[Event200, Tuple[Event200, int], Tuple[Event200, int, Dict[str, str]]
    """
    conn = connect()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM events_log WHERE event_id = %s",
                (event_id,),
            )
            result = cur.fetchone()
            return Event200.from_dict(
                {
                    "submission_id": result[0],
                    "tag_id": result[1],
                    "event_id": str(result[2]),
                    "event_category": result[3],
                    "event_name": result[4],
                    "time_start": result[5],
                    "time_end": result[6],
                    "duration": result[7],
                    "event_status": result[8],
                    "event_notes": result[9],
                }
            )


def list_all_events():  # noqa: E501
    """Get information about all events

    Get information about all events # noqa: E501


    :rtype: Union[Events200, Tuple[Events200, int], Tuple[Events200, int, Dict[str, str]]
    """
    conn = connect()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT event_id, tag_id, submission_id FROM events_log ORDER BY tag_id",
            )
            events = []
            for event in cur.fetchall():
                events.append(
                    {
                        "event_id": str(event[0]),
                        "tag_id": event[1],
                        "submission_id": event[2],
                    }
                )
            cur.execute(
                "SELECT COUNT(DISTINCT event_id) FROM events_log",
            )
            count = cur.fetchone()[0]
            return Events200.from_dict({"count": count, "events": events})


def list_events(tag_id, sub_id):  # noqa: E501
    """Get all events for a given tag submission

    Get all events for a given tag submission # noqa: E501

    :param tag_id: Numeric tag ID
    :type tag_id:
    :param sub_id: Numeric submission ID
    :type sub_id:

    :rtype: Union[Events200, Tuple[Events200, int], Tuple[Events200, int, Dict[str, str]]
    """
    conn = connect()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT event_id"
                "FROM events_log WHERE tag_id = %s AND submission_id = %s ORDER BY tag_id",
                (tag_id, sub_id),
            )
            events = []
            for event in cur.fetchall():
                events.append(
                    {
                        "event_id": str(event[0]),
                    }
                )
            cur.execute(
                "SELECT COUNT(DISTINCT event_id) FROM events_log",
            )
            count = cur.fetchone()[0]
            return Events200.from_dict({"count": count, "events": events})


def put_event(event_id, notes=None):  # noqa: E501
    """Update the &#39;notes&#39; associated with an event

    Update notes for an event # noqa: E501

    :param event_id: Event UUID
    :type event_id: str
    :type event_id: str
    :param notes: Free-form text field where details of submitted eTUFF file for ingest can be provided e.g. submitter name, etuff data contents (tag metadata and measurements + primary position data, or just secondary solution-positional meta/data)
    :type notes: str

    :rtype: Union[EventPut200, Tuple[EventPut200, int], Tuple[EventPut200, int, Dict[str, str]]
    """
    conn = connect()
    with conn:
        with conn.cursor() as cur:
            if notes is not None:
                cur.execute(
                    "UPDATE events_log SET event_notes = %s WHERE event_id = %s",
                    (notes, event_id),
                )
            message = f"Event: '{str(event_id)}' successfully updated."
            return EventPut200.from_dict({"code": "200", "message": message})
