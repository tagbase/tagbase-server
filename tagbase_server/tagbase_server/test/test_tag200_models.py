# coding: utf-8

import pytest

from tagbase_server.encoder import ModelJSONEncoder, create_jsonifier
from tagbase_server.models.tag200 import Tag200
from tagbase_server.models.tag200_collection import Tag200Collection
from tagbase_server.models.tag200_summary import Tag200Summary
from tagbase_server.models.tag_submission import TagSubmission


def test_tag200_summary_round_trip():
    summary = Tag200Summary(tag_id=7, filename="demo.etuff")
    assert summary.tag_id == 7
    assert summary.filename == "demo.etuff"

    summary.tag_id = 8
    summary.filename = "other.etuff"
    assert summary.to_dict() == {"tag_id": 8, "filename": "other.etuff"}
    assert "8" in summary.to_str()

    cloned = Tag200Summary.from_dict({"tag_id": 8, "filename": "other.etuff"})
    assert cloned == summary
    assert not (cloned != summary)


def test_tag200_collection_round_trip_and_validation():
    summary = Tag200Summary(tag_id=1, filename="a.etuff")
    collection = Tag200Collection(count=1, tags=[summary])
    assert collection.count == 1
    assert collection.tags[0].tag_id == 1

    collection.count = 2
    collection.tags = [
        Tag200Summary(tag_id=1, filename="a.etuff"),
        Tag200Summary(tag_id=2, filename="b.etuff"),
    ]
    payload = collection.to_dict()
    assert payload["count"] == 2
    assert len(payload["tags"]) == 2

    restored = Tag200Collection.from_dict(payload)
    assert restored.count == 2
    assert restored.tags[1].filename == "b.etuff"

    with pytest.raises(ValueError):
        collection.tags = []
    with pytest.raises(ValueError):
        collection.tags = [summary] * 100001


def test_tag200_round_trip_and_validation():
    submission = TagSubmission(
        tag_id=3,
        submission_id=1,
        filename="tag.etuff",
        version="1",
    )
    tag = Tag200(tag=[submission], tag_id=3, filename="tag.etuff")
    assert tag.tag_id == 3
    assert tag.filename == "tag.etuff"
    assert len(tag.tag) == 1

    tag.tag_id = 4
    tag.filename = "renamed.etuff"
    tag.tag = [submission]
    payload = tag.to_dict()
    assert payload["tag_id"] == 4
    assert payload["filename"] == "renamed.etuff"
    assert isinstance(payload["tag"], list)

    restored = Tag200.from_dict(
        {
            "tag": [
                {
                    "tag_id": 4,
                    "submission_id": 1,
                    "filename": "renamed.etuff",
                    "version": "1",
                }
            ],
            "tag_id": 4,
            "filename": "renamed.etuff",
        }
    )
    assert restored.tag_id == 4
    assert restored.filename == "renamed.etuff"
    assert len(restored.tag) == 1

    with pytest.raises(ValueError):
        tag.tag = []
    with pytest.raises(ValueError):
        tag.tag = [submission] * 101


def test_model_jsonifier_omits_nulls_and_falls_back():
    encoder = ModelJSONEncoder()
    summary = Tag200Summary(tag_id=9, filename=None)
    encoded = encoder.default(summary)
    assert encoded == {"tag_id": 9}
    assert "filename" not in encoded

    with pytest.raises(TypeError):
        encoder.default(object())

    jsonifier = create_jsonifier()
    payload = jsonifier.dumps(Tag200Summary(tag_id=1, filename="x.etuff"))
    assert "x.etuff" in payload
