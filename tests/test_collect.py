from collector.collect import (
    STATUS_MAX_LEN,
    build_record,
    extract_status,
    filter_candidates,
    merge_record,
)


# --- extract_status -------------------------------------------------------

def test_extract_status_from_bold_line_joins_wrapped_paragraph():
    readme = (
        "# Bloodborne\n\n"
        "**Status: experimental, playable.** The game boots, loads saves\n"
        "and plays.\n\n"
        "## Install\n"
    )

    assert extract_status(readme) == "experimental, playable. The game boots, loads saves and plays."


def test_extract_status_from_bold_line_with_qualifier():
    readme = "**Status on Windows: playable.** Menus, Adventure and Arcade.\n"

    assert extract_status(readme) == "playable. Menus, Adventure and Arcade."


def test_extract_status_from_heading_takes_next_paragraph():
    readme = (
        "# UFC 3\n\n## Status\n\n"
        "**Playable.** Menus, loading, fights,\nsound and controller.\n\n"
        "## Build\n"
    )

    assert extract_status(readme) == "Playable. Menus, loading, fights, sound and controller."


def test_extract_status_uses_first_occurrence():
    readme = "**Status: alpha.** First.\n\n## Status\n\nSecond.\n"

    assert extract_status(readme) == "alpha. First."


def test_extract_status_strips_markdown_links_code_and_html():
    readme = "## Status\n\nSee [the notes](docs/x.md) and `ISS_FLAG` <b>now</b>.\n"

    assert extract_status(readme) == "See the notes and ISS_FLAG now."


def test_extract_status_returns_none_without_section():
    assert extract_status("# Title\n\nJust a description.\n") is None


def test_extract_status_returns_none_for_empty_readme():
    assert extract_status(None) is None
    assert extract_status("") is None


def test_extract_status_returns_none_when_heading_has_no_paragraph():
    assert extract_status("## Status\n\n## Next\n\ntext\n") is None


def test_extract_status_truncates_long_text_at_word_boundary():
    readme = "## Status\n\n" + ("word " * 200) + "\n"

    status = extract_status(readme)

    assert len(status) <= STATUS_MAX_LEN
    assert status.endswith("…")
    assert not status[:-1].endswith(" ")


# --- build_record ---------------------------------------------------------

REPO_JSON = {
    "full_name": "Supermedo/bloodborne_pc",
    "html_url": "https://github.com/Supermedo/bloodborne_pc",
    "stargazers_count": 3670,
    "pushed_at": "2026-10-18T11:00:14Z",
    "archived": False,
    "fork": False,
}


def test_build_record_maps_repo_and_latest_release():
    releases = [{"tag_name": "windows-v1.9.1", "published_at": "2026-10-17T10:00:00Z", "prerelease": False}]

    record = build_record("Supermedo/bloodborne_pc", REPO_JSON, releases, "**Status: playable.** Ok.\n")

    assert record == {
        "stars": 3670,
        "pushed_at": "2026-10-18T11:00:14Z",
        "archived": False,
        "fork": False,
        "missing": False,
        "renamed_to": None,
        "release_tag": "windows-v1.9.1",
        "release_date": "2026-10-17",
        "status_text": "playable. Ok.",
    }


def test_build_record_without_releases():
    record = build_record("Supermedo/bloodborne_pc", REPO_JSON, [], None)

    assert record["release_tag"] is None
    assert record["release_date"] is None
    assert record["status_text"] is None


def test_build_record_detects_rename_case_insensitively():
    renamed = {**REPO_JSON, "full_name": "bc160201983/medievil_2019_pc_port"}

    assert build_record("bc160201983/MediEvil-PC", renamed, [], None)["renamed_to"] == "bc160201983/medievil_2019_pc_port"
    assert build_record("SUPERMEDO/Bloodborne_PC", REPO_JSON, [], None)["renamed_to"] is None


def test_build_record_flags_archived_and_fork():
    record = build_record("a/b", {**REPO_JSON, "full_name": "a/b", "archived": True, "fork": True}, [], None)

    assert record["archived"] is True
    assert record["fork"] is True


# --- merge_record ---------------------------------------------------------

def _rec(**over):
    base = build_record("Supermedo/bloodborne_pc", REPO_JSON, [], None)
    return {**base, **over}


def test_merge_record_first_time_has_no_status_change():
    merged = merge_record(None, _rec(status_text="alpha"), "2026-10-18")

    assert merged["status_changed_at"] is None


def test_merge_record_marks_status_change_date():
    prev = {**_rec(status_text="alpha"), "status_changed_at": None}

    merged = merge_record(prev, _rec(status_text="playable"), "2026-10-19")

    assert merged["status_changed_at"] == "2026-10-19"


def test_merge_record_keeps_previous_change_date_when_unchanged():
    prev = {**_rec(status_text="alpha"), "status_changed_at": "2026-10-10"}

    merged = merge_record(prev, _rec(status_text="alpha"), "2026-10-19")

    assert merged["status_changed_at"] == "2026-10-10"


def test_merge_record_does_not_mutate_inputs():
    prev = {**_rec(status_text="alpha"), "status_changed_at": None}
    new = _rec(status_text="beta")

    merge_record(prev, new, "2026-10-19")

    assert prev["status_changed_at"] is None
    assert "status_changed_at" not in new


def test_merge_record_missing_repo_keeps_previous_data():
    prev = {**_rec(stars=10), "status_changed_at": None}

    merged = merge_record(prev, None, "2026-10-19")

    assert merged["missing"] is True
    assert merged["stars"] == 10


def test_merge_record_missing_repo_without_history():
    merged = merge_record(None, None, "2026-10-19")

    assert merged["missing"] is True
    assert merged["stars"] is None


# --- filter_candidates ----------------------------------------------------

def _item(name, fork=False, stars=5):
    return {
        "full_name": name,
        "html_url": f"https://github.com/{name}",
        "description": f"desc {name}",
        "stargazers_count": stars,
        "pushed_at": "2026-10-18T00:00:00Z",
        "fork": fork,
    }


def test_filter_candidates_excludes_known_dismissed_and_forks():
    items = [_item("a/known"), _item("b/dismissed"), _item("c/fork", fork=True), _item("d/new")]

    result = filter_candidates(items, known={"A/Known"}, dismissed={"b/dismissed"}, previous={}, today="2026-10-18")

    assert list(result) == ["d/new"]
    assert result["d/new"]["found_at"] == "2026-10-18"
    assert result["d/new"]["description"] == "desc d/new"


def test_filter_candidates_deduplicates_and_keeps_first_found_date():
    previous = {"d/new": {"found_at": "2026-10-01"}}

    result = filter_candidates([_item("d/new"), _item("D/New")], set(), set(), previous, "2026-10-18")

    assert list(result) == ["d/new"]
    assert result["d/new"]["found_at"] == "2026-10-01"


def test_filter_candidates_keeps_previous_candidates_not_in_todays_search():
    previous = {"e/old": {"repo": "e/old", "found_at": "2026-10-01"}}

    result = filter_candidates([], set(), set(), previous, "2026-10-18")

    assert "e/old" in result


def test_filter_candidates_drops_previous_candidates_now_dismissed_or_known():
    previous = {"e/old": {"repo": "e/old", "found_at": "2026-10-01"}, "f/acc": {"repo": "f/acc", "found_at": "2026-10-01"}}

    result = filter_candidates([], known={"f/acc"}, dismissed={"e/old"}, previous=previous, today="2026-10-18")

    assert result == {}
