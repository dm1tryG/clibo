"""Tests for the 🤒 symptom tool."""

from __future__ import annotations


def test_log_basic_symptom(cli):
    data = cli.json("symptom", "log", "back pain", "-i", "7")
    assert data["name"] == "back pain"
    assert data["intensity"] == 7
    assert data["intensity_label"] == "severe"


def test_log_with_all_fields(cli):
    data = cli.json(
        "symptom", "log", "migraine",
        "-i", "9", "-l", "frontal", "-t", "120",
        "--triggers", "poor sleep,bright light",
        "-r", "ibuprofen,dark room",
    )
    assert data["location"] == "frontal"
    assert data["duration_min"] == 120
    assert "poor sleep" in data["triggers"]
    assert "ibuprofen" in data["relief"]


def test_add_alias_works(cli):
    data = cli.json("symptom", "add", "headache", "-i", "4")
    assert data["intensity"] == 4
    assert data["intensity_label"] == "moderate"


def test_intensity_labels_match_medical_scale(cli):
    """Standard 1-10 pain scale buckets."""
    cases = [
        (1, "mild"), (3, "mild"),
        (4, "moderate"), (6, "moderate"),
        (7, "severe"), (9, "severe"),
        (10, "worst possible"),
    ]
    for n, expected in cases:
        d = cli.json("symptom", "log", f"test-{n}", "-i", str(n))
        assert d["intensity_label"] == expected, f"intensity {n} → {expected}"


def test_intensity_out_of_range_fails(cli):
    assert cli.run("symptom", "log", "x", "-i", "0").exit_code != 0
    assert cli.run("symptom", "log", "x", "-i", "11").exit_code != 0
    assert cli.run("symptom", "log", "x", "-i", "-1").exit_code != 0


def test_negative_duration_fails(cli):
    result = cli.run("symptom", "log", "back pain", "-i", "5", "-t", "-1")
    assert result.exit_code != 0


def test_today_shows_only_todays_entries(cli):
    cli.run("symptom", "log", "back pain", "-i", "7")
    cli.run("symptom", "log", "old pain", "-i", "5", "-d", "yesterday")
    today = cli.json("symptom", "today")
    names = [e["name"] for e in today["entries"]]
    assert "back pain" in names
    assert "old pain" not in names
    assert today["worst"] == 7


def test_today_empty(cli):
    today = cli.json("symptom", "today")
    assert today["entries"] == []
    assert today["worst"] == 0


def test_list_filters_by_name(cli):
    cli.run("symptom", "log", "back pain", "-i", "7")
    cli.run("symptom", "log", "migraine", "-i", "9")
    back = cli.json("symptom", "list", "-N", "back")
    assert len(back) == 1
    assert back[0]["name"] == "back pain"


def test_list_filters_by_days(cli):
    cli.run("symptom", "log", "old", "-i", "5", "-d", "20 days ago")
    cli.run("symptom", "log", "fresh", "-i", "5")
    week = cli.json("symptom", "list", "--days", "7")
    names = [e["name"] for e in week]
    assert "fresh" in names
    assert "old" not in names


def test_show_by_name(cli):
    cli.run("symptom", "log", "back pain", "-i", "5")
    data = cli.json("symptom", "show", "back")
    assert data["name"] == "back pain"
    assert data["intensity"] == 5


def test_show_by_name_picks_most_recent(cli):
    """One condition flares multiple times — show picks the latest."""
    cli.run("symptom", "log", "migraine", "-i", "6")
    latest = cli.json("symptom", "log", "migraine", "-i", "9")
    data = cli.json("symptom", "show", "migraine")
    assert data["id"] == latest["id"]
    assert data["intensity"] == 9


def test_edit_by_name(cli):
    cli.run("symptom", "log", "back pain", "-i", "5")
    edited = cli.json("symptom", "edit", "back", "-i", "3", "-r", "rest")
    assert edited["intensity"] == 3
    assert edited["intensity_label"] == "mild"
    assert edited["relief"] == "rest"


def test_edit_rejects_bad_intensity(cli):
    cli.run("symptom", "log", "test", "-i", "5")
    assert cli.run("symptom", "edit", "test", "-i", "0").exit_code != 0
    assert cli.run("symptom", "edit", "test", "-i", "11").exit_code != 0


def test_rm_by_name(cli):
    cli.run("symptom", "log", "doomed", "-i", "5")
    cli.json("symptom", "rm", "doomed")
    listing = cli.json("symptom", "list")
    assert not any(e["name"] == "doomed" for e in listing)


def test_unknown_name_fails(cli):
    result = cli.run("symptom", "show", "ghost")
    assert result.exit_code != 0


def test_history_aggregates_by_day(cli):
    cli.run("symptom", "log", "back pain", "-i", "5", "-d", "2 days ago")
    cli.run("symptom", "log", "back pain", "-i", "6", "-d", "yesterday")
    cli.run("symptom", "log", "back pain", "-i", "7")
    cli.run("symptom", "log", "back pain", "-i", "3")  # also today
    hist = cli.json("symptom", "history", "back")
    by_day = {r["entry_date"]: r for r in hist}
    today = max(by_day)
    assert by_day[today]["episodes"] == 2  # two today
    assert by_day[today]["max_intensity"] == 7
    assert by_day[today]["avg_intensity"] == 5.0


def test_history_unknown_fails(cli):
    cli.run("symptom", "log", "back pain", "-i", "5")
    result = cli.run("symptom", "history", "ghost")
    assert result.exit_code != 0


def test_stats_top_symptoms(cli):
    cli.run("symptom", "log", "back pain", "-i", "7")
    cli.run("symptom", "log", "back pain", "-i", "6", "-d", "yesterday")
    cli.run("symptom", "log", "back pain", "-i", "5", "-d", "2 days ago")
    cli.run("symptom", "log", "migraine", "-i", "9")
    stats = cli.json("symptom", "stats")
    assert stats["total_episodes"] == 4
    assert stats["days_affected"] == 3
    assert stats["top_symptoms"][0]["name"] == "back pain"
    assert stats["top_symptoms"][0]["episodes"] == 3
    assert stats["worst_episode"]["name"] == "migraine"
    assert stats["worst_episode"]["intensity"] == 9


def test_stats_empty(cli):
    stats = cli.json("symptom", "stats")
    assert stats["total_episodes"] == 0
    assert stats["top_symptoms"] == []
    assert stats["worst_episode"] is None



# ── bare-command default (iter 106) ──


def test_bare_symptom_runs_today(cli):
    """`clibo symptom` (no subcommand) runs `today`."""
    result = cli.run("symptom")
    assert result.exit_code == 0


def test_symptom_help_still_works(cli):
    """`clibo symptom --help` still shows the menu after the bare change."""
    result = cli.run("symptom", "--help")
    assert result.exit_code == 0
    assert "today" in result.stdout
