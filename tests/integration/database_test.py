from __future__ import annotations

import uuid

import pytest
import pywikibot
from sqlalchemy.sql.expression import text

from copypatrol_backend import database


UUID = uuid.uuid4()


@pytest.fixture
def diffs_data(request, db_session):
    sql_dct = {
        k: v.encode() if isinstance(v, str) else v
        for k, v in request.param.items()
    }
    cols = ", ".join(sql_dct)
    vals = ", ".join(f":{key}" for key in sql_dct)
    stmt = text(f"INSERT INTO `diffs` ({cols}) VALUES ({vals})")
    db_session.execute(stmt, sql_dct)
    db_session.commit()
    yield


def test_add_revision(db_session):
    site = pywikibot.Site("en", "wikipedia")
    page = pywikibot.Page(site, "Add revision")
    database.add_revision(
        session=db_session,
        page=page,
        rev_id=1001,
        rev_parent_id=1000,
        rev_timestamp=pywikibot.Timestamp.set_timestamp(
            "2022-01-01T01:01:01Z"
        ),
        rev_user_text="Examplé",
    )
    db_session.commit()
    expected = {
        "project": b"wikipedia",
        "lang": b"en",
        "page_namespace": 0,
        "page_title": b"Add_revision",
        "rev_id": 1001,
        "rev_parent_id": 1000,
        "rev_timestamp": b"20220101010101",
        "rev_user_text": "Examplé".encode(),
        "submission_id": None,
        "status": database.Status.UNSUBMITTED.value,
        "status_timestamp": None,
        "status_user_text": None,
    }
    stmt = text("SELECT * FROM `diffs` WHERE `page_title` = :title")
    result = db_session.execute(stmt, {"title": b"Add_revision"}).all()
    assert len(result) == 1
    res = result[0]._asdict()
    assert res.pop("diff_id") is not None
    # assert res.pop("status_timestamp") is not None
    assert res == expected


@pytest.mark.parametrize(
    "diffs_data,status",
    [
        (
            {
                "project": "wikipedia",
                "lang": "en",
                "page_namespace": 0,
                "page_title": "Records_by_status",
                "rev_id": 3000 + status,
                "rev_parent_id": 3000,
                "rev_timestamp": "20220101010101",
                "rev_user_text": "Example",
                "status": status,
                "status_timestamp": "20220101020202",
            },
            status,
        )
        for status in range(-4, 1)
    ],
    indirect=["diffs_data"],
)
def test_diffs_by_status(db_session, diffs_data, status):
    result = database.diffs_by_status(db_session, [database.Status(status)])
    assert len(result) == 1
    assert result[0].status == status


@pytest.mark.parametrize(
    "diffs_data",
    [
        {
            "project": "wikipedia",
            "lang": "en",
            "page_namespace": 0,
            "page_title": "Remove_revision",
            "rev_id": 4001,
            "rev_parent_id": 4000,
            "rev_timestamp": "20220101010101",
            "rev_user_text": "Example",
            "status": database.Status.PENDING.value,
            "status_timestamp": "20220101020202",
        },
    ],
    indirect=True,
)
def test_remove_revision(db_session, diffs_data):
    site = pywikibot.Site("en", "wikipedia")
    database.remove_revision(db_session, site, 4001)
    stmt = text("SELECT * FROM `diffs` WHERE `page_title` = :title")
    result = db_session.execute(stmt, {"title": b"Remove_revision"}).all()
    assert len(result) == 0


@pytest.mark.parametrize(
    "diffs_data",
    [
        {
            "project": "wikipedia",
            "lang": "en",
            "page_namespace": 0,
            "page_title": "Remove_submission",
            "rev_id": 5001,
            "rev_parent_id": 5000,
            "rev_timestamp": "20220101010101",
            "rev_user_text": "Example",
            "submission_id": str(UUID),
            "status": database.Status.PENDING.value,
            "status_timestamp": "20220101020202",
        },
    ],
    indirect=True,
)
def test_remove_submission(db_session, diffs_data):
    database.remove_submission(db_session, UUID)
    stmt = text("SELECT * FROM `diffs` WHERE `page_title` = :title")
    result = db_session.execute(stmt, {"title": b"Remove_submission"}).all()
    assert len(result) == 0
