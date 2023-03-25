"""Listen to EventStreams."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pywikibot.comms.eventstreams import EventStreams

from copypatrol_backend.config import domains, site_config


if TYPE_CHECKING:
    import datetime
    from collections.abc import Generator

    from pywikibot.site import APISite


def _site_filter(data: dict[str, Any], /) -> bool:
    domain = data["meta"]["domain"]
    if domain not in domains():
        return False
    if data["page_namespace"] not in site_config(domain).namespaces:
        return False
    return True


def revision_stream(
    site: APISite,
    *,
    since: datetime.datetime | None = None,
    total: int | None = None,
) -> Generator[dict[str, Any], None, None]:
    """Yield from the filtered revision stream."""
    stream = EventStreams(streams="revision-create", site=site, since=since)
    stream.register_filter(_site_filter)
    stream.register_filter(rev_content_changed=True)
    stream.register_filter(lambda data: not data["performer"]["user_is_bot"])
    stream.register_filter(lambda data: data["rev_len"] > 500)
    stream.set_maximum_items(total)
    yield from stream
