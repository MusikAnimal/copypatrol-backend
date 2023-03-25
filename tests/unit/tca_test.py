from __future__ import annotations

from uuid import UUID

import pytest
import pywikibot

from copypatrol_backend.tca import Source, TurnitinCoreAPI
from testing.resources import resource


SID = UUID("7b3074cf-4d3b-4648-8c68-f56aee0f1058")


@pytest.fixture(autouse=True)
def mock_tca_eula(mock_responses):
    mock_responses._add_from_file(file_path="testing/unit/eula.yaml")
    yield


def test_latest_eula_version():
    assert TurnitinCoreAPI()._latest_eula_version() == "v1beta"


def test_create_submission(mock_responses):
    mock_responses._add_from_file(
        file_path="testing/unit/create-submission.yaml"
    )
    assert (
        TurnitinCoreAPI().create_submission(
            site=pywikibot.Site("en", "wikipedia"),
            title="unit test submission",
            timestamp=pywikibot.Timestamp.set_timestamp(
                "2022-12-02T02:12:22Z"
            ),
            owner="Example",
        )
        == SID
    )


def test_upload_submission(mock_responses):
    mock_responses._add_from_file(
        file_path="testing/unit/upload-submission.yaml"
    )
    TurnitinCoreAPI().upload_submission(
        SID,
        resource("Kommet,_ihr_Hirten-1126962296-added.txt"),
    )


def test_submission_info_complete(mock_responses):
    mock_responses._add_from_file(
        file_path="testing/unit/submission-info-complete.yaml"
    )
    info = TurnitinCoreAPI().submission_info(SID)
    assert info["status"] == "COMPLETE"


def test_submission_info_error(mock_responses):
    mock_responses._add_from_file(
        file_path="testing/unit/submission-info-error.yaml"
    )
    info = TurnitinCoreAPI().submission_info(SID)
    assert info["status"] == "ERROR"
    assert info["error_code"] == "PROCESSING_ERROR"


def test_generate_report(mock_responses):
    mock_responses._add_from_file(
        file_path="testing/unit/generate-report.yaml"
    )
    TurnitinCoreAPI().generate_report(SID)


def test_report_info(mock_responses):
    mock_responses._add_from_file(file_path="testing/unit/report-info.yaml")
    info = TurnitinCoreAPI()._report_info(SID)
    assert info["status"] == "COMPLETE"
    assert info["top_source_largest_matched_word_count"] == 100


SOURCES = [
    Source(
        submission_id=SID,
        description="http://www.singalongfestivetunes.com/christian-christmas-songs/come-all-ye-shepherds.htm",
        url="http://www.singalongfestivetunes.com/christian-christmas-songs/come-all-ye-shepherds.htm",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="http://www.santasearch.org/music.asp?PID=1&SongID=785",
        url="http://www.santasearch.org/music.asp?PID=1&SongID=785",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="http://www.reindeerland.org/classic-christmas-carols/come-all-ye-shepherds.htm",
        url="http://www.reindeerland.org/classic-christmas-carols/come-all-ye-shepherds.htm",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="http://www.parolesmania.com/paroles_chansons_de_noel_10575/paroles_come,_all_ye_shepherds_360290.html",
        url="http://www.parolesmania.com/paroles_chansons_de_noel_10575/paroles_come,_all_ye_shepherds_360290.html",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="http://www.bookofcarols.com/c/come_all_ye_shepherds.html",
        url="http://www.bookofcarols.com/c/come_all_ye_shepherds.html",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="http://www.oocities.org/heartland/pines/1107/clyrics4.html",
        url="http://www.oocities.org/heartland/pines/1107/clyrics4.html",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="http://www.merry-christmas.org.uk/classic-christmas-carols/come-all-ye-shepherds.htm",
        url="http://www.merry-christmas.org.uk/classic-christmas-carols/come-all-ye-shepherds.htm",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="http://reindeerland.org/classic-christmas-carols/come-all-ye-shepherds.htm",
        url="http://reindeerland.org/classic-christmas-carols/come-all-ye-shepherds.htm",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="http://santasearch.org/lyrics.asp?ID=996",
        url="http://santasearch.org/lyrics.asp?ID=996",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="http://santasearch.org/music.asp?PID=1&SongID=785",
        url="http://santasearch.org/music.asp?PID=1&SongID=785",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="http://hymns.athleo.net/c/come-all-ye-shepherds.html",
        url="http://hymns.athleo.net/c/come-all-ye-shepherds.html",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="https://doctormargo.blogspot.com/2017/12",
        url="https://doctormargo.blogspot.com/2017/12",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="http://doctormargo.blogspot.com/2017/12/december-31-2017.html",
        url="http://doctormargo.blogspot.com/2017/12/december-31-2017.html",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="http://doctormargo.blogspot.com/2017/12/",
        url="http://doctormargo.blogspot.com/2017/12/",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="http://doctormargo.blogspot.com/2017/",
        url="http://doctormargo.blogspot.com/2017/",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="https://bible.sabda.org/bible.php?book=42&chapter=2&tab=hymns",
        url="https://bible.sabda.org/bible.php?book=42&chapter=2&tab=hymns",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="http://allcarols.com/c/come_all_ye_shepherds_1.html",
        url="http://allcarols.com/c/come_all_ye_shepherds_1.html",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="https://alkitab.sabda.org/bible.php?book=42&chapter=2&tab=hymns",
        url="https://alkitab.sabda.org/bible.php?book=42&chapter=2&tab=hymns",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="https://alkitab.sabda.org/passage.php?passage=Luk+2%3A8+2%3A15+2%3A17+2%3A18+2%3A20+8%3A34+17%3A7&tab=hymns",
        url="https://alkitab.sabda.org/passage.php?passage=Luk+2%3A8+2%3A15+2%3A17+2%3A18+2%3A20+8%3A34+17%3A7&tab=hymns",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="https://alkitab.sabda.org/passage.php?passage=lukas+2%3A8-20&tab=hymns",
        url="https://alkitab.sabda.org/passage.php?passage=lukas+2%3A8-20&tab=hymns",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="https://alkitab.sabda.org/passage.php?passage=Luk+2%3A10-15&tab=hymns",
        url="https://alkitab.sabda.org/passage.php?passage=Luk+2%3A10-15&tab=hymns",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="https://alkitab.sabda.org/passage.php?passage=Lukas+2-3&tab=hymns",
        url="https://alkitab.sabda.org/passage.php?passage=Lukas+2-3&tab=hymns",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="https://christianchristmassongs.org/come-all-ye-shepherds/",
        url="https://christianchristmassongs.org/come-all-ye-shepherds/",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="http://christianchristmassongs.org/come-all-ye-shepherds/",
        url="http://christianchristmassongs.org/come-all-ye-shepherds/",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description="http://carols.co/come-all-ye-shepherds/",
        url="http://carols.co/come-all-ye-shepherds/",
        percent=89.28571,
    ),
    Source(
        submission_id=SID,
        description='"Adoration of the Shepherds", Wikipedia, en, 2022',
        url="https://en.wikipedia.org/wiki?curid=2349963",
        percent=28.571428,
    ),
]


def test_report_sources_inner(mock_responses):
    mock_responses._add_from_file(file_path="testing/unit/report-sources.yaml")
    assert TurnitinCoreAPI()._report_sources(SID) == SOURCES


def test_report_sources_processing(mocker):
    mocker.patch(
        "copypatrol_backend.tca.TurnitinCoreAPI._report_info",
        return_value={"status": "PROCESSING"},
    )
    assert TurnitinCoreAPI().report_sources(SID) is None


def test_report_sources_no_matches(mocker):
    mocker.patch(
        "copypatrol_backend.tca.TurnitinCoreAPI._report_info",
        return_value={
            "status": "COMPLETE",
            "top_source_largest_matched_word_count": 0,
        },
    )
    assert TurnitinCoreAPI().report_sources(SID) == []


def test_report_sources_matches(mock_responses):
    mock_responses._add_from_file(file_path="testing/unit/report-info.yaml")
    mock_responses._add_from_file(file_path="testing/unit/report-sources.yaml")
    assert TurnitinCoreAPI().report_sources(SID) == SOURCES
