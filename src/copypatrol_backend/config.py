"""Configuration."""
from __future__ import annotations

import configparser
import os.path
from functools import cache
from typing import NamedTuple, TypedDict


PKG_CONFIGS = [os.path.expanduser("~/.copypatrol.ini"), ".copypatrol.ini"]
DB_CONFIGS = [
    os.path.expanduser("~/replica.my.cnf"),
    os.path.expanduser("~/.my.cnf"),
] + PKG_CONFIGS


class DatabaseConfig(TypedDict):
    """Database configuration."""

    drivername: str
    username: str | None
    password: str | None
    host: str | None
    port: int | None
    database: str | None


class SiteConfig(NamedTuple):
    """Site configuration."""

    domain: str
    enabled: bool
    namespaces: list[int]
    pagetriage_namespaces: list[int]


class TCAConfig(NamedTuple):
    """Turnitin Core API configuration."""

    domain: str
    key: str


def _config_parser() -> configparser.ConfigParser:
    return configparser.ConfigParser(
        converters={
            "listint": lambda x: [int(i) for i in x.split(",")],
        },
        default_section="copypatrol",
        interpolation=None,
    )


@cache
def database_config() -> DatabaseConfig:
    """Return the database configuration."""
    parser = _config_parser()
    parser.read(DB_CONFIGS)
    client = parser["client"]
    return DatabaseConfig(
        drivername=client["drivername"],
        username=client.get("username", client.get("user")),
        password=client.get("password"),
        host=client.get("host"),
        port=client.getint("port"),
        database=client.get("database"),
    )


@cache
def domains() -> list[str]:
    """Return enabled domains."""
    parser = _config_parser()
    parser.read(PKG_CONFIGS)
    domains = [
        section.removeprefix("copypatrol:")
        for section in parser.sections()
        if section.startswith("copypatrol:")
        if parser.getboolean(section, "enabled", fallback=False)
    ]
    assert domains
    return domains


@cache
def ignore_list_title() -> str:
    """Return title of the ignore list."""
    parser = _config_parser()
    parser.read(PKG_CONFIGS)
    return parser.get("copypatrol", "ignore-list-title", fallback="")


@cache
def site_config(domain: str) -> SiteConfig:
    """Return the site configuration."""
    parser = _config_parser()
    parser.read(PKG_CONFIGS)
    section = parser[f"copypatrol:{domain}"]
    return SiteConfig(
        domain=domain,
        enabled=section.getboolean("enabled", fallback=False),
        namespaces=section.getlistint("namespaces", fallback=[]),
        pagetriage_namespaces=section.getlistint(
            "pagetriage-namespaces",
            fallback=[],
        ),
    )


@cache
def tca_config() -> TCAConfig:
    """Return the TCA configuration."""
    parser = _config_parser()
    parser.read(PKG_CONFIGS)
    return TCAConfig(domain=parser["tca"]["domain"], key=parser["tca"]["key"])
