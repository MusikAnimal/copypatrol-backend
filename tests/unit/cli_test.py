from __future__ import annotations

import datetime
from argparse import Namespace
from uuid import UUID

import pytest
import pywikibot

from copypatrol_backend import cli


SITE = pywikibot.Site("meta")


def test_parse_ignore_list(mocker):
    text = r"""
# comment
 # space before comment
 \b.*\.wikipedia\.org\b # Wikipedia
\b192\.168\.1\.1\b  # IP
 \b\zee\b # invalid
"""
    expected = [r"\b.*\.wikipedia\.org\b", r"\b192\.168\.1\.1\b"]
    mocker.patch(
        "pywikibot.Page.text",
        new_callable=mocker.PropertyMock,
        return_value=text,
    )
    result = [p.pattern for p in cli._parse_ignore_list(SITE)]
    assert result == expected


def test_parse_ignore_list_none(mocker):
    mocker.patch(
        "copypatrol_backend.cli.ignore_list_title",
        return_value="",
    )
    assert cli._parse_ignore_list(SITE) == []


@pytest.mark.parametrize(
    "args, expected",
    [
        pytest.param(
            ("store-changes",),
            Namespace(action="store-changes", since=None, total=None),
            id="store-changes",
        ),
        pytest.param(
            ("store-changes", "--since", "2022-01-01T00:00:00"),
            Namespace(
                action="store-changes",
                since=datetime.datetime(2022, 1, 1, 0, 0, 0),
                total=None,
            ),
            id="store-changes since",
        ),
        pytest.param(
            ("store-changes", "-n", "10"),
            Namespace(
                action="store-changes",
                since=None,
                total=10,
            ),
            id="store-changes total",
        ),
        pytest.param(
            ("check-changes",),
            Namespace(action="check-changes"),
            id="check-changes",
        ),
        pytest.param(
            ("reports",),
            Namespace(action="reports"),
            id="reports",
        ),
        pytest.param(
            ("db", "--create-tables"),
            Namespace(
                action="db",
                create_tables=True,
                remove_revision=None,
                remove_submission=None,
            ),
            id="db create tables",
        ),
        pytest.param(
            ("db", "--remove-revision", "123"),
            Namespace(
                action="db",
                create_tables=False,
                remove_revision=123,
                remove_submission=None,
            ),
            id="db remove-revision",
        ),
        pytest.param(
            (
                "db",
                "--remove-submission",
                "7b3074cf-4d3b-4648-8c68-f56aee0f1058",
            ),
            Namespace(
                action="db",
                create_tables=False,
                remove_revision=None,
                remove_submission=UUID("7b3074cf-4d3b-4648-8c68-f56aee0f1058"),
            ),
            id="db remove-submission",
        ),
    ],
)
def test_parse_script_args(args, expected):
    assert cli._parse_script_args(*args) == expected


@pytest.mark.parametrize(
    "args",
    [
        ("foo",),
        ("store-changes", "--foo", "bar"),
        ("store-changes", "--since", "2022-01-01T00:00:00", "-n", "ten"),
        ("store-changes", "--since", "2022-01-01T00:00:00", "--foo"),
        ("check-changes", "foo"),
        ("reports", "foo"),
        ("db", "--create-tables", "foo"),
        ("db", "--remove-revision"),
        ("db", "--remove-revision", "foo"),
        ("db", "--remove-submission"),
    ],
)
def test_parse_script_args_exits(args):
    with pytest.raises(SystemExit):
        cli._parse_script_args(*args)
