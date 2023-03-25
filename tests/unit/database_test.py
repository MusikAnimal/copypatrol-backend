from __future__ import annotations

import uuid

import pytest
from pywikibot.time import Timestamp
from sqlalchemy import Dialect, LargeBinary

from copypatrol_backend import database


database._BinaryBase.impl = LargeBinary


DIALECT = Dialect()
UUID = uuid.uuid4()


@pytest.mark.parametrize(
    "value1,value2",
    [
        (None, None),
        ("Example", b"Example"),
        ("Éxàmþlë", "Éxàmþlë".encode()),
        ("ﭗﭧﭷﮇﮗ", "ﭗﭧﭷﮇﮗ".encode()),
        ("𒀇𒀗𒀧𒀷𒁇𒁗𒁧𒁷", "𒀇𒀗𒀧𒀷𒁇𒁗𒁧𒁷".encode()),
    ],
)
def test_binarybase_process(value1, value2):
    bb = database._BinaryBase(255)
    assert bb.process_bind_param(value1, DIALECT) == value2
    assert bb.process_result_value(value2, DIALECT) == value1


@pytest.mark.parametrize(
    "value1,value2",
    [
        (None, None),
        (Timestamp(2023, 1, 2, 3, 4, 5), b"20230102030405"),
    ],
)
def test_timestamp_process(value1, value2):
    ts = database._Timestamp(14)
    assert ts.process_bind_param(value1, DIALECT) == value2
    assert ts.process_result_value(value2, DIALECT) == value1


@pytest.mark.parametrize(
    "value1,value2",
    [
        (None, None),
        (UUID, str(UUID).encode()),
        ("123456789", b"123456789"),
    ],
)
def test_uuid_process(value1, value2):
    uuid_ = database._Uuid(36)
    assert uuid_.process_bind_param(value1, DIALECT) == value2
    assert uuid_.process_result_value(value2, DIALECT) == value1
