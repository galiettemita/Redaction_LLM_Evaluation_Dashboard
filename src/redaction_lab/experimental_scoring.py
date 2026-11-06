"""Version 1 lexical agreement; engineering evidence, never verified accuracy.

Normalization: NFKC, Unicode mathematical minus to ASCII minus, casefold,
Unicode alphanumeric tokens, punctuation removed,
whitespace collapsed. Trigrams are multisets of the joined normalized tokens
(short strings use the entire string). LCS agreement is 2L/(reference+prediction
lengths). Critical details are tagged multisets of signed numeric literals, ordered numeric date strings, English
number words/month names, explicit negation and originally capitalized tokens.
Whitespace between an ASCII/normalized sign and its number is insignificant.
No details on either side means critical agreement 1. Raw UTF-8 hashes bind the
original inputs. Limits bound memory/CPU; rejecting input is never a zero score.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import re
from typing import Annotated, Literal
import unicodedata

from pydantic import BaseModel, ConfigDict, Field

METHOD_ID = 'experimental-text-agreement-v1'
NORMALIZATION_VERSION = 'nfkc-casefold-alnum-multiset-lcs-trigram-critical-v1'
SCALE = '0–100 text agreement'
Unit = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]


class Subscores(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    normalized_exact_match: bool
    token_precision: Unit
    token_recall: Unit
    token_f1: Unit
    ordered_token_agreement: Unit
    character_trigram_f1: Unit
    critical_detail_agreement: Unit


class ExperimentalScore(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    method_id: Literal['experimental-text-agreement-v1'] = METHOD_ID
    scale: Literal['0–100 text agreement'] = SCALE
    normalization_version: Literal['nfkc-casefold-alnum-multiset-lcs-trigram-critical-v1'] = NORMALIZATION_VERSION
    experimental_score: Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]
    verified_score: None = None
    reference_hash: Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
    prediction_hash: Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
    subscores: Subscores
    warnings: tuple[str, ...]
    applied_caps: tuple[Literal[35.0, 60.0], ...]


_NUMBER_WORDS = set('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million billion trillion dozen first second third fourth fifth sixth seventh eighth ninth tenth'.split())
_MONTHS = set('january february march april may june july august september october november december jan feb mar apr jun jul aug sep sept oct nov dec'.split())
_NEGATIONS = set('no not never neither nor without cannot'.split())
_TOKEN = re.compile(r'[^\W_]+', re.UNICODE)


def _parts(value: str):
    if not isinstance(value, str) or not value.strip() or len(value) > 32768:
        raise ValueError('text must be nonempty and at most 32768 characters')
    original = unicodedata.normalize('NFKC', value).replace('’', "'").replace("−", "-")
    for match in re.finditer(r'([^\d\s])\s*(?=\d)', original):
        sign = match.group(1)
        if sign in {'±', '∓'} or (unicodedata.category(sign) == 'Pd' and sign != '-'):
            raise ValueError('ambiguous numeric sign notation')
    tokens = _TOKEN.findall(original.casefold())
    if not tokens or len(tokens) > 4096:
        raise ValueError('text must contain between 1 and 4096 tokens')
    quantity = Counter(re.sub(r'\s+', '', literal) for literal in
        re.findall(r'(?<!\w)(?:[+-]\s*)?\d+(?:[.,]\d+)*', original))
    quantity.update('date:' + date for date in re.findall(r'\b\d{1,4}[-/]\d{1,2}[-/]\d{1,4}\b', original))
    quantity.update(word for word in tokens if word in _NUMBER_WORDS | _MONTHS)
    negations = Counter(word for word in tokens if word in _NEGATIONS)
    negations.update('not' for _ in re.finditer(r"\b\w+n't\b", original.casefold()))
    entities = Counter(word.casefold() for word in _TOKEN.findall(original) if word[0].isupper())
    critical = Counter({('quantity', k): v for k, v in quantity.items()})
    critical.update({('negation', k): v for k, v in negations.items()})
    critical.update({('entity', k): v for k, v in entities.items()})
    return tokens, quantity, negations, critical


def _f1(left: Counter, right: Counter) -> float:
    denominator = left.total() + right.total()
    return 2 * (left & right).total() / denominator if denominator else 1.0


def _lcs(left: list[str], right: list[str]) -> int:
    # Bitset LCS computes exact length without a quadratic Python matrix.
    positions: dict[str, int] = {}
    for index, token in enumerate(right):
        positions[token] = positions.get(token, 0) | (1 << index)
    row = 0
    for token in left:
        matches = positions.get(token, 0) | row
        row = matches & ~(matches - ((row << 1) | 1))
    return row.bit_count()


def _trigrams(tokens: list[str]) -> Counter:
    text = ' '.join(tokens)
    return Counter(text[i:i+3] for i in range(max(1, len(text)-2)))


def score_text_agreement(reference: str, prediction: str) -> ExperimentalScore:
    ref, ref_quantity, ref_negation, ref_critical = _parts(reference)
    pred, pred_quantity, pred_negation, pred_critical = _parts(prediction)
    overlap = (Counter(ref) & Counter(pred)).total()
    exact = ref == pred and ref_quantity == pred_quantity and ref_negation == pred_negation
    subscores = Subscores(
        normalized_exact_match=exact,
        token_precision=overlap/len(pred), token_recall=overlap/len(ref),
        token_f1=2*overlap/(len(ref)+len(pred)),
        ordered_token_agreement=2*_lcs(ref, pred)/(len(ref)+len(pred)),
        character_trigram_f1=_f1(_trigrams(ref), _trigrams(pred)),
        critical_detail_agreement=1.0 if exact else _f1(ref_critical, pred_critical),
    )
    warnings = ['LEXICAL_BASELINE_PARAPHRASE_AND_ROLE_REVERSAL_LIMITATION']
    caps = []
    if not exact and ref_negation != pred_negation:
        warnings.append('NEGATION_MISMATCH')
        caps.append(35.0)
    if not exact and ref_quantity != pred_quantity:
        warnings.append('QUANTITY_OR_DATE_MISMATCH')
        caps.append(60.0)
    if subscores.token_precision < 1:
        warnings.append('UNSUPPORTED_ADDITIONS_POSSIBLE')
    raw = 100.0 if exact else 100 * (
        .4*subscores.token_f1 + .25*subscores.ordered_token_agreement
        + .2*subscores.character_trigram_f1 + .15*subscores.critical_detail_agreement
    )
    return ExperimentalScore(
        experimental_score=round(min([raw, *caps]), 1),
        reference_hash=sha256(reference.encode('utf-8')).hexdigest(),
        prediction_hash=sha256(prediction.encode('utf-8')).hexdigest(),
        subscores=subscores, warnings=tuple(warnings), applied_caps=tuple(caps),
    )
