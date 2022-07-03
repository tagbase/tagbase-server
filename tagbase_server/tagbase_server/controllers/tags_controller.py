from tagbase_server.utils.db_utils import connect

from tagbase_server.models.tag200 import Tag200  # noqa: E501
from tagbase_server.models.tag_put200 import TagPut200  # noqa: E501

import logging

logger = logging.getLogger(__name__)


def get_tag(tag_id):  # noqa: E501
    """Get information about an individual tag

    Get information about an individual tag # noqa: E501

    :param tag_id: Existing tag id
    :type tag_id:

    :rtype: Union[Tag200, Tuple[Tag200, int], Tuple[Tag200, int, Dict[str, str]]
    """
    conn = connect()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM submission WHERE tag_id = %s ORDER BY submission_id",
                (tag_id,),
            )
            results = cur.fetchall()
            tags = []
            for row in results:
                cur.execute(
                    "SELECT mt.attribute_name, md.attribute_value FROM metadata_types mt, metadata md "
                    "WHERE md.attribute_id = mt.attribute_id;"
                )
                meta_dict = {}
                for md_row in cur.fetchall():
                    meta_dict[md_row[0]] = md_row[1].strip('\"')
                tags.append(
                    {
                        "submission_id": row[0],
                        "tag_id": row[1],
                        "date_time": row[2],
                        "filename": row[3],
                        "solution_id": row[4],
                        "notes": row[5],
                        "metadata": meta_dict,
                    }
                )
            return Tag200.from_dict({"tag": tags})


def list_tags():  # noqa: E501
    """Get information about all tags

    Get information about all tags # noqa: E501


    :rtype: Union[Tags200, Tuple[Tags200, int], Tuple[Tags200, int, Dict[str, str]]
    """
    conn = connect()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT tag_id, filename FROM submission ORDER BY tag_id",
            )
            tags = []
            for tag in cur.fetchall():
                tags.append({"tag_id": tag[0], "filename": tag[1]})
            cur.execute(
                "SELECT COUNT(DISTINCT tag_id) FROM submission",
            )
            count = cur.fetchone()[0]
            return {"count": count, "tags": tags}


def put_tag(tag_id, sub_id, notes=None, solution_id=None):  # noqa: E501
    """Update the &#39;solution id&#39; and/or &#39;notes&#39; associated with a tag submission

    Update a tag submission # noqa: E501

    :param tag_id: Existing tag id
    :type tag_id:
    :param sub_id: Existing submission id for an existing tag
    :type sub_id:
    :param notes: Free-form text field where details of submitted eTUFF file for ingest can be provided e.g. submitter name, etuff data contents (tag metadata and measurements + primary position data, or just secondary solution-positional meta/data)
    :type notes: str
    :param solution_id: Unique numeric identifier for a given tag geolocation dataset solution. solution_id&#x3D;1 is assigned to the primary or approved solution. Incremented solution_id&#39;s are assigned to other positional dataset solutions for a given tag_id and submission_id
    :type solution_id:

    :rtype: Union[TagPut200, Tuple[TagPut200, int], Tuple[TagPut200, int, Dict[str, str]]
    """
    conn = connect()
    with conn:
        with conn.cursor() as cur:
            if notes is not None:
                cur.execute(
                    "UPDATE submission SET notes = %s WHERE tag_id = %s AND submission_id = %s",
                    (notes, tag_id, sub_id),
                )
            if solution_id is not None:
                cur.execute(
                    "UPDATE submission SET solution_id = %s WHERE tag_id = %s AND submission_id = %s",
                    (solution_id, tag_id, sub_id),
                )
                # possibly refactor into a TRIGGER
                cur.execute(
                    "UPDATE data_position SET solution_id = %s WHERE tag_id = %s AND submission_id = %s",
                    (solution_id, tag_id, sub_id),
                )
                # possibly refactor into a TRIGGER
                cur.execute(
                    "UPDATE metadata_position SET solution_id = %s WHERE tag_id = %s AND submission_id = %s",
                    (solution_id, tag_id, sub_id),
                )
            message = f"Tag: '{int(tag_id)}' submission id: '{int(sub_id)}' successfully updated."
            return TagPut200.from_dict({"code": "200", "message": message})
