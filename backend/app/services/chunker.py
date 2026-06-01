"""
Log chunking and truncation service.

Large log sets need to be split into manageable chunks before sending
to the LLM, which has a limited context window. This module implements
intelligent chunking with overlap to preserve context between chunks,
and prioritizes error-level logs for better analysis quality.
"""

from typing import Any

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text string.
    
    Uses the rough heuristic of 1 token ≈ 4 characters,
    which is reasonably accurate for English text.
    A more precise tokenizer could be used if needed.
    
    Args:
        text: Input text.
    
    Returns:
        Estimated token count.
    """
    return len(text) // 4


def truncate_log_entry(entry: str, max_length: int | None = None) -> str:
    """
    Truncate a single log entry to the configured maximum length.
    
    Adds a truncation marker to indicate that content was removed,
    so the LLM knows to account for missing context.
    
    Args:
        entry: Raw log entry string.
        max_length: Max characters. Defaults to settings.MAX_LOG_ENTRY_LENGTH.
    
    Returns:
        Truncated log entry with marker if truncation occurred.
    """
    max_len = max_length or settings.MAX_LOG_ENTRY_LENGTH
    if len(entry) <= max_len:
        return entry
    return entry[:max_len] + " ... [TRUNCATED]"


def prioritize_logs(log_entries: list[str]) -> list[str]:
    """
    Reorder logs to prioritize error and warning entries.
    
    Error-level logs are most valuable for root cause analysis,
    so they should appear first in the prompt to ensure they're
    within the model's attention window.
    
    Prioritization order:
    1. ERROR / FATAL / CRITICAL entries
    2. WARN / WARNING entries
    3. All other entries (INFO, DEBUG, TRACE)
    
    Args:
        log_entries: List of log entry strings.
    
    Returns:
        Reordered list with errors first.
    """
    errors: list[str] = []
    warnings: list[str] = []
    others: list[str] = []

    error_keywords = {"error", "fatal", "critical", "exception", "panic"}
    warn_keywords = {"warn", "warning"}

    for entry in log_entries:
        entry_lower = entry.lower()
        if any(kw in entry_lower for kw in error_keywords):
            errors.append(entry)
        elif any(kw in entry_lower for kw in warn_keywords):
            warnings.append(entry)
        else:
            others.append(entry)

    return errors + warnings + others


def chunk_logs(
    log_entries: list[str],
    chunk_size: int | None = None,
    overlap: int = 3,
) -> list[list[str]]:
    """
    Split log entries into chunks that fit within the LLM's token budget.
    
    Each chunk stays within the configured token limit. An overlap of
    N entries between consecutive chunks preserves context continuity,
    helping the LLM understand sequences that span chunk boundaries.
    
    Algorithm:
    1. Prioritize logs (errors first)
    2. Truncate individual entries
    3. Greedily fill chunks up to the token budget
    4. Include overlap entries from the end of the previous chunk
    
    Args:
        log_entries: List of log entry strings.
        chunk_size: Max tokens per chunk. Defaults to settings.CHUNK_SIZE.
        overlap: Number of entries to overlap between consecutive chunks.
    
    Returns:
        List of chunks, where each chunk is a list of log entries.
    """
    max_tokens = chunk_size or settings.CHUNK_SIZE

    # Step 1: Prioritize
    prioritized = prioritize_logs(log_entries)

    # Step 2: Truncate individual entries
    truncated = [truncate_log_entry(entry) for entry in prioritized]

    # Step 3: Enforce max log entries limit
    if len(truncated) > settings.MAX_LOG_ENTRIES:
        logger.warning(
            "Log entries exceed maximum, truncating",
            total=len(truncated),
            max_entries=settings.MAX_LOG_ENTRIES,
        )
        truncated = truncated[:settings.MAX_LOG_ENTRIES]

    # Step 4: Build chunks
    chunks: list[list[str]] = []
    current_chunk: list[str] = []
    current_tokens = 0

    for entry in truncated:
        entry_tokens = estimate_tokens(entry)

        # If single entry exceeds chunk size, force it into its own chunk
        if entry_tokens > max_tokens:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_tokens = 0
            # Further truncate to fit
            max_chars = max_tokens * 4
            chunks.append([entry[:max_chars] + " ... [CHUNK-TRUNCATED]"])
            continue

        # If adding this entry would exceed the limit, start a new chunk
        if current_tokens + entry_tokens > max_tokens:
            chunks.append(current_chunk)
            # Start new chunk with overlap from previous
            overlap_entries = current_chunk[-overlap:] if overlap > 0 else []
            current_chunk = list(overlap_entries)
            current_tokens = sum(estimate_tokens(e) for e in current_chunk)

        current_chunk.append(entry)
        current_tokens += entry_tokens

    # Don't forget the last chunk
    if current_chunk:
        chunks.append(current_chunk)

    logger.info(
        "Logs chunked",
        total_entries=len(log_entries),
        chunks_created=len(chunks),
        avg_chunk_size=sum(len(c) for c in chunks) / len(chunks) if chunks else 0,
    )

    return chunks


def format_chunks_for_prompt(chunks: list[list[str]]) -> list[str]:
    """
    Convert chunked log lists into formatted text blocks for prompt inclusion.
    
    Each chunk is formatted with a header indicating its position and
    the entries are numbered for easy reference in the LLM's response.
    
    Args:
        chunks: List of chunked log entry lists.
    
    Returns:
        List of formatted text blocks, one per chunk.
    """
    formatted: list[str] = []

    for i, chunk in enumerate(chunks, 1):
        header = f"=== Log Chunk {i}/{len(chunks)} ({len(chunk)} entries) ==="
        entries = [f"  [{j}] {entry}" for j, entry in enumerate(chunk, 1)]
        formatted.append(header + "\n" + "\n".join(entries))

    return formatted
