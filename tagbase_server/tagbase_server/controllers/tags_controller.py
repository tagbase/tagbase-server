import connexion
import six
from typing import Dict
from typing import Tuple
from typing import Union

from tagbase_server.models.error_container import ErrorContainer  # noqa: E501
from tagbase_server.models.tag200 import Tag200  # noqa: E501
from tagbase_server.models.tag_put200 import TagPut200  # noqa: E501
from tagbase_server.models.tags200 import Tags200  # noqa: E501
from tagbase_server import util


def delete_sub(sub_id, tag_id):  # noqa: E501
    """Delete a tag submission

    Delete a tag submission # noqa: E501

    :param sub_id: Existing submission id for an existing tag
    :type sub_id: int
    :param tag_id: Existing tag id
    :type tag_id: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return "do some magic!"


def delete_tag(tag_id):  # noqa: E501
    """Delete an individual tag

    Delete an individual tag # noqa: E501

    :param tag_id: Existing tag id
    :type tag_id: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return "do some magic!"


def delete_tags():  # noqa: E501
    """Delete all tags

    Delete all tags # noqa: E501


    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return "do some magic!"


def get_tag(tag_id):  # noqa: E501
    """Get information about an individual tag

    Get information about an individual tag # noqa: E501

    :param tag_id: Existing tag id
    :type tag_id: int

    :rtype: Union[Tag200, Tuple[Tag200, int], Tuple[Tag200, int, Dict[str, str]]
    """
    return "do some magic!"


def list_tags():  # noqa: E501
    """Get information about all tags

    Get information about all tags # noqa: E501


    :rtype: Union[Tags200, Tuple[Tags200, int], Tuple[Tags200, int, Dict[str, str]]
    """
    return "do some magic!"


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
    return "do some magic!"
