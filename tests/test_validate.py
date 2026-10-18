import json
from pathlib import Path

from collector.validate import validate_follows, validate_ports, validate_review

DATA = Path(__file__).resolve().parent.parent / "data"


def _port(**over):
    base = {"id": "bloodborne", "game": "Bloodborne", "repo": "Supermedo/bloodborne_pc",
            "os": "Windows", "status": "play", "reach": "Entero", "note": ""}
    return {**base, **over}


def test_valid_ports_have_no_errors():
    assert validate_ports({"ports": [_port()]}) == []


def test_ports_requires_list():
    assert validate_ports({}) == ["ports: falta la lista 'ports'"]


def test_ports_rejects_bad_fields():
    errors = validate_ports({"ports": [_port(id="Mal Id", repo="sin-barra", status="beta", game="")]})

    assert any("id" in e for e in errors)
    assert any("repo" in e for e in errors)
    assert any("status" in e for e in errors)
    assert any("game" in e for e in errors)


def test_ports_rejects_non_string_optional_fields():
    errors = validate_ports({"ports": [_port(os=3, reach=None, note=[])]})

    assert len(errors) == 3


def test_ports_rejects_duplicate_ids():
    errors = validate_ports({"ports": [_port(), _port()]})

    assert errors == ["ports[1]: id duplicado 'bloodborne'"]


def test_ports_rejects_non_object_entries():
    assert validate_ports({"ports": ["x"]}) == ["ports[0]: debe ser un objeto"]


def test_follows_must_reference_existing_ids():
    assert validate_follows({"follows": ["bloodborne"]}, {"bloodborne"}) == []
    assert validate_follows({"follows": ["nope"]}, {"bloodborne"}) == ["follows: id desconocido 'nope'"]
    assert validate_follows({}, set()) == ["follows: falta la lista 'follows'"]


def test_review_requires_repo_names():
    assert validate_review({"dismissed": ["a/b"]}) == []
    assert validate_review({"dismissed": ["mal"]}) == ["review: repo inválido 'mal'"]
    assert validate_review({}) == ["review: falta la lista 'dismissed'"]


def test_committed_data_files_are_valid():
    ports = json.loads((DATA / "ports.json").read_text())
    follows = json.loads((DATA / "follows.json").read_text())
    review = json.loads((DATA / "review.json").read_text())

    assert validate_ports(ports) == []
    assert validate_follows(follows, {p["id"] for p in ports["ports"]}) == []
    assert validate_review(review) == []
