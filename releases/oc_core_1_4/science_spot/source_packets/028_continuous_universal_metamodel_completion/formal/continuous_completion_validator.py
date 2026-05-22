"""Validate OC continuous universal metamodel completion 028."""

from __future__ import annotations

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "oc_continuous_completion_028.sqlite"
ARTICLE = ROOT / "OC_ARTICLE_INTEGRATION_LEDGER_028.md"

ALLOWED_STATUSES = {
    "PROVED_UNIVERSAL_METAMODEL_THEOREM",
    "REFUTED_OLD_FORMULATION",
    "DOMAIN_INSTANTIATION_REQUIRED",
    "REPAIRED_AND_BOUND_TO_OCU",
}

FORBIDDEN_ALLOWED_WORDING = {
    "every real-world conflict produces dimension birth or collapse",
    "lean proves oc true of the world",
    "the six operators are globally minimal and unique",
    "k0-k12 is the unique cosmic hierarchy",
    "domain projections are validated by the oc core alone",
    "crown stones are established by the core alone",
}


def fetch_one(conn: sqlite3.Connection, sql: str) -> int | str | None:
    row = conn.execute(sql).fetchone()
    return None if row is None else row[0]


def artifact_exists(ref: str) -> bool:
    for part in ref.split(";"):
        candidate = part.strip()
        if not candidate:
            continue
        if not (ROOT / candidate).resolve().exists():
            return False
    return True


def main() -> None:
    if not DB.exists():
        raise SystemExit(f"missing DB: {DB}")

    with sqlite3.connect(DB) as conn:
        total = fetch_one(conn, "select count(*) from queue_rows")
        open_total = fetch_one(conn, "select count(*) from queue_rows where status = 'OPEN'")
        bad_statuses = conn.execute(
            "select row_id, status from queue_rows"
        ).fetchall()
        bad_statuses = [
            (row_id, status)
            for row_id, status in bad_statuses
            if status not in ALLOWED_STATUSES
        ]
        missing_content = conn.execute(
            """
            select row_id from queue_rows
            where artifact_ref is null or trim(artifact_ref) = ''
               or proof_or_boundary is null or trim(proof_or_boundary) = ''
               or falsifier_check is null or trim(falsifier_check) = ''
               or dependency_closure is null or trim(dependency_closure) = ''
            """
        ).fetchall()
        artifacts = conn.execute(
            "select row_id, artifact_ref from queue_rows"
        ).fetchall()
        missing_artifacts = [
            (row_id, ref) for row_id, ref in artifacts if not artifact_exists(ref)
        ]
        control = conn.execute(
            """
            select active_row_id, open_total, closeout_allowed, handoff_is_completion
            from control where id = 1
            """
        ).fetchone()
        article_bad = conn.execute(
            """
            select row_id, allowed_wording from article_boundary
            """
        ).fetchall()

    if total != 16:
        raise SystemExit(f"expected 16 queue rows, found {total}")
    if open_total != 0:
        raise SystemExit(f"queue has open rows: {open_total}")
    if bad_statuses:
        raise SystemExit(f"bad statuses: {bad_statuses}")
    if missing_content:
        raise SystemExit(f"rows missing proof fields: {missing_content}")
    if missing_artifacts:
        raise SystemExit(f"missing artifact refs: {missing_artifacts}")
    if control != ("COMPLETE", 0, 1, 0):
        raise SystemExit(f"bad control row: {control}")

    article_text = ARTICLE.read_text(encoding="utf-8").lower()
    if "allowed article thesis" not in article_text:
        raise SystemExit("article ledger missing allowed thesis section")

    for row_id, allowed in article_bad:
        lowered = allowed.lower()
        violations = [phrase for phrase in FORBIDDEN_ALLOWED_WORDING if phrase in lowered]
        if violations:
            raise SystemExit(f"{row_id} allowed wording violation: {violations}")

    print("OC 028 continuous completion validator: PASS")
    print(f"queue_rows={total}")
    print("open_total=0")
    print("closeout_allowed=1")


if __name__ == "__main__":
    main()
