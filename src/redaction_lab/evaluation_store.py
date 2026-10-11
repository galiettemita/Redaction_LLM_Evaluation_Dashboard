"""Trusted, append-only Task-6 evidence repository on the Task-4 database."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
import json
from os import PathLike
from pathlib import Path
import sqlite3

from redaction_lab.contracts import (
    EvaluationRecord,
    ReferenceMapping,
    SummaryExclusion,
    SummaryExclusionReason,
    SummaryRequest,
    SummaryRequestedMember,
    SummarySnapshot,
)
from redaction_lab.evaluator import (
    build_source_fact_record,
    evaluate_attempt,
    verify_evaluation_bindings,
)
from redaction_lab.judges.base import FactJudge, SourceFact, SourceFactRecord
from redaction_lab.store import RunStore
from redaction_lab.summary import build_authoritative_summary, verify_summary_identity


class EvaluationStore:
    """Internal trusted-caller repository; project IDs are namespace selectors."""

    def __init__(self, path: str | PathLike[str]) -> None:
        self.path = Path(path)
        self.run_store = RunStore(self.path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS source_fact_records (
                    source_fact_record_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    mapping_id TEXT NOT NULL,
                    mapping_version TEXT NOT NULL,
                    rubric_version TEXT NOT NULL,
                    validation_state TEXT NOT NULL
                        CHECK (validation_state = 'UNVALIDATED_SYNTHETIC'),
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS evaluations (
                    evaluation_id TEXT PRIMARY KEY,
                    evaluation_series_key TEXT NOT NULL UNIQUE,
                    project_id TEXT NOT NULL,
                    attempt_id TEXT NOT NULL REFERENCES attempts(attempt_id),
                    job_id TEXT NOT NULL REFERENCES jobs(job_id),
                    source_id TEXT NOT NULL REFERENCES canonical_sources(source_id),
                    source_fact_record_id TEXT
                        REFERENCES source_fact_records(source_fact_record_id),
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS summaries (
                    summary_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS summary_members (
                    summary_id TEXT NOT NULL REFERENCES summaries(summary_id),
                    ordinal INTEGER NOT NULL,
                    subject_id TEXT NOT NULL REFERENCES attempts(attempt_id),
                    evaluation_id TEXT REFERENCES evaluations(evaluation_id),
                    disposition TEXT NOT NULL,
                    exclusion_reason TEXT,
                    PRIMARY KEY (summary_id, ordinal),
                    UNIQUE (summary_id, subject_id)
                );

                CREATE TRIGGER IF NOT EXISTS source_fact_records_no_update
                BEFORE UPDATE ON source_fact_records
                BEGIN SELECT RAISE(ABORT, 'source fact records are immutable'); END;
                CREATE TRIGGER IF NOT EXISTS source_fact_records_no_delete
                BEFORE DELETE ON source_fact_records
                BEGIN SELECT RAISE(ABORT, 'source fact records are immutable'); END;
                CREATE TRIGGER IF NOT EXISTS evaluations_no_update BEFORE UPDATE ON evaluations
                BEGIN SELECT RAISE(ABORT, 'evaluations are immutable'); END;
                CREATE TRIGGER IF NOT EXISTS evaluations_no_delete BEFORE DELETE ON evaluations
                BEGIN SELECT RAISE(ABORT, 'evaluations are immutable'); END;
                CREATE TRIGGER IF NOT EXISTS summaries_no_update BEFORE UPDATE ON summaries
                BEGIN SELECT RAISE(ABORT, 'summaries are immutable'); END;
                CREATE TRIGGER IF NOT EXISTS summaries_no_delete BEFORE DELETE ON summaries
                BEGIN SELECT RAISE(ABORT, 'summaries are immutable'); END;
                CREATE TRIGGER IF NOT EXISTS summary_members_no_update BEFORE UPDATE ON summary_members
                BEGIN SELECT RAISE(ABORT, 'summary membership is immutable'); END;
                CREATE TRIGGER IF NOT EXISTS summary_members_no_delete BEFORE DELETE ON summary_members
                BEGIN SELECT RAISE(ABORT, 'summary membership is immutable'); END;
                """
            )

    @staticmethod
    def _source_fact_identity(record: SourceFactRecord) -> str:
        payload = record.model_dump(
            mode="json", exclude={"source_fact_record_id"}
        )
        encoded = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        return f"source-facts-{sha256(encoded).hexdigest()}"

    def _get_source_fact_record(
        self, source_fact_record_id: str, *, project_id: str
    ) -> SourceFactRecord:
        with self._connect() as connection:
            row = connection.execute(
                """SELECT * FROM source_fact_records
                   WHERE source_fact_record_id = ?""",
                (source_fact_record_id,),
            ).fetchone()
        if row is None:
            raise KeyError(source_fact_record_id)
        if row["project_id"] != project_id:
            raise ValueError("source fact record project identity mismatch")
        record = SourceFactRecord.model_validate_json(row["payload_json"])
        if (
            record.source_fact_record_id != row["source_fact_record_id"]
            or record.project_id != row["project_id"]
            or record.mapping_id != row["mapping_id"]
            or record.mapping_version != row["mapping_version"]
            or record.rubric_version != row["rubric_version"]
            or record.validation_state.value != row["validation_state"]
            or self._source_fact_identity(record) != record.source_fact_record_id
        ):
            raise ValueError("stored source fact record integrity mismatch")
        return record

    def record_source_facts(
        self,
        mapping: ReferenceMapping,
        *,
        facts: tuple[SourceFact, ...],
        rubric_version: str,
        source_fact_record_version: str,
    ) -> SourceFactRecord:
        record = build_source_fact_record(
            mapping,
            facts=facts,
            rubric_version=rubric_version,
            source_fact_record_version=source_fact_record_version,
        )
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """INSERT OR IGNORE INTO source_fact_records (
                    source_fact_record_id, project_id, mapping_id, mapping_version,
                    rubric_version, validation_state, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.source_fact_record_id,
                    record.project_id,
                    record.mapping_id,
                    record.mapping_version,
                    record.rubric_version,
                    record.validation_state.value,
                    record.model_dump_json(),
                ),
            )
            row = connection.execute(
                """SELECT payload_json FROM source_fact_records
                   WHERE source_fact_record_id = ?""",
                (record.source_fact_record_id,),
            ).fetchone()
            if row is None or SourceFactRecord.model_validate_json(row[0]) != record:
                raise ValueError("source fact identity already has different content")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return record

    def evaluate_and_store(
        self,
        *,
        project_id: str,
        attempt_id: str,
        mapping: ReferenceMapping,
        redacted_pdf: bytes,
        reference_pdf: bytes | None,
        source_fact_record_id: str | None,
        judge: FactJudge,
        evaluator_version: str,
        rubric_version: str,
    ) -> EvaluationRecord:
        resolved = self.run_store.resolve_attempt(attempt_id, project_id=project_id)
        if sha256(redacted_pdf).hexdigest() != resolved.source.source_sha256:
            raise ValueError("redacted PDF does not match trusted Task-4 source")
        source_fact_record = (
            self._get_source_fact_record(
                source_fact_record_id, project_id=project_id
            )
            if source_fact_record_id is not None
            else None
        )
        candidate = evaluate_attempt(
            resolved,
            mapping,
            redacted_pdf=redacted_pdf,
            reference_pdf=reference_pdf,
            source_fact_record=source_fact_record,
            judge=judge,
            evaluator_version=evaluator_version,
            rubric_version=rubric_version,
            created_at=datetime.now(UTC),
        )
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                """SELECT payload_json FROM evaluations
                   WHERE evaluation_series_key = ?""",
                (candidate.evaluation_series_key,),
            ).fetchone()
            if existing is not None:
                stored = EvaluationRecord.model_validate_json(existing[0])
                if stored.evaluation_id != candidate.evaluation_id:
                    raise ValueError(
                        "evaluation series already has different immutable evidence"
                    )
                connection.commit()
                return self.get_evaluation(
                    stored.evaluation_id, project_id=project_id
                )
            connection.execute(
                """INSERT INTO evaluations (
                    evaluation_id, evaluation_series_key, project_id, attempt_id,
                    job_id, source_id, source_fact_record_id, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    candidate.evaluation_id,
                    candidate.evaluation_series_key,
                    candidate.project_id,
                    candidate.attempt_id,
                    candidate.job_id,
                    candidate.source_id,
                    candidate.source_fact_record_id,
                    candidate.model_dump_json(),
                    candidate.created_at.isoformat(),
                ),
            )
            connection.commit()
            return candidate
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get_evaluation(
        self, evaluation_id: str, *, project_id: str
    ) -> EvaluationRecord:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM evaluations WHERE evaluation_id = ?",
                (evaluation_id,),
            ).fetchone()
        if row is None:
            raise KeyError(evaluation_id)
        if row["project_id"] != project_id:
            raise ValueError("evaluation project identity mismatch")
        record = EvaluationRecord.model_validate_json(row["payload_json"])
        if (
            record.evaluation_id != row["evaluation_id"]
            or record.evaluation_series_key != row["evaluation_series_key"]
            or record.attempt_id != row["attempt_id"]
            or record.job_id != row["job_id"]
            or record.source_id != row["source_id"]
            or record.source_fact_record_id != row["source_fact_record_id"]
        ):
            raise ValueError("stored evaluation row integrity mismatch")
        resolved = self.run_store.resolve_attempt(
            record.attempt_id, project_id=project_id
        )
        verify_evaluation_bindings(record, resolved)
        if record.source_fact_record_id is not None:
            self._get_source_fact_record(
                record.source_fact_record_id, project_id=project_id
            )
        return record

    def build_summary(self, request: SummaryRequest) -> SummarySnapshot:
        """Atomically persist a summary and its exact authenticated membership."""

        evaluations: list[EvaluationRecord] = []
        exclusions: list[SummaryExclusion] = []
        for member in request.members:
            self.run_store.resolve_attempt(
                member.attempt_id, project_id=request.project_id
            )
            if member.evaluation_id is None:
                exclusions.append(
                    SummaryExclusion(
                        attempt_id=member.attempt_id,
                        reason=SummaryExclusionReason.NO_EVALUATION,
                    )
                )
                continue
            evaluation = self.get_evaluation(
                member.evaluation_id, project_id=request.project_id
            )
            if evaluation.attempt_id != member.attempt_id:
                raise ValueError("summary evaluation does not match requested attempt")
            evaluations.append(evaluation)
        snapshot = build_authoritative_summary(
            request,
            tuple(evaluations),
            tuple(exclusions),
            generated_at=datetime.now(UTC),
        )
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT payload_json FROM summaries WHERE summary_id = ?",
                (snapshot.summary_id,),
            ).fetchone()
            if existing is not None:
                stored = SummarySnapshot.model_validate_json(existing[0])
                if stored != snapshot.model_copy(update={"generated_at": stored.generated_at}):
                    raise ValueError("summary identity already has different content")
                connection.commit()
                return self.get_summary(
                    stored.summary_id, project_id=request.project_id
                )
            connection.execute(
                """INSERT INTO summaries (
                    summary_id, project_id, payload_json, created_at
                ) VALUES (?, ?, ?, ?)""",
                (
                    snapshot.summary_id,
                    snapshot.project_id,
                    snapshot.model_dump_json(),
                    snapshot.generated_at.isoformat(),
                ),
            )
            members_by_attempt = {
                item.attempt_id: item for item in request.members
            }
            exclusions_by_attempt = {
                item.attempt_id: item for item in exclusions
            }
            for ordinal, attempt_id in enumerate(snapshot.requested_attempt_ids):
                member = members_by_attempt[attempt_id]
                exclusion = exclusions_by_attempt.get(attempt_id)
                connection.execute(
                    """INSERT INTO summary_members (
                        summary_id, ordinal, subject_id, evaluation_id,
                        disposition, exclusion_reason
                    ) VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        snapshot.summary_id,
                        ordinal,
                        attempt_id,
                        member.evaluation_id,
                        "EXCLUDED" if exclusion else "INCLUDED",
                        exclusion.reason.value if exclusion else None,
                    ),
                )
            connection.commit()
            return snapshot
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get_summary(
        self,
        summary_id: str,
        *,
        project_id: str,
        expected_compatibility_profile_id: str | None = None,
    ) -> SummarySnapshot:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM summaries WHERE summary_id = ?", (summary_id,)
            ).fetchone()
            member_rows = connection.execute(
                """SELECT * FROM summary_members WHERE summary_id = ?
                   ORDER BY ordinal""",
                (summary_id,),
            ).fetchall()
        if row is None:
            raise KeyError(summary_id)
        if row["project_id"] != project_id:
            raise ValueError("summary project identity mismatch")
        stored = SummarySnapshot.model_validate_json(row["payload_json"])
        if stored.summary_id != row["summary_id"] or stored.project_id != project_id:
            raise ValueError("stored summary row integrity mismatch")
        if len(member_rows) != stored.requested_count:
            raise ValueError("stored summary membership count mismatch")
        members: list[SummaryRequestedMember] = []
        for ordinal, member_row in enumerate(member_rows):
            if member_row["ordinal"] != ordinal:
                raise ValueError("stored summary membership ordinal mismatch")
            self.run_store.resolve_attempt(
                member_row["subject_id"], project_id=project_id
            )
            disposition = member_row["disposition"]
            evaluation_id = member_row["evaluation_id"]
            if disposition == "INCLUDED":
                if evaluation_id is None:
                    raise ValueError("included summary member lacks evaluation")
                evaluation = self.get_evaluation(
                    evaluation_id, project_id=project_id
                )
                if evaluation.attempt_id != member_row["subject_id"]:
                    raise ValueError("stored summary membership binding mismatch")
            elif (
                disposition != "EXCLUDED"
                or evaluation_id is not None
                or member_row["exclusion_reason"]
                != SummaryExclusionReason.NO_EVALUATION.value
            ):
                raise ValueError("stored summary exclusion integrity mismatch")
            members.append(
                SummaryRequestedMember(
                    attempt_id=member_row["subject_id"],
                    evaluation_id=evaluation_id,
                )
            )
        request = SummaryRequest(
            project_id=project_id,
            summary_level=stored.summary_level,
            scope_id=stored.scope_id,
            scope_version=stored.scope_version,
            members=tuple(members),
            aggregation_version=stored.aggregation_version,
        )
        rebuilt = build_authoritative_summary(
            request,
            tuple(
                self.get_evaluation(member.evaluation_id, project_id=project_id)
                for member in members
                if member.evaluation_id is not None
            ),
            tuple(
                SummaryExclusion(
                    attempt_id=member.attempt_id,
                    reason=SummaryExclusionReason.NO_EVALUATION,
                )
                for member in members
                if member.evaluation_id is None
            ),
            generated_at=stored.generated_at,
        )
        if rebuilt != stored:
            raise ValueError("stored summary evidence does not recompute")
        verify_summary_identity(stored)
        if (
            expected_compatibility_profile_id is not None
            and stored.compatibility_profile_id
            != expected_compatibility_profile_id
        ):
            raise ValueError("summary is stale for expected compatibility profile")
        return stored
