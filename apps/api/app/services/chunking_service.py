from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    chunk_text: str
    token_count: int


class ChunkingService:
    def __init__(
        self,
        chunk_size_words: int = 120,
        overlap_words: int = 24,
    ) -> None:
        if chunk_size_words <= 0:
            raise ValueError(
                "chunk_size_words must be positive."
            )

        if overlap_words < 0:
            raise ValueError(
                "overlap_words cannot be negative."
            )

        if overlap_words >= chunk_size_words:
            raise ValueError(
                "overlap_words must be smaller "
                "than chunk_size_words."
            )

        self.chunk_size_words = chunk_size_words
        self.overlap_words = overlap_words

    def split_text(
        self,
        text: str,
    ) -> list[TextChunk]:
        words = text.split()

        if len(words) == 0:
            return []

        chunks: list[TextChunk] = []

        step_size = (
            self.chunk_size_words
            - self.overlap_words
        )

        start_index = 0
        chunk_index = 0

        while start_index < len(words):
            end_index = min(
                start_index + self.chunk_size_words,
                len(words),
            )

            chunk_words = words[
                start_index:end_index
            ]

            chunk_text = " ".join(chunk_words)

            chunks.append(
                TextChunk(
                    chunk_index=chunk_index,
                    chunk_text=chunk_text,
                    token_count=len(chunk_words),
                )
            )

            if end_index >= len(words):
                break

            start_index += step_size
            chunk_index += 1

        return chunks