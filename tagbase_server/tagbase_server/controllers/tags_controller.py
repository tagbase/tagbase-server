from tagbase_server.utils.db_utils import connect

from tagbase_server.models.tag200 import Tag200  # noqa: E501
from tagbase_server.models.tag_put200 import TagPut200  # noqa: E501

import logging

logger = logging.getLogger(__name__)


def delete_sub(sub_id, tag_id):  # noqa: E501
    """Delete a tag submission

    Delete a tag submission # noqa: E501

    :param sub_id: Existing submission id for an existing tag
    :type sub_id: int
    :param tag_id: Existing tag id
    :type tag_id: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    conn = connect()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "CALL sp_delete_submission(%s, %s);", (int(tag_id), int(sub_id))
            )


def delete_tag(tag_id):  # noqa: E501
    """Delete an individual tag

    Delete an individual tag # noqa: E501

    :param tag_id: Existing tag id
    :type tag_id: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    conn = connect()
    with conn:
        with conn.cursor() as cur:
            cur.execute("CALL sp_delete_tag(%s);", (tag_id,))


def delete_tags():  # noqa: E501
    """Delete all tags

    Delete all tags # noqa: E501


    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    conn = connect()
    with conn:
        with conn.cursor() as cur:
            cur.execute("CALL sp_delete_all_tags();")


def get_tag(tag_id):  # noqa: E501
    """Get information about an individual tag

    Get information about an individual tag # noqa: E501

    :param tag_id: Existing tag id
    :type tag_id: int

    :rtype: Union[Tag200, Tuple[Tag200, int], Tuple[Tag200, int, Dict[str, str]]
    """
    conn = connect()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM submission WHERE tag_id = %s ORDER BY submission_id",
                (tag_id,),
            )
            subs_results = cur.fetchall()
            subs = []
            for row in subs_results:
                cur.execute(
                    "SELECT mt.attribute_name, md.attribute_value FROM metadata_types mt, metadata md "
                    "WHERE md.attribute_id = mt.attribute_id;"
                )
                meta_dict = {}
                md_results = cur.fetchall()
                logger.info(md_results)
                for md_row in md_results:
                    meta_dict[md_row[0]] = md_row[1]
                subs.append(
                    {
                        "submission_id": row[0],
                        "tag_id": row[1],
                        "date_time": row[2],
                        "filename": row[3],
                        "version": row[4],
                        "notes": row[5],
                        "hash_sha256": row[6],
                        "dataset_id": row[7],
                        "metadata": meta_dict,
                    }
                )
            return Tag200.from_dict({"tag": subs})


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


def replace_tag(sub_id, tag_id, notes=None, version=None):  # noqa: E501
    """Update the &#39;notes&#39; and/or &#39;version&#39; associated with a tag submission

    Update a tag submission # noqa: E501

    :param sub_id: Existing submission id for an existing tag
    :type sub_id: int
    :param tag_id: Existing tag id
    :type tag_id: int
    :param notes: Free-form text field where details of submitted eTUFF file for ingest can be provided e.g. submitter name, etuff data contents (tag metadata and measurements + primary position data, or just secondary solution-positional meta/data)
    :type notes: str
    :param version: Version identifier for the eTUFF tag data file ingested
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
                f"tag_id: '{int(tag_id)}' sub_id: '{int(sub_id)}' successfully updated."
            )
            return TagPut200.from_dict({"code": "200", "message": message})
