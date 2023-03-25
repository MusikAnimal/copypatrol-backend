"""Command line interface."""
from __future__ import annotations

import argparse
import datetime
import re
from typing import TYPE_CHECKING
from uuid import UUID

import pywikibot

from copypatrol_backend import database
from copypatrol_backend.check_diff import check_diff
from copypatrol_backend.config import ignore_list_title, site_config
from copypatrol_backend.stream_listener import revision_stream
from copypatrol_backend.tca import TurnitinCoreAPI


if TYPE_CHECKING:
    from pywikibot.site import APISite


def _store_changes(
    site: APISite,
    /,
    *,
    since: datetime.datetime | None = None,
    total: int | None = None,
) -> None:
    for event in revision_stream(site, since=since, total=total):
        with database.Session.begin() as db_session:
            database.add_revision(
                session=db_session,
                page=pywikibot.Page(
                    pywikibot.Site(url=event["meta"]["uri"]),
                    event["page_title"],
                    event["page_namespace"],
                ),
                rev_id=event["rev_id"],
                rev_parent_id=event["rev_parent_id"],
                rev_timestamp=event["rev_timestamp"],
                rev_user_text=event["performer"]["user_text"],
            )


def _check_changes() -> None:
    api = TurnitinCoreAPI()
    with database.Session.begin() as db_session:
        for diff in database.diffs_by_status(
            db_session,
            [database.Status.UNSUBMITTED, database.Status.CREATED],
        ):
            site = pywikibot.Site(diff.lang, diff.project)
            page = pywikibot.Page(site, diff.page_title, diff.page_namespace)
            try:
                text = check_diff(page, diff.rev_parent_id, diff.rev_id)
            except Exception:  # pragma: no cover
                pywikibot.exception()
                continue
            if text is None:
                database.remove_revision(db_session, site, diff.rev_id)
                continue
            if diff.submission_id is None:
                try:
                    diff.submission_id = api.create_submission(
                        site=site,
                        title=f"Revision {diff.rev_id} of {page.title()}",
                        timestamp=diff.rev_timestamp,
                        owner=diff.rev_user_text,
                    )
                except Exception:  # pragma: no cover
                    pywikibot.exception()
                    continue
            assert isinstance(diff.submission_id, UUID)
            try:
                api.upload_submission(diff.submission_id, text)
            except Exception:  # pragma: no cover
                pywikibot.exception()
            else:
                diff.status = database.Status.UPLOADED.value


def _generate_reports() -> None:
    api = TurnitinCoreAPI()
    with database.Session.begin() as db_session:
        for diff in database.diffs_by_status(
            db_session,
            [database.Status.UPLOADED],
        ):
            assert isinstance(diff.submission_id, UUID)
            info = api.submission_info(diff.submission_id)
            if info["status"] == "COMPLETE":
                try:
                    api.generate_report(diff.submission_id)
                except Exception:  # pragma: no cover
                    pywikibot.exception()
                else:
                    diff.status = database.Status.PENDING.value
            elif info["status"] == "ERROR":
                pywikibot.log(info)
                error_code = info["error_code"]
                pywikibot.error(f"submission {error_code=}")
                if error_code == "PROCESSING_ERROR":
                    # retry as a new submission
                    diff.submission_id = None
                    diff.status = database.Status.UNSUBMITTED.value
                else:
                    db_session.delete(diff)
            elif info["status"] != "PROCESSING":
                pywikibot.log(info)
                pywikibot.error(f"unhandled status={info['status']}")


def _submit_pagetriage(site: APISite, page_id: int, rev_id: int, /) -> None:
    if not site.has_extension("PageTriage"):
        raise pywikibot.exceptions.UnknownExtension(  # pragma: no cover
            f"PageTriage is not enabled on {site!r}"
        )
    if not site.has_right("pagetriage-copyvio"):
        raise pywikibot.exceptions.UserRightsError(  # pragma: no cover
            f"{site.username()} does not have the required pagetriage-copyvio"
            " user right"
        )
    data = site.simple_request(
        action="pagetriagelist",
        page_id=page_id,
        formatversion="2",
    ).submit()["pagetriagelist"]
    if page_id in data["pages_missing_metadata"]:
        return None
    try:
        site.simple_request(
            action="pagetriagetagcopyvio",
            revid=rev_id,
            token=site.tokens["csrf"],
        ).submit()
    except pywikibot.exceptions.APIError:
        pywikibot.log(data)
        pywikibot.exception()
        pywikibot.error(f"failed to add {rev_id=} to PageTriage")
    else:
        pywikibot.log(f"{rev_id=} added to PageTriage")


def _check_reports(site: APISite, /) -> None:
    api = TurnitinCoreAPI()
    ignore_regexes = _parse_ignore_list(site)
    with database.Session.begin() as db_session:
        for diff in database.diffs_by_status(
            db_session,
            [database.Status.PENDING],
        ):
            assert isinstance(diff.submission_id, UUID)
            try:
                sources = api.report_sources(diff.submission_id)
            except Exception:  # pragma: no cover
                pywikibot.exception()
                continue
            if sources is None:
                continue
            sources = [
                source
                for source in sources
                if source.percent > 50
                if source.url is None
                or not any(i.search(source.url) for i in ignore_regexes)
            ]
            if sources:
                diff.sources = sources
                diff.status = database.Status.READY.value
                rev_site = pywikibot.Site(diff.lang, diff.project)
                config = site_config(rev_site.hostname())
                if diff.page_namespace in config.pagetriage_namespaces:
                    page = pywikibot.Page(
                        rev_site,
                        diff.page_title,
                        diff.page_namespace,
                    )
                    _submit_pagetriage(rev_site, page.pageid, diff.rev_id)
            else:
                db_session.delete(diff)


def _parse_ignore_list(site: APISite) -> list[re.Pattern[str]]:
    result: list[re.Pattern[str]] = []
    if not ignore_list_title():
        return result
    page = pywikibot.Page(site, ignore_list_title())
    for line in page.text.splitlines():
        line, _, _ = line.partition("#")
        line = line.strip()
        if not line:
            continue
        try:
            result.append(re.compile(line, flags=re.I))
        except Exception as e:
            pywikibot.error(e)
            pywikibot.error(f"invalid regex ignored: {line!r}")
    return result


def _parse_script_args(*args: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="copypatrol backend",
        allow_abbrev=False,
    )
    subparsers = parser.add_subparsers(dest="action", required=True)
    description = "store recent changes to be checked"
    store_subparser = subparsers.add_parser(
        "store-changes",
        description=description,
        help=description,
        allow_abbrev=False,
    )
    store_subparser.add_argument(
        "--since",
        type=datetime.datetime.fromisoformat,
        help="since the timestamp",
        metavar="YYYY-MM-DD HH:MM:SS",
    )
    store_subparser.add_argument(
        "--total",
        "-n",
        type=int,
        help="maximum number to store",
        metavar="N",
    )
    description = "check stored changes"
    subparsers.add_parser(
        "check-changes",
        description=description,
        help=description,
        allow_abbrev=False,
    )
    description = "check and generate reports"
    subparsers.add_parser(
        "reports",
        description=description,
        help=description,
        allow_abbrev=False,
    )
    db_subparser = subparsers.add_parser("db", allow_abbrev=False)
    db_group = db_subparser.add_mutually_exclusive_group(required=True)
    db_group.add_argument(
        "--create-tables",
        action="store_true",
        help="create the database tables",
    )
    db_group.add_argument(
        "--remove-revision",
        type=int,
        help="remove revision from the database",
        metavar="ID",
    )
    db_group.add_argument(
        "--remove-submission",
        type=UUID,
        help="remove submission from the database",
        metavar="ID",
    )
    return parser.parse_args(args=args)


def cli(*args: str) -> int:
    """CLI for the package."""
    local_args = pywikibot.handle_args(args, do_help=False)
    parsed_args = _parse_script_args(*local_args)
    site = pywikibot.Site()
    site.login()
    if parsed_args.action == "store-changes":
        _store_changes(site, since=parsed_args.since, total=parsed_args.total)
    if parsed_args.action == "check-changes":
        _check_changes()
    elif parsed_args.action == "reports":
        _check_reports(site)
        _generate_reports()
    elif parsed_args.action == "db":
        with database.Session.begin() as db_session:
            if parsed_args.create_tables:
                database.create_tables()
            elif parsed_args.remove_revision:
                database.remove_revision(
                    db_session,
                    site,
                    parsed_args.remove_revision,
                )
            elif parsed_args.remove_submission:
                database.remove_submission(
                    db_session,
                    parsed_args.remove_submission,
                )
    return 0
