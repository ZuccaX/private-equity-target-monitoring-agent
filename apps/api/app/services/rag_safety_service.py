from __future__ import annotations

import re


class RAGSafetyService:
    _instruction_pattern = re.compile(
        r"(?i)(ignore (all |the )?(previous|system)|system prompt|"
        r"developer message|do not follow|override instructions)"
    )

    def isolate_untrusted_text(self, text: str) -> tuple[str, list[str]]:
        warnings: list[str] = []
        safe_lines: list[str] = []
        for line in text.splitlines():
            if self._instruction_pattern.search(line):
                safe_lines.append("[UNTRUSTED INSTRUCTION REMOVED]")
                if "prompt_injection_pattern_isolated" not in warnings:
                    warnings.append("prompt_injection_pattern_isolated")
            else:
                safe_lines.append(line)
        return "\n".join(safe_lines), warnings
