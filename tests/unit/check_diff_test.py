from __future__ import annotations

import re

import pytest
import pywikibot
from pywikibot.page import Revision

from copypatrol_backend import check_diff
from testing.resources import resource


SITE = pywikibot.Site("en", "wikipedia")


@pytest.fixture
def mock_filename_regex(mocker):
    regex = re.compile(r"(File|Image)\s*:.+?\.(png|gif|jpg|jpeg)", flags=re.I)
    mocker.patch(
        "copypatrol_backend.check_diff._file_name_regex",
        return_value=regex,
    )
    yield


def test_category_regex():
    expected = r"\[\[\s*:?\s*(Category)\s*:[^\]]+?\]\]\s*"
    assert check_diff._category_regex(SITE).pattern == expected


def test_file_name_regex(mocker):
    mocker.patch(
        "copypatrol_backend.check_diff.pywikibot.site.APISite.siteinfo",
        new_callable=mocker.PropertyMock,
        return_value={
            "fileextensions": [
                {"ext": ext} for ext in ["png", "gif", "jpg", "jpeg"]
            ]
        },
    )
    expected = r"(File|Image)\s*:.+?\.(png|gif|jpg|jpeg)"
    assert check_diff._file_name_regex(SITE).pattern == expected


def test_clean_wikitext(mock_filename_regex):
    text = resource("Kommet,_ihr_Hirten-1126962296.txt")
    expected = resource("Kommet,_ihr_Hirten-1126962296-cleaned.txt").strip()
    assert check_diff._clean_wikitext(text, site=SITE) == expected


def test_clean_wikitext_empty():
    assert check_diff._clean_wikitext("", site=SITE) == ""


def test_added_revision_text(mock_filename_regex):
    old = resource("Kommet,_ihr_Hirten-1125722395.txt")
    new = resource("Kommet,_ihr_Hirten-1126962296.txt")
    expected = resource("Kommet,_ihr_Hirten-1126962296-added.txt").strip()
    assert check_diff._added_revision_text(old, new, site=SITE) == expected


def test_load_revisions(mock_responses):
    revids = [1125722395, 1126962296]
    if SITE.is_oauth_token_available():  # pragma: no cover
        path = "testing/unit/load-revisions-oauth.yaml"
    else:  # pragma: no cover
        path = "testing/unit/load-revisions-nooauth.yaml"
    mock_responses._add_from_file(file_path=path)
    res = check_diff._load_revisions(SITE, revids)
    for revid in revids:
        assert revid in res
        assert res[revid].revid == revid
        expected_text = resource(f"Kommet,_ihr_Hirten-{revid}.txt").strip()
        assert res[revid].text == expected_text
        assert res[revid].commenthidden is False
    assert res[1125722395].comment == "See also 'List of Christmas carols"
    assert res[1125722395].tags == []
    assert (
        res[1126962296].comment
        == "better LilyPond score, incl. repeat; +English text."
    )
    assert res[1126962296].tags == ["wikieditor"]


@pytest.mark.parametrize(
    "old_text, new_text, new_comment, new_tags, added_text",
    [
        pytest.param(
            resource("Kommet,_ihr_Hirten-1125722395.txt"),
            resource("Kommet,_ihr_Hirten-1126962296.txt"),
            "another edit summary",
            [],
            resource("Kommet,_ihr_Hirten-1126962296-added.txt").strip(),
            id="Kommet",
        ),
        pytest.param(
            "foo bar" * 100,
            "small" * 50,
            "another edit summary",
            [],
            None,
            id="small addition 1",
        ),
        pytest.param(
            "foo bar" * 100,
            f'{"baz " * 70} "{"small " * 40}"',
            "another edit summary",
            [],
            None,
            id="small addition 2",
        ),
        pytest.param(
            "foo bar" * 100,
            f'{"baz" * 500} "short quote"',
            "another edit summary",
            [],
            "baz" * 500,
            id="short quote",
        ),
        pytest.param(
            "foo bar" * 100,
            f'"{"baz " * 500}"',
            "another edit summary",
            [],
            f'"{"baz " * 500}"',
            id="long quote",
        ),
        pytest.param(
            "foo bar" * 100,
            "baz" * 500,
            "another edit summary",
            ["mw-rollback"],
            None,
            id="mw-rollback",
        ),
        pytest.param(
            "foo bar" * 100,
            "baz" * 500,
            "another edit summary",
            ["mw-rollback", "foo"],
            None,
            id="mw-rollback foo",
        ),
        pytest.param(
            "foo bar" * 100,
            "baz" * 500,
            "another edit summary",
            ["mw-undo", "twinkle"],
            None,
            id="mw-undo twinkle",
        ),
        pytest.param(
            "foo bar" * 100,
            "baz" * 500,
            "another edit summary",
            ["mw-undo", "twinkle", "foo"],
            None,
            id="mw-undo twinkle foo",
        ),
        pytest.param(
            "foo bar" * 100,
            "baz" * 500,
            "another edit summary",
            ["mw-reverted"],
            None,
            id="mw-reverted",
        ),
        pytest.param(
            "foo bar" * 100,
            "baz" * 500,
            "another edit summary",
            ["mw-reverted", "foo"],
            None,
            id="mw-reverted foo",
        ),
        pytest.param(
            "foo bar" * 100,
            "baz" * 500,
            "",
            [],
            "baz" * 500,
            id="no comment",
        ),
    ],
)
def test_check_diff(
    mocker,
    mock_filename_regex,
    old_text,
    new_comment,
    new_text,
    new_tags,
    added_text,
):
    page = pywikibot.Page(SITE, "Barack Obama")
    old_rev = Revision(
        revid=1088665641,
        comment="some edit summary",
        slots={"main": {"*": old_text}},
        tags=[],
        user="A",
    )
    new_rev = Revision(
        revid=1089519971,
        comment=new_comment,
        slots={"main": {"*": new_text}},
        tags=new_tags,
        user="B",
    )
    mocker.patch(
        "copypatrol_backend.check_diff._load_revisions",
        return_value={
            old_rev.revid: old_rev,
            new_rev.revid: new_rev,
        },
    )
    result = check_diff.check_diff(page, old_rev.revid, new_rev.revid)
    assert result == added_text


@pytest.mark.parametrize(
    "linked_page_exists, copied_text, added_text",
    [
        pytest.param(
            True,
            resource("Kommet,_ihr_Hirten-1126962296.txt").strip(),
            None,
            id="new page copied text from existing page",
        ),
        pytest.param(
            False,
            "something not copied",
            resource("Kommet,_ihr_Hirten-1126962296-cleaned.txt").strip(),
            id="new page not copied",
        ),
    ],
)
def test_check_diff_new_links(
    mocker,
    mock_filename_regex,
    linked_page_exists,
    copied_text,
    added_text,
):
    mocker.patch("pywikibot.site.APISite.loadrevisions")
    mocker.patch("pywikibot.Page.exists", return_value=linked_page_exists)
    mocker.patch(
        "pywikibot.Page.revisions",
        return_value=[
            Revision(
                revid=987654321,
                comment="something",
                slots={
                    "main": {
                        "*": copied_text,
                    },
                },
                tags=["foo"],
                user="C",
            ),
        ],
    )
    page = pywikibot.Page(SITE, "Kommet, ihr Hirten")
    new_rev = Revision(
        revid=1126962296,
        comment="some text copied from [[example]]",
        slots={
            "main": {
                "*": resource("Kommet,_ihr_Hirten-1126962296.txt"),
            }
        },
        tags=[],
        user="B",
    )
    mocker.patch(
        "copypatrol_backend.check_diff._load_revisions",
        return_value={
            new_rev.revid: new_rev,
        },
    )
    assert check_diff.check_diff(page, 0, new_rev.revid) == added_text
