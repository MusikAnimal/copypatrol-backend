"""Configure pytest."""
from __future__ import annotations

from unittest import mock

import pytest
from pytest_socket import disable_socket  # type: ignore[import]
from responses import RequestsMock  # type: ignore[import]


def pytest_runtest_setup():
    disable_socket()


@pytest.fixture(autouse=True, scope="session")
def disable_pywikibot_cache():
    from pywikibot.data.api import CachedRequest, Request

    class NoCacheRequest(CachedRequest):  # pragma: no cover
        def submit(self):
            return Request.submit(self)

    with mock.patch("pywikibot.data.api.CachedRequest", NoCacheRequest):
        yield


@pytest.fixture(autouse=True, scope="session")
def mock_namespaces():
    from pywikibot.site import Namespace, NamespacesDict

    with mock.patch(
        "pywikibot.site.APISite.namespaces",
        new_callable=mock.PropertyMock,
        return_value=NamespacesDict(Namespace.builtin_namespaces()),
    ):
        yield


@pytest.fixture
def mock_responses():
    with RequestsMock(assert_all_requests_are_fired=False) as requests_mock:
        yield requests_mock
