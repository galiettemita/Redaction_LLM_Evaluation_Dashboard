from __future__ import annotations

from dataclasses import dataclass

import pytest
from PIL import Image

from redaction_lab.ocr import OcrFailure, TesseractOcrEngine


TSV_HEADER = (
    "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\t"
    "left\ttop\twidth\theight\tconf\ttext\n"
)


@dataclass
class StubRunner:
    returncode: int = 0
    stdout: bytes = b""
    stderr: bytes = b""
    error: Exception | None = None
    input_bytes: bytes | None = None
    timeout_seconds: int | None = None

    def run(self, input_bytes: bytes, *, timeout_seconds: int) -> tuple[int, bytes, bytes]:
        self.input_bytes = input_bytes
        self.timeout_seconds = timeout_seconds
        if self.error is not None:
            raise self.error
        return self.returncode, self.stdout, self.stderr


def _image() -> Image.Image:
    return Image.new("RGB", (200, 100), "white")


def test_tesseract_tsv_produces_immutable_words_with_confidence_and_geometry() -> None:
    output = (
        TSV_HEADER
        + "5\t1\t1\t1\t1\t1\t12\t20\t42\t11\t94.25\tVisible\n"
        + "5\t1\t1\t1\t1\t2\t60\t20\t35\t11\t81.5\ttext\n"
    ).encode()
    runner = StubRunner(stdout=output)

    page = TesseractOcrEngine(runner=runner).recognize(_image())

    assert page.width == 200
    assert page.height == 100
    assert page.words[0].text == "Visible"
    assert page.words[0].confidence == 94.25
    assert page.words[0].bbox == (12, 20, 54, 31)
    assert page.words[0].line_key == (1, 1, 1)
    assert page.words[1].bbox == (60, 20, 95, 31)
    assert runner.input_bytes is not None and runner.input_bytes.startswith(b"\x89PNG")
    assert runner.timeout_seconds == 20
    with pytest.raises((AttributeError, TypeError)):
        page.words[0].text = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("runner", "max_output_bytes"),
    (
        (StubRunner(stdout=b"x" * 65), 64),
        (StubRunner(stdout=b"not tsv\nSYNTHETIC_SECRET"), 1024),
        (StubRunner(returncode=1, stderr=b"SYNTHETIC_SECRET"), 1024),
        (StubRunner(error=TimeoutError("SYNTHETIC_SECRET")), 1024),
    ),
)
def test_ocr_failures_are_bounded_and_do_not_leak_engine_output(
    runner: StubRunner, max_output_bytes: int
) -> None:
    engine = TesseractOcrEngine(
        runner=runner,
        max_output_bytes=max_output_bytes,
    )

    with pytest.raises(OcrFailure) as error:
        engine.recognize(_image())

    assert "SYNTHETIC_SECRET" not in str(error.value)
    assert "SYNTHETIC_SECRET" not in repr(error.value)


def test_ocr_rejects_invalid_word_geometry_and_nonfinite_confidence() -> None:
    invalid_rows = (
        TSV_HEADER
        + "5\t1\t1\t1\t1\t1\t190\t20\t42\t11\t94.25\tVisible\n"
        + "5\t1\t1\t1\t1\t2\t60\t20\t35\t11\tnan\ttext\n"
    ).encode()

    with pytest.raises(OcrFailure):
        TesseractOcrEngine(runner=StubRunner(stdout=invalid_rows)).recognize(_image())


def test_ocr_rejects_control_characters_without_echoing_them() -> None:
    output = (
        TSV_HEADER
        + "5\t1\t1\t1\t1\t1\t12\t20\t42\t11\t94.25\tBAD\x01TOKEN\n"
    ).encode()

    with pytest.raises(OcrFailure) as error:
        TesseractOcrEngine(runner=StubRunner(stdout=output)).recognize(_image())

    assert "BAD" not in str(error.value)
