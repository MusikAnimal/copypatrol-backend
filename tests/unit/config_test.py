from __future__ import annotations

import pytest

from copypatrol_backend import config


TEST_CONFIG = "testing/unit/config.ini"


@pytest.fixture(autouse=True)
def mock_configs(mocker):
    mocker.patch("copypatrol_backend.config.DB_CONFIGS", [TEST_CONFIG]),
    mocker.patch("copypatrol_backend.config.PKG_CONFIGS", [TEST_CONFIG]),
    yield


def test_database_config():
    expected = config.DatabaseConfig(  # nosec: B106
        drivername="mysql+pymysql",
        username="test-db-user",
        password="test-db-password",
        database="test-db-name",
        host="localhost",
        port=3306,
    )
    assert config.database_config.__wrapped__() == expected


def test_domains():
    expected = ["en.wikipedia.org", "es.wikipedia.org"]
    assert config.domains.__wrapped__() == expected


def test_ignore_list_title():
    assert config.ignore_list_title.__wrapped__() == "example"


def test_tca_config():
    expected = config.TCAConfig(
        domain="test-tca-domain.com",
        key="test-tca-key",
    )
    assert config.tca_config.__wrapped__() == expected


@pytest.mark.parametrize(
    "domain, expected",
    [
        (
            "en.wikipedia.org",
            config.SiteConfig(
                domain="en.wikipedia.org",
                enabled=True,
                namespaces=[0, 2, 118],
                pagetriage_namespaces=[0, 118],
            ),
        ),
        (
            "es.wikipedia.org",
            config.SiteConfig(
                domain="es.wikipedia.org",
                enabled=True,
                namespaces=[0, 2],
                pagetriage_namespaces=[],
            ),
        ),
        (
            "fr.wikipedia.org",
            config.SiteConfig(
                domain="fr.wikipedia.org",
                enabled=False,
                namespaces=[],
                pagetriage_namespaces=[],
            ),
        ),
    ],
)
def test_site_config(domain, expected):
    assert config.site_config.__wrapped__(domain) == expected
