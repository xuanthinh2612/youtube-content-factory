from __future__ import annotations

import re
import unicodedata

_CJK = re.compile(r"[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]")
_WORD = re.compile(r"(?u)[^\W_]+(?:['’\-][^\W_]+)*")
_RATES = {
    "vi": ("words", 145.0),
    "en": ("words", 150.0),
    "ja": ("cjk_chars", 320.0),
    "zh": ("cjk_chars", 280.0),
    "ko": ("cjk_chars", 300.0),
}


def length_profile(language: str) -> tuple[str, float]:
    """Return the shared length metric and units-per-minute for a language."""
    lang = (language or "").lower().split("-")[0]
    if lang in _RATES:
        return _RATES[lang]
    return "words", 150.0


def measure_length(text: str, language: str) -> int:
    clean = unicodedata.normalize("NFC", clean_narration_text(text))
    metric, _ = length_profile(language)
    if metric == "cjk_chars":
        return len(_CJK.findall(clean))
    return len(_WORD.findall(clean))


def length_target(language: str, duration_seconds: int, tolerance: float = .15) -> dict:
    """Target units for writer prompts, using the same metric as duration validation."""
    metric, rate = length_profile(language)
    target = max(1, round(max(1, int(duration_seconds)) * rate / 60.0))
    return {
        "metric": metric,
        "target": target,
        "minimum": max(1, int(target * (1 - tolerance))),
        "maximum": max(1, int(target * (1 + tolerance))),
        "rate_per_minute": rate,
    }


def clean_narration_text(text: str) -> str:
    """Remove presentation markup while preserving the spoken wording."""
    lines = []
    for raw in (text or "").splitlines():
        s = raw.strip()
        if not s:
            lines.append("")
            continue
        if re.match(r"^#{1,6}\s+", s):
            continue
        if s.startswith("``` ") or s == "```":
            continue
        s = re.sub(r"^[-*+]\s+", "", s)
        s = re.sub(r"^>\s?", "", s)
        s = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", s)
        s = re.sub(r"\[([^]]+)\]\(([^)]+)\)", r"\1", s)
        s = re.sub(r"(\*\*|__|\*|_)(.*?)\1", r"\2", s)
        s = re.sub(r"`([^`]+)`", r"\1", s)
        lines.append(s)
    out = "\n".join(lines)
    out = re.sub(r"[ \t]+", " ", out)
    return re.sub(r"\n{3,}", "\n\n", out).strip()


def estimate_seconds(text: str, language: str) -> float:
    units = measure_length(text, language)
    _, rate = length_profile(language)
    return max(units, 1) / rate * 60.0


def validate_duration(text: str, language: str, target_minutes: int, tolerance: float | None = None):
    target = max(60, int(target_minutes or 1) * 60)
    if tolerance is None:
        tolerance = .15 if target_minutes <= 15 else .12
    estimated = estimate_seconds(text, language)
    ratio = estimated / target if target else 1.0
    passed = abs(estimated - target) / target <= tolerance
    issue = None if passed else (
        f"Estimated narration duration {estimated / 60:.1f} min is outside "
        f"±{int(tolerance * 100)}% of requested {target / 60:.1f} min"
    )
    return {
        "pass": passed,
        "estimated_seconds": round(estimated, 1),
        "target_seconds": target,
        "ratio": round(ratio, 3),
        "tolerance": tolerance,
        "metric": length_profile(language)[0],
        "measured_units": measure_length(text, language),
        "issues": [] if passed else [issue],
    }


def validate_story_duration(text: str, language: str, target_minutes: int,
                            minimum_ratio: float = .8, maximum_ratio: float = 1.2):
    """Accept a soft ±20% story-duration band without targeting an exact runtime."""
    target = max(60, int(target_minutes or 1) * 60)
    estimated = estimate_seconds(text, language)
    minimum = round(target * minimum_ratio)
    maximum = round(target * maximum_ratio)
    passed = minimum <= estimated <= maximum
    issue = None if passed else (
        f"Estimated story narration {estimated / 60:.1f} min is outside the "
        f"soft {minimum / 60:.1f}-{maximum / 60:.1f} min duration range "
        f"for a {target / 60:.1f} min request"
    )
    return {
        "pass": passed,
        "estimated_seconds": round(estimated, 1),
        "target_seconds": target,
        "minimum_seconds": minimum,
        "maximum_seconds": maximum,
        "ratio": round(estimated / target, 3),
        "metric": length_profile(language)[0],
        "measured_units": measure_length(text, language),
        "mode": "soft_story_duration_band",
        "issues": [] if passed else [issue],
    }
