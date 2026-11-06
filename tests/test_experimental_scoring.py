from hashlib import sha256

import pytest

from redaction_lab.experimental_scoring import score_text_agreement


def test_normalized_exact_match_is_100_with_raw_input_hashes():
    result = score_text_agreement('  Café, CREW! ', 'café crew')
    assert result.experimental_score == 100.0
    assert result.subscores.normalized_exact_match is True
    assert result.reference_hash == sha256('  Café, CREW! '.encode()).hexdigest()
    assert result.prediction_hash == sha256(b'caf\xc3\xa9 crew').hexdigest()
    assert result.method_id == 'experimental-text-agreement-v1'
    assert result.verified_score is None


@pytest.mark.parametrize('value', ['', '  ', '!!!', None, 12, 'a' * 32769])
def test_invalid_or_empty_input_is_not_zero(value):
    with pytest.raises(ValueError):
        score_text_agreement(value, 'crew')
    with pytest.raises(ValueError):
        score_text_agreement('crew', value)


def test_repetition_is_multiset_penalized_and_rounded():
    # a a vs a: token F1=LCS=2/3; trigrams {a a} vs {a}: 0;
    # no critical details => 1. 100 * (.4*2/3 + .25*2/3 + .15) = 58.333...
    result = score_text_agreement('a a', 'a')
    assert result.experimental_score == 58.3
    assert result.subscores.token_precision == 1
    assert result.subscores.token_recall == .5
    assert result.subscores.token_f1 == pytest.approx(2/3)
    assert result.subscores.ordered_token_agreement == pytest.approx(2/3)
    assert result.subscores.character_trigram_f1 == 0
    assert result.subscores.critical_detail_agreement == 1


def test_unsupported_addition_reduces_precision():
    result = score_text_agreement('a', 'a a')
    assert result.experimental_score == 58.3
    assert result.subscores.token_precision == .5
    assert 'UNSUPPORTED_ADDITIONS_POSSIBLE' in result.warnings


def test_paraphrase_is_not_mistaken_for_semantic_judgment():
    # No token/trigram overlap or critical details: only .15 critical baseline.
    result = score_text_agreement('fast', 'quick')
    assert result.experimental_score == 15.0
    assert 'LEXICAL_BASELINE_PARAPHRASE_AND_ROLE_REVERSAL_LIMITATION' in result.warnings


def test_role_reversal_preserves_bag_overlap_but_warns():
    result = score_text_agreement('alice helps bob', 'bob helps alice')
    assert result.subscores.token_f1 == 1
    assert result.subscores.ordered_token_agreement == pytest.approx(1/3)
    assert result.experimental_score < 100
    assert 'LEXICAL_BASELINE_PARAPHRASE_AND_ROLE_REVERSAL_LIMITATION' in result.warnings


@pytest.mark.parametrize('reference,prediction,cap,warning', [
    ('the crew has 12 aircraft ready today', 'the crew has 13 aircraft ready today', 60.0, 'QUANTITY_OR_DATE_MISMATCH'),
    ('the crew leaves on March 12 2026', 'the crew leaves on April 12 2026', 60.0, 'QUANTITY_OR_DATE_MISMATCH'),
    ('the crew has twelve aircraft ready today', 'the crew has thirteen aircraft ready today', 60.0, 'QUANTITY_OR_DATE_MISMATCH'),
    ('the crew will not leave the base today', 'the crew will leave the base today', 35.0, 'NEGATION_MISMATCH'),
    ("the crew can't leave the base today", 'the crew can leave the base today', 35.0, 'NEGATION_MISMATCH'),
])
def test_critical_changes_apply_exact_caps(reference, prediction, cap, warning):
    result = score_text_agreement(reference, prediction)
    assert result.experimental_score == cap
    assert cap in result.applied_caps
    assert warning in result.warnings


def test_tighter_cap_wins():
    result = score_text_agreement('the crew will not move 12 aircraft today', 'the crew will move 13 aircraft today')
    assert result.experimental_score == 35.0
    assert result.applied_caps == (35.0, 60.0)


@pytest.mark.parametrize('reference,prediction', [
    ('the amount is 12.5 units in total today', 'the amount is 12 5 units in total today'),
    ('the amount is -12 units in total today', 'the amount is 12 units in total today'),
    ('the date is 2026-01-02 for this event', 'the date is 2026-02-01 for this event'),
])
def test_numeric_punctuation_and_date_order_cannot_bypass_caps(reference, prediction):
    result = score_text_agreement(reference, prediction)
    assert result.experimental_score <= 60.0
    assert result.subscores.normalized_exact_match is False
    assert 60.0 in result.applied_caps


@pytest.mark.parametrize('minus', ['−', '﹣', '－', '⁻', '₋'])
def test_supported_unicode_minus_preserves_numeric_sign(minus):
    reference = f'the amount is {minus}12 units in total today'
    positive = score_text_agreement(reference, 'the amount is 12 units in total today')
    # Lexical F1, LCS and trigrams all 1; signed-quantity agreement 0:
    # 100 * (.4 + .25 + .2) = 85, capped at exactly 60.
    assert positive.experimental_score == 60.0
    assert positive.subscores.normalized_exact_match is False
    assert positive.subscores.critical_detail_agreement == 0.0
    assert positive.applied_caps == (60.0,)
    assert 'QUANTITY_OR_DATE_MISMATCH' in positive.warnings
    same_negative = score_text_agreement(reference, 'the amount is -12 units in total today')
    assert same_negative.experimental_score == 100.0
    assert same_negative.subscores.normalized_exact_match is True


@pytest.mark.parametrize('ambiguous_sign', ['–', '—', '‑', '±', '∓'])
def test_ambiguous_numeric_sign_is_rejected_instead_of_exact_match(ambiguous_sign):
    with pytest.raises(ValueError, match='numeric sign'):
        score_text_agreement(f'the amount is {ambiguous_sign}12 units', 'the amount is 12 units')


@pytest.mark.parametrize('reference,prediction', [
    ('Temperature was - 5 degrees.', 'Temperature was + 5 degrees.'),
    ('Temperature was + 5 degrees.', 'Temperature was - 5 degrees.'),
    ('Temperature was − 5 degrees.', 'Temperature was + 5 degrees.'),
    ('Temperature was + 5 degrees.', 'Temperature was − 5 degrees.'),
    ('Temperature was −\u00a05 degrees.', 'Temperature was +\u20095 degrees.'),
    ('Temperature was -\t5 degrees.', 'Temperature was +\n5 degrees.'),
])
def test_whitespace_separated_numeric_signs_cannot_erase_contradiction(reference, prediction):
    result = score_text_agreement(reference, prediction)
    assert result.experimental_score == 60.0
    assert result.subscores.normalized_exact_match is False
    assert result.applied_caps == (60.0,)
    assert 'QUANTITY_OR_DATE_MISMATCH' in result.warnings
    assert result.verified_score is None


@pytest.mark.parametrize('reference,prediction', [
    ('Temperature was - 5 degrees.', 'Temperature was -5 degrees.'),
    ('Temperature was + 5 degrees.', 'Temperature was +5 degrees.'),
    ('Temperature was − 5 degrees.', 'Temperature was -5 degrees.'),
])
def test_numeric_sign_whitespace_does_not_change_the_quantity(reference, prediction):
    result = score_text_agreement(reference, prediction)
    assert result.experimental_score == 100.0
    assert result.subscores.normalized_exact_match is True
    assert result.applied_caps == ()
