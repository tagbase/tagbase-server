import connexion
import six
from typing import Dict
from typing import Tuple
from typing import Union

from tagbase_server.models.error_container import ErrorContainer  # noqa: E501
from tagbase_server.models.ingest200 import Ingest200  # noqa: E501
from tagbase_server import util


def ingest_get(file, notes=None, type=None, version=None):  # noqa: E501
    """Get network accessible file and execute ingestion

    Get network accessible file and execute ingestion # noqa: E501

    :param file: Location of a network accessible (file, ftp, http, https) file e.g. &#39;file:///usr/src/app/data/eTUFF-sailfish-117259.txt&#39;.
    :type file: str
    :param notes: Free-form text field where details of submitted eTUFF file for ingest can be provided e.g. submitter name, etuff data contents (tag metadata and measurements + primary position data, or just secondary solution-positional meta/data)
    :type notes: str
    :param type: Type of file to be ingested, defaults to &#39;etuff&#39;
    :type type: str
    :param version: Version identifier for the eTUFF tag data file ingested
    :type version: str

    :rtype: Union[Ingest200, Tuple[Ingest200, int], Tuple[Ingest200, int, Dict[str, str]]
    """
    return "do some magic!"


def ingest_post(filename, body, notes=None, type=None, version=None):  # noqa: E501
    """Post a local file and perform a ingest operation

    Post a local file and perform a ingest operation # noqa: E501

    :param filename: Free-form text field to explicitly define the name of the file to be persisted
    :type filename: str
    :param body:
    :type body: str
    :param notes: Free-form text field where details of submitted eTUFF file for ingest can be provided e.g. submitter name, etuff data contents (tag metadata and measurements + primary position data, or just secondary solution-positional meta/data)
    :type notes: str
    :param type: Type of file to be ingested, defaults to &#39;etuff&#39;
    :type type: str
    :param version: Version identifier for the eTUFF tag data file ingested
    :type version: str

    :rtype: Union[Ingest200, Tuple[Ingest200, int], Tuple[Ingest200, int, Dict[str, str]]
    """
    return "do some magic!"
