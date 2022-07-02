from tagbase_server.utils.db_utils import connect

from tagbase_server.models.tag200 import Tag200  # noqa: E501
from tagbase_server.models.tag_put200 import TagPut200  # noqa: E501


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
                tags.append(
                    {
                        "submission_id": row[0],
                        "tag_id": row[1],
                        "date_time": row[2],
                        "filename": row[3],
                        "version": row[4],
                        "notes": row[5],
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
                "SELECT DISTINCT tag_id FROM submission ORDER BY tag_id",
            )
            tags = []
            for tag in cur.fetchall():
                tags.append(tag[0])
            cur.execute(
                "SELECT COUNT(DISTINCT tag_id) FROM submission",
            )
            count = cur.fetchone()[0]
            return {"count": count, "tag_ids": tags}


def put_tag(tag_id, sub_id, notes=None, version=None):  # noqa: E501
    """Update the &#39;version&#39; and/or &#39;notes&#39; associated with a tag submission

    Update a tag submission # noqa: E501

    :param tag_id: Existing tag id
    :type tag_id:
    :param sub_id: Existing submission id for an existing tag
    :type sub_id:
    :param notes: Free-form text field where details of submitted eTUFF file for ingest can be provided e.g. submitter name, etuff data contents (tag metadata and measurements + primary position data, or just  secondary solutionpositional meta/data)
    :type notes: str
    :param version: Version identifier for the eTUFF tag data file ingested.
    :type version: str

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
            if version is not None:
                cur.execute(
                    "UPDATE submission SET version = %s WHERE tag_id = %s AND submission_id = %s",
                    (version, tag_id, sub_id),
                )
            message = (
                f"Tag '{int(tag_id)}' submission '{int(sub_id)}' successfully updated."
            )
            return TagPut200.from_dict({"code": "200", "message": message})
