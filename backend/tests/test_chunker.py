"""Tests for the log chunker service."""

from app.services.chunker import (
    chunk_logs,
    truncate_log_entry,
    prioritize_logs,
    estimate_tokens,
    format_chunks_for_prompt,
)


def test_estimate_tokens():
    """Test token estimation (1 token ≈ 4 chars)."""
    assert estimate_tokens("") == 0
    assert estimate_tokens("a" * 100) == 25
    assert estimate_tokens("hello world") == 2  # 11 chars // 4


def test_truncate_short_entry():
    """Short entries should not be truncated."""
    entry = "Short log entry"
    assert truncate_log_entry(entry) == entry


def test_truncate_long_entry():
    """Long entries should be truncated with marker."""
    entry = "x" * 5000
    result = truncate_log_entry(entry, max_length=100)
    assert len(result) < 5000
    assert "TRUNCATED" in result


def test_prioritize_logs_errors_first():
    """Error logs should appear before info logs."""
    logs = [
        "INFO: Request processed",
        "ERROR: Connection failed",
        "WARN: High memory usage",
        "INFO: Server started",
    ]
    result = prioritize_logs(logs)
    assert "ERROR" in result[0]
    assert "WARN" in result[1]


def test_chunk_logs_single_chunk():
    """Small log sets should produce a single chunk."""
    logs = ["Log entry 1", "Log entry 2", "Log entry 3"]
    chunks = chunk_logs(logs, chunk_size=1000)
    assert len(chunks) == 1
    assert len(chunks[0]) == 3


def test_chunk_logs_multiple_chunks():
    """Large log sets should be split into multiple chunks."""
    # Create logs that exceed a small chunk size
    logs = [f"Log entry {i}: " + "x" * 200 for i in range(50)]
    chunks = chunk_logs(logs, chunk_size=500)
    assert len(chunks) > 1


def test_chunk_logs_empty():
    """Empty log list should produce empty chunks."""
    chunks = chunk_logs([])
    assert chunks == []


def test_format_chunks_for_prompt():
    """Test chunk formatting produces numbered entries."""
    chunks = [["entry 1", "entry 2"], ["entry 3"]]
    formatted = format_chunks_for_prompt(chunks)
    assert len(formatted) == 2
    assert "Chunk 1/2" in formatted[0]
    assert "Chunk 2/2" in formatted[1]
    assert "[1]" in formatted[0]
