"""Check a diff."""
from __future__ import annotations

import difflib
import re
from contextlib import suppress
from functools import cache
from typing import TYPE_CHECKING

import mwparserfromhell
import pywikibot
from pywikibot.page import Revision
from pywikibot_extensions.page import Page


if TYPE_CHECKING:
    from pywikibot.site import APISite


@cache
def _category_regex(site: APISite, /) -> re.Pattern[str]:
    namespaces = "|".join(site.namespaces.CATEGORY)
    return re.compile(
        rf"\[\[\s*:?\s*({namespaces})\s*:[^\]]+?\]\]\s*",
        flags=re.I,
    )


@cache
def _file_name_regex(site: APISite, /) -> re.Pattern[str]:
    namespaces = "|".join(site.namespaces.FILE)
    extensions = "|".join([e["ext"] for e in site.siteinfo["fileextensions"]])
    return re.compile(rf"({namespaces})\s*:.+?\.({extensions})", flags=re.I)


def _clean_wikitext(text: str, /, *, site: APISite) -> str:
    text = text.strip()
    if not text:
        return ""

    # remove bold/italic wikitext markup
    text = re.sub(r"(?P<open>'{2,3})(.+?)(?P=open)", r"\2", text)

    text = _category_regex(site).sub("", text)

    # remove quotes of less than 50 words
    for quote in re.findall('".+?"', text):
        if len(quote.split()) < 50:
            text = text.replace(quote, "")

    wikicode = mwparserfromhell.parse(text, skip_style_tags=True)
    for link in wikicode.ifilter_external_links():
        wikicode.replace(link, link.title or "")
    text = wikicode.strip_code(keep_template_params=True)

    text = _file_name_regex(site).sub("", text)
    text = re.sub(r" {2,}", " ", text)
    text = "\n".join(line.strip() for line in text.splitlines())
    text = re.sub(r"( ?\n){3,}", r"\n\n", text)

    return text.strip()


def _added_revision_text(old: str, new: str, /, *, site: APISite) -> str:
    old = _clean_wikitext(old, site=site)
    new = _clean_wikitext(new, site=site)
    sm = difflib.SequenceMatcher(None, old, new)
    return "\n".join(
        part.strip(" ")
        for op, _, _, new_start, new_end in sm.get_opcodes()
        if op in ("insert", "replace")
        if new_end - new_start > 50
        if (part := "".join(new[new_start:new_end])) not in old
    ).strip()


def _load_revisions(
    site: APISite,
    revids: list[int],
    /,
) -> dict[int, Revision]:
    data = site.simple_request(
        action="query",
        revids=revids,
        prop="revisions",
        rvprop=site._rvprops(content=True),
        rvslots="*",
    ).submit()
    return {
        rev["revid"]: Revision(**rev)
        for page in data["query"]["pages"].values()
        for rev in page["revisions"]
    }


def check_diff(
    page: pywikibot.Page,
    old: int,
    new: int,
    /,
) -> str | None:
    """Compare changes between two revisions."""

    def _small_len(text: str) -> bool:
        if len(text) < 500:
            pywikibot.log(f"revision {new} to {page!r} too small to compare")
            return True
        return False

    revs = _load_revisions(page.site, [r for r in (old, new) if r > 0])
    new_rev = revs[new]
    if _small_len(new_rev.text):
        return None
    if old > 0:
        old_rev = revs[old]
        if "mw-rollback" in new_rev.tags or {"mw-undo", "twinkle"} & set(
            new_rev.tags
        ):
            pywikibot.log(f"revision {new} to {page!r} was a revert")
            return None
        if "mw-reverted" in new_rev.tags:
            pywikibot.log(f"revision {new} to {page!r} was reverted")
            return None
        added_text = _added_revision_text(
            old_rev.text,
            new_rev.text,
            site=page.site,
        )
    else:
        added_text = _clean_wikitext(new_rev.text, site=page.site)
    if _small_len(added_text):
        return None
    # remove text that may have been copied from a page linked in the comment
    if not new_rev.commenthidden and new_rev.comment:
        comment_wikicode = mwparserfromhell.parse(
            new_rev.comment, skip_style_tags=True
        )
        for wikilink in comment_wikicode.ifilter_wikilinks():
            with suppress(ValueError):
                linked_page = Page.from_wikilink(wikilink, page.site)
                if not linked_page.exists():
                    continue
                for rev in linked_page.revisions(total=2, content=True):
                    linked_page_text = _clean_wikitext(
                        rev.text, site=page.site
                    )
                    added_text = "\n".join(
                        part
                        for part in added_text.splitlines()
                        if not part.strip() or part not in linked_page_text
                    )
        if _small_len(added_text):
            return None
    return added_text
