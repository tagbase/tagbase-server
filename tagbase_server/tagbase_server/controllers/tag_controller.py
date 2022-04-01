from tagbase_server.db_utils import connect


def get_tag(tag_id):  # noqa: E501
    """Get information about an individual tag

    Get information about an individual tag # noqa: E501

    :param tag_id: submission id for an existing tag
    :type tag_id:

    :rtype: Response200
    """
    return "do some magic!"


def list_tags():  # noqa: E501
    """Get information about all tags

    Get information about all tags # noqa: E501


    :rtype: Response200
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
