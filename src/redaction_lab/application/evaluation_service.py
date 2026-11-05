"""Explicit experimental evaluation commands and read-only persisted queries.

The service has no model adapter. Reference content is consumed only after a
frozen attempt exists, from isolated reference evidence for an explicit pair.
"""
from __future__ import annotations

from collections import defaultdict

from redaction_lab.application.application_store import ApplicationStore
from redaction_lab.contracts import ExperimentalSummaryCell
from redaction_lab.evaluation_store import EvaluationStore
from redaction_lab.reference import align_experimental_reference
from redaction_lab.summary import build_experimental_summary, build_experimental_model_summary

MAPPING_VERSION = 'experimental-mapping-v1'


class EvaluationService:
    def __init__(self, store: ApplicationStore):
        self.store = store
        self.evaluations = EvaluationStore(store.path)

    def evaluate_attempt(self, *, project_id: str, attempt_id: str, pair_id: str | None = None):
        """Intentional write command; never call from a GET/results path."""
        resolved = self.evaluations.run_store.resolve_attempt(attempt_id, project_id=project_id)
        mapping = None
        if pair_id is not None:
            pair = self.store.get_pair(pair_id)
            version = self.store.get_version(pair.redacted_version_id)
            if (pair.project_id != project_id or version.project_id != project_id
                    or version.source_id != resolved.source.source_id
                    or version.sha256 != resolved.source.source_sha256):
                raise ValueError('reference pair does not bind this prediction source')
            reference = self.store.reference_source(pair.reference_version_id) if pair.reference_version_id else None
            if reference is not None:
                if reference.project_id != project_id or reference.version_id != pair.reference_version_id:
                    raise ValueError('reference pair evidence binding mismatch')
                mappings = align_experimental_reference(
                    resolved.source.canonical_document, reference.canonical_text,
                    targets=resolved.source.targets,
                    reference_document_version_id=reference.version_id,
                    reference_canonical_version_id=reference.source_id,
                    mapping_version=MAPPING_VERSION,
                )
                mapping = next(m for m in mappings if m.target_id == resolved.attempt.target_id
                               and m.target_version == resolved.attempt.target_version)
        return self.evaluations.evaluate_experimental_and_store(
            project_id=project_id, attempt_id=attempt_id, mapping=mapping,
        )

    def get_evaluation(self, evaluation_id, *, project_id):
        return self.evaluations.get_evaluation(evaluation_id, project_id=project_id)

    def list_evaluations(self, *, project_id, attempt_id=None):
        return self.evaluations.list_experimental_evaluations(project_id=project_id, attempt_id=attempt_id)

    def list_summaries(self, *, project_id):
        return self.evaluations.list_experimental_summaries(project_id=project_id)

    def summarize(self, records, *, excluded_candidate_ids=()):
        """Persist target/document/model revisions for an explicit evaluation set.

        For unfinished intents or exclusion-only scopes the orchestrator can use
        ExperimentalSummaryCell/build_experimental_summary and the same store.
        """
        groups = defaultdict(list)
        for record in records:
            cell = ExperimentalSummaryCell.from_evaluation(record)
            groups[(cell.profile, cell.document_version_id)].append(cell)
        results = []
        documents_by_profile = defaultdict(list)
        if excluded_candidate_ids and len(groups) != 1:
            raise ValueError('exclusions must be bound to one document scope')
        for (profile, _), cells in groups.items():
            for cell in cells:
                target = build_experimental_summary((cell,), summary_level='TARGET')
                results.append(self.evaluations.store_experimental_summary(target))
            document = build_experimental_summary(cells, summary_level='DOCUMENT', excluded_candidate_ids=excluded_candidate_ids)
            results.append(self.evaluations.store_experimental_summary(document))
            documents_by_profile[profile].append(document)
        for documents in documents_by_profile.values():
            model = build_experimental_model_summary(documents)
            results.append(self.evaluations.store_experimental_summary(model))
        return tuple(results)
