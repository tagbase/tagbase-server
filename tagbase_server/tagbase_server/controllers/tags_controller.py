from tagbase_server.db_utils import connect

from tagbase_server.models.tag200 import Tag200  # noqa: E501


def get_tag(tag_id):  # noqa: E501
    """Get information about an individual tag

    Get information about an individual tag # noqa: E501

    :param tag_id: submission id for an existing tag
    :type tag_id:

    :rtype: Tag200
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


    :rtype: Tags200
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
