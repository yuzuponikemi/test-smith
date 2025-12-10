"""
Result Validator - Phase 1.2

Validates subtask research results for quality, language consistency,
and content relevance before aggregation.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ValidationResult:
    """Result of validating a subtask's research findings."""

    is_valid: bool
    quality_score: float  # 0.0-1.0
    relevance_score: float  # 0.0-1.0
    language_match: bool
    detected_language: str
    contains_meta_description: bool
    word_count: int
    issues: list[str]
    warnings: list[str]


# Common meta-description patterns to detect
META_DESCRIPTION_PATTERNS = [
    # English patterns
    r"RAG\s*(queries|results|retrieval)",
    r"web\s*search\s*(queries|results)",
    r"knowledge\s*base\s*(retrieval|search)",
    r"allocation\s*strategy",
    r"planner\s*(selected|decided|allocated)",
    r"query\s*optimization",
    r"internal\s*documentation",
    r"the\s*system\s*(process|allocat|retriev)",
    r"research\s*methodology\s*(used|employed)",
    r"subtask\s*(execution|processing)",
    # Japanese patterns
    r"RAG\s*(クエリ|検索|結果)",
    r"ウェブ検索\s*(クエリ|結果)",
    r"知識ベース\s*(検索|取得)",
    r"割り当て戦略",
    r"プランナー\s*(が|は)",
    r"クエリ最適化",
    r"内部ドキュメント",
    r"システム\s*(処理|プロセス)",
    r"サブタスク\s*(実行|処理)",
]


def detect_language(text: str) -> str:
    """
    Detect the primary language of text.

    Returns language code: 'ja' (Japanese), 'en' (English), 'zh' (Chinese), 'unknown'
    """
    if not text:
        return "unknown"

    # Count character types
    japanese_chars = len(re.findall(r"[\u3040-\u309f\u30a0-\u30ff]", text))  # Hiragana + Katakana
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))  # CJK
    ascii_chars = len(re.findall(r"[a-zA-Z]", text))

    total_chars = japanese_chars + chinese_chars + ascii_chars

    if total_chars == 0:
        return "unknown"

    # Japanese has hiragana/katakana
    if japanese_chars > 0:
        return "ja"

    # Chinese has CJK without hiragana/katakana
    if chinese_chars > ascii_chars:
        return "zh"

    return "en"


def count_words(text: str) -> int:
    """
    Count words in text, handling both English and Japanese.

    For Japanese, characters are counted and divided by 2 as word equivalent.
    """
    if not text:
        return 0

    # Remove markdown
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]+`", "", text)
    text = re.sub(r"[#*_\[\]()>]", " ", text)

    # Count English words
    english_words = len(re.findall(r"[a-zA-Z]+", text))

    # Count Japanese/Chinese characters
    cjk_chars = len(re.findall(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]", text))
    cjk_word_equiv = cjk_chars // 2

    return english_words + cjk_word_equiv


def check_meta_description(text: str) -> tuple[bool, list[str]]:
    """
    Check if text contains meta-descriptions of the research process.

    Returns (contains_meta, list of matched patterns)
    """
    if not text:
        return False, []

    matched_patterns = []
    text_lower = text.lower()

    for pattern in META_DESCRIPTION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            matched_patterns.append(pattern)

    return len(matched_patterns) > 0, matched_patterns


def calculate_relevance_score(
    text: str,
    original_query: str,
    focus_area: str,
) -> float:
    """
    Calculate relevance score based on keyword overlap.

    This is a simple heuristic - more sophisticated approaches would use
    embeddings or LLM evaluation.
    """
    if not text or not original_query:
        return 0.0

    # Extract keywords from query and focus area
    query_words = set(re.findall(r"\w+", original_query.lower()))
    focus_words = set(re.findall(r"\w+", focus_area.lower()))
    target_words = query_words | focus_words

    # Extract words from text
    text_words = set(re.findall(r"\w+", text.lower()))

    # Calculate overlap
    if not target_words:
        return 0.5  # Default if no keywords

    overlap = len(target_words & text_words)
    score = min(1.0, overlap / max(len(target_words), 1) * 2)  # Scale up

    return round(score, 2)


def calculate_quality_score(
    text: str,
    word_count: int,
    contains_meta: bool,
    relevance_score: float,
    min_word_count: int = 100,
) -> float:
    """
    Calculate overall quality score for subtask findings.

    Factors:
    - Word count (length adequacy)
    - Meta-description penalty
    - Relevance to query
    - Content structure (has multiple points)
    """
    if not text:
        return 0.0

    score = 0.0

    # Length factor (0.0 - 0.3)
    if word_count >= min_word_count * 2:
        score += 0.3
    elif word_count >= min_word_count:
        score += 0.2
    elif word_count >= min_word_count // 2:
        score += 0.1

    # Meta-description penalty (-0.3 if contains meta)
    if contains_meta:
        score -= 0.3

    # Relevance factor (0.0 - 0.4)
    score += relevance_score * 0.4

    # Structure factor (0.0 - 0.3)
    # Check for multiple points/bullets/paragraphs
    bullet_points = len(re.findall(r"^[\-\*•]\s", text, re.MULTILINE))
    paragraphs = len(re.findall(r"\n\n", text))

    if bullet_points >= 3 or paragraphs >= 2:
        score += 0.3
    elif bullet_points >= 1 or paragraphs >= 1:
        score += 0.15

    return max(0.0, min(1.0, round(score, 2)))


def validate_subtask_result(
    text: str,
    original_query: str,
    subtask_query: str,  # noqa: ARG001 - Reserved for future use
    focus_area: str,
    expected_language: Optional[str] = None,
    min_word_count: int = 100,
) -> ValidationResult:
    """
    Validate a subtask's research result.

    Args:
        text: The research findings text
        original_query: The user's original query
        subtask_query: The specific subtask query/description
        focus_area: The focus area for this subtask
        expected_language: Expected language code (None to auto-detect from query)
        min_word_count: Minimum acceptable word count

    Returns:
        ValidationResult with all validation metrics
    """
    issues = []
    warnings = []

    # Detect language
    detected_language = detect_language(text)

    # Determine expected language from query if not provided
    if expected_language is None:
        expected_language = detect_language(original_query)

    # Check language match
    language_match = detected_language == expected_language
    if not language_match:
        issues.append(
            f"Language mismatch: expected '{expected_language}', got '{detected_language}'"
        )

    # Count words
    word_count = count_words(text)
    if word_count < min_word_count:
        issues.append(f"Word count too low: {word_count} < {min_word_count}")
    elif word_count < min_word_count * 2:
        warnings.append(f"Word count is marginal: {word_count}")

    # Check for meta-descriptions
    contains_meta, meta_patterns = check_meta_description(text)
    if contains_meta:
        issues.append(f"Contains meta-descriptions: {meta_patterns[:3]}")

    # Calculate relevance
    relevance_score = calculate_relevance_score(text, original_query, focus_area)
    if relevance_score < 0.3:
        issues.append(f"Low relevance score: {relevance_score}")
    elif relevance_score < 0.5:
        warnings.append(f"Moderate relevance score: {relevance_score}")

    # Calculate quality score
    quality_score = calculate_quality_score(
        text, word_count, contains_meta, relevance_score, min_word_count
    )

    # Determine overall validity
    is_valid = quality_score >= 0.4 and not contains_meta and word_count >= min_word_count // 2

    return ValidationResult(
        is_valid=is_valid,
        quality_score=quality_score,
        relevance_score=relevance_score,
        language_match=language_match,
        detected_language=detected_language,
        contains_meta_description=contains_meta,
        word_count=word_count,
        issues=issues,
        warnings=warnings,
    )


def validate_all_subtask_results(
    results: dict[str, str],
    original_query: str,
    subtask_metadata: dict[str, dict],
    min_word_count: int = 100,
) -> dict[str, ValidationResult]:
    """
    Validate all subtask results.

    Args:
        results: Dict of subtask_id -> result text
        original_query: The user's original query
        subtask_metadata: Dict of subtask_id -> {"query": str, "focus_area": str}
        min_word_count: Minimum acceptable word count per subtask

    Returns:
        Dict of subtask_id -> ValidationResult
    """
    validations = {}
    expected_language = detect_language(original_query)

    for subtask_id, text in results.items():
        metadata = subtask_metadata.get(subtask_id, {})
        subtask_query = metadata.get("query", "")
        focus_area = metadata.get("focus_area", "")

        validations[subtask_id] = validate_subtask_result(
            text=text,
            original_query=original_query,
            subtask_query=subtask_query,
            focus_area=focus_area,
            expected_language=expected_language,
            min_word_count=min_word_count,
        )

    return validations


def print_validation_summary(validations: dict[str, ValidationResult]) -> None:
    """Print a summary of validation results."""
    total = len(validations)
    valid_count = sum(1 for v in validations.values() if v.is_valid)
    avg_quality = sum(v.quality_score for v in validations.values()) / max(total, 1)

    print("\n  📊 Validation Summary:")
    print(f"     Valid subtasks: {valid_count}/{total}")
    print(f"     Average quality: {avg_quality:.2f}")

    for subtask_id, result in validations.items():
        status = "✓" if result.is_valid else "✗"
        print(
            f"     {status} {subtask_id}: quality={result.quality_score:.2f}, "
            f"lang={result.detected_language}, words={result.word_count}"
        )

        if result.issues:
            for issue in result.issues[:2]:
                print(f"        ⚠️  {issue}")
