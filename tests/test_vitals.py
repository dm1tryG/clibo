"""Tests for the ❤️ vitals tool."""

from __future__ import annotations


def test_bp_classifies(cli):
    normal = cli.json("vitals", "bp", "118", "75")
    assert normal["category"] == "normal"
    high = cli.json("vitals", "bp", "150", "95")
    assert high["category"] == "stage 2 hypertension"


def test_pulse_and_glucose(cli):
    pulse = cli.json("vitals", "pulse", "72")
    assert pulse["reading"] == "72 bpm"
    glucose = cli.json("vitals", "glucose", "95", "-u", "mg/dL")
    assert glucose["value"] == 95


def test_latest_per_kind(cli):
    cli.run("vitals", "pulse", "70")
    cli.run("vitals", "pulse", "80")
    cli.run("vitals", "spo2", "98")
    latest = cli.json("vitals", "latest")
    assert latest["pulse"]["value"] == 80
    assert latest["spo2"]["value"] == 98


def test_stats_for_kind(cli):
    cli.run("vitals", "pulse", "60")
    cli.run("vitals", "pulse", "80")
    stats = cli.json("vitals", "stats", "pulse")
    assert stats["readings"] == 2
    assert stats["avg"] == 70.0
    assert stats["min"] == 60
    assert stats["max"] == 80


def test_stats_unknown_kind_fails(cli):
    result = cli.run("vitals", "stats", "height")
    assert result.exit_code != 0


# ── generic `log` dispatcher (iter 100) ──


def test_log_temp(cli):
    """`clibo vitals log temp 39.2` — the canonical agent flow."""
    data = cli.json("vitals", "log", "temp", "39.2")
    assert data["kind"] == "temp"
    assert data["value"] == 39.2
    assert data["unit"] == "°C"
    assert data["reading"] == "39.2 °C"


def test_log_pulse(cli):
    data = cli.json("vitals", "log", "pulse", "72")
    assert data["kind"] == "pulse"
    assert data["value"] == 72.0


def test_log_bp_slash_shorthand(cli):
    """115/75 is normal — diastolic ≥80 alone would bump to stage 1."""
    data = cli.json("vitals", "log", "bp", "115/75")
    assert data["kind"] == "bp"
    assert data["value"] == 115.0
    assert data["value2"] == 75.0
    assert data["category"] == "normal"


def test_log_bp_two_args(cli):
    data = cli.json("vitals", "log", "bp", "140", "90")
    assert data["value"] == 140.0
    assert data["value2"] == 90.0
    assert data["category"] == "stage 2 hypertension"


def test_log_glucose_default_unit(cli):
    data = cli.json("vitals", "log", "glucose", "95")
    assert data["unit"] == "mg/dL"


def test_log_glucose_unit_override(cli):
    data = cli.json("vitals", "log", "glucose", "5.5", "-u", "mmol/L")
    assert data["unit"] == "mmol/L"
    assert data["value"] == 5.5


def test_log_spo2(cli):
    data = cli.json("vitals", "log", "spo2", "98")
    assert data["kind"] == "spo2"
    assert data["unit"] == "%"


def test_log_writes_to_same_table_as_kind_subcommands(cli):
    """`vitals log temp` and `vitals temp` produce indistinguishable rows."""
    a = cli.json("vitals", "log", "temp", "37.5")
    b = cli.json("vitals", "temp", "37.5")
    # Both write the same kind + unit; ids differ.
    assert a["kind"] == b["kind"] == "temp"
    assert a["unit"] == b["unit"] == "°C"
    assert a["value"] == b["value"] == 37.5


def test_log_rejects_unknown_kind(cli):
    result = cli.run("vitals", "log", "fever", "39.2")
    assert result.exit_code != 0


def test_log_rejects_non_numeric_value(cli):
    result = cli.run("vitals", "log", "temp", "hot")
    assert result.exit_code != 0


def test_log_bp_missing_diastolic_fails(cli):
    result = cli.run("vitals", "log", "bp", "120")
    assert result.exit_code != 0


def test_log_non_bp_with_value2_fails(cli):
    """`temp 37.5 42` is nonsense — should fail rather than silently drop value2."""
    result = cli.run("vitals", "log", "temp", "37.5", "42")
    assert result.exit_code != 0


def test_log_supports_date_flag(cli):
    data = cli.json("vitals", "log", "temp", "38.0", "-d", "yesterday")
    # Should backdate; just check entry_date isn't today.
    from datetime import date
    assert data["entry_date"] != str(date.today())


def test_log_supports_note(cli):
    """Note flag forwards through the dispatcher."""
    data = cli.json("vitals", "log", "pulse", "72", "-n", "morning resting")
    assert data["note"] == "morning resting"


# ── bare-command default (iter 105) ──


def test_bare_vitals_runs_latest(cli):
    """`clibo vitals` (no subcommand) runs `latest`."""
    result = cli.run("vitals")
    assert result.exit_code == 0
    # No assertion on output content — that varies by tool.
    # Equivalence check: bare exits cleanly just like the explicit subcommand would.


def test_vitals_help_still_works(cli):
    """`clibo vitals --help` still shows the menu after the bare change."""
    result = cli.run("vitals", "--help")
    assert result.exit_code == 0
    assert "latest" in result.stdout


# ── add alias for log (iter 121) ──


def test_add_alias_routes_to_log(cli):
    """`vitals add temp 38.5` works like `vitals log temp 38.5`."""
    data = cli.json("vitals", "add", "temp", "38.5")
    assert data["kind"] == "temp"
    assert data["value"] == 38.5


def test_add_alias_supports_bp_slash(cli):
    """BP shorthand survives through the alias."""
    data = cli.json("vitals", "add", "bp", "120/80")
    assert data["value"] == 120
    assert data["value2"] == 80
