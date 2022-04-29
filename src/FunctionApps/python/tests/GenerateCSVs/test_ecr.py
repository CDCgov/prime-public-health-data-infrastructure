import json
import pathlib
from GenerateCSVs.ecr import ecr_to_csv
import pytest


@pytest.fixture()
def bundle():
    return json.load(open(pathlib.Path(__file__).parent / "assets" / "ecr.json"))


def test_ecr_to_csv(bundle):
    generated_rows = ecr_to_csv(bundle)
    assert generated_rows == [
        [
            "",
            "Jane",
            "Doe",
            "2001-01-01",
            "female",
            "123 Fake Blvd",
            "NARROWS",
            "VA",
            "24000",
            "",
            "",
            "2106-3",
            "2186-5",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "72166-2",
            "Never smoked tobacco",
            "2015-04-14",
        ],
        [
            "",
            "Jane",
            "Doe",
            "2001-01-01",
            "female",
            "123 Fake Blvd",
            "NARROWS",
            "VA",
            "24000",
            "",
            "",
            "2106-3",
            "2186-5",
            "",
            "",
            "",
            "",
            "115",
            "Tdap",
            "2013-08-16",
            "",
            "",
            "",
        ],
    ]