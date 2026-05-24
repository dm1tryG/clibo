"""Tests for ``clibo stale`` — cross-tool neglected-item aggregator."""

from __future__ import annotations

from datetime import date


def test_stale_empty_state(cli):
    data = cli.json("stale")
    assert data["total"] == 0
    assert data["items"] == []
    assert data["by_source"] == {}
    assert data["days"] == 30


def test_stale_picks_dormant_contacts(cli):
    cli.run("crm", "add", "Old Friend", "-c", "Acme")
    cli.run("crm", "touch", "Old Friend", "-d", "60 days ago")
    data = cli.json("stale")
    crm_rows = data["by_source"]["crm"]
    assert len(crm_rows) == 1
    assert crm_rows[0]["title"] == "Old Friend"
    assert crm_rows[0]["detail"] == "Acme"
    assert crm_rows[0]["days_since"] >= 59


def test_stale_picks_stale_ideas(cli, tmp_path):
    cli.run("ideas", "add", "Stale idea", "-s", "raw")
    import sqlite3
    from datetime import datetime, timedelta
    when = (datetime.now() - timedelta(days=60)).isoformat(" ", "seconds")
    con = sqlite3.connect(f"{tmp_path}/clibo.db")
    con.execute("UPDATE ideas_idea SET updated_at=? WHERE title='Stale idea'", (when,))
    con.commit()
    con.close()
    data = cli.json("stale")
    idea_rows = data["by_source"]["ideas"]
    assert idea_rows[0]["title"] == "Stale idea"
    assert idea_rows[0]["detail"] == "raw"


def test_stale_picks_stale_reading_books(cli):
    cli.run("books", "add", "Old read", "-p", "300", "-s", "reading")
    cli.run("books", "read", "Old read", "10", "-d", "60 days ago")
    data = cli.json("stale")
    book_rows = data["by_source"]["books"]
    assert book_rows[0]["title"] == "Old read"
    assert book_rows[0]["days_since"] >= 59


def test_stale_excludes_recent_activity(cli):
    """Anything touched within the threshold is excluded."""
    cli.run("crm", "add", "Fresh contact")
    cli.run("crm", "touch", "Fresh contact")
    cli.run("ideas", "add", "Fresh idea")
    cli.run("books", "add", "Fresh book", "-p", "200", "-s", "reading")
    cli.run("books", "read", "Fresh book", "20")
    data = cli.json("stale")
    assert data["total"] == 0


def test_stale_sorts_most_stale_first(cli, tmp_path):
    """Across sources, the longest-untouched item appears first."""
    # Make a book stale by 60d, an idea by 90d.
    cli.run("books", "add", "60d book", "-p", "300", "-s", "reading")
    cli.run("books", "read", "60d book", "10", "-d", "60 days ago")
    cli.run("ideas", "add", "90d idea")
    import sqlite3
    from datetime import datetime, timedelta
    when = (datetime.now() - timedelta(days=90)).isoformat(" ", "seconds")
    con = sqlite3.connect(f"{tmp_path}/clibo.db")
    con.execute("UPDATE ideas_idea SET updated_at=? WHERE title='90d idea'", (when,))
    con.commit()
    con.close()
    data = cli.json("stale")
    # The 90d idea should be first in the flat sorted list.
    assert data["items"][0]["title"] == "90d idea"
    assert data["items"][1]["title"] == "60d book"


def test_stale_threshold_filters(cli):
    """`--days 7` is a tighter threshold; `--days 200` looser."""
    cli.run("crm", "add", "Friend")
    cli.run("crm", "touch", "Friend", "-d", "60 days ago")
    # 7d threshold → caught
    tight = cli.json("stale", "--days", "7")
    assert tight["total"] == 1
    # 200d threshold → too loose for a 60d-stale contact
    loose = cli.json("stale", "--days", "200")
    assert loose["total"] == 0


def test_stale_excludes_non_active_contacts(cli):
    """Non-active CRM contacts (lead/customer/cold) don't appear."""
    cli.run("crm", "add", "Cold one")
    cli.run("crm", "edit", "Cold one", "--status", "cold")
    cli.run("crm", "touch", "Cold one", "-d", "60 days ago")
    data = cli.json("stale")
    assert "crm" not in data["by_source"]


def test_stale_excludes_shipped_ideas(cli, tmp_path):
    """Shipped / abandoned ideas aren't 'open' — they aren't stale."""
    cli.run("ideas", "add", "Shipped", "-s", "shipped")
    import sqlite3
    from datetime import datetime, timedelta
    when = (datetime.now() - timedelta(days=60)).isoformat(" ", "seconds")
    con = sqlite3.connect(f"{tmp_path}/clibo.db")
    con.execute("UPDATE ideas_idea SET updated_at=? WHERE title='Shipped'", (when,))
    con.commit()
    con.close()
    data = cli.json("stale")
    assert "ideas" not in data["by_source"]


def test_stale_excludes_finished_books(cli):
    """Finished books are off the list — only `reading` status counts."""
    cli.run("books", "add", "Done", "-p", "100", "-s", "finished")
    data = cli.json("stale")
    assert "books" not in data["by_source"]


def test_stale_negative_days_fails(cli):
    result = cli.run("stale", "--days", "-1")
    assert result.exit_code != 0


def test_stale_human_view_runs(cli):
    """Smoke: empty and populated render cleanly."""
    empty = cli.run("stale")
    assert empty.exit_code == 0
    assert "Nothing's gone stale" in empty.output

    cli.run("crm", "add", "Friend")
    cli.run("crm", "touch", "Friend", "-d", "60 days ago")
    populated = cli.run("stale")
    assert populated.exit_code == 0
    assert "Friend" in populated.output
    assert "Stale" in populated.output


def test_stale_asof_is_today(cli):
    data = cli.json("stale")
    assert data["asof"] == date.today().isoformat()
