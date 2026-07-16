import re
from datetime import datetime, timezone

from app.integrations.news.normalization import normalize_text
from app.models.news_article import NewsArticle
from app.services.trigger_providers.base import TriggerCandidate


RULE_VERSION = "m3-rules-v1"

RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("market_expansion", (r"\bopened? (?:a )?new (?:office|site|market)\b", r"\bexpanded? (?:into|in)\b", r"\bentered? (?:the )?[\w -]+ market\b")),
    ("product_launch", (r"\blaunched? (?:a )?(?:new )?(?:product|platform|service)\b", r"\bunveiled? (?:a )?(?:new )?(?:product|platform)\b")),
    ("partnership", (r"\bpartnership\b", r"\bpartnered with\b", r"\bstrategic alliance\b")),
    ("customer_win", (r"\bwon (?:a )?(?:major )?[\w -]+ customer\b", r"\bsigned (?:a )?(?:major )?(?:customer|client|contract)\b")),
    ("funding", (r"\braised (?:a )?(?:series [a-z] )?(?:round|funding|investment)\b", r"\bseries [a-z] round\b", r"\bfunding round\b")),
    ("leadership_hire", (r"\bappointed (?:a )?(?:new )?(?:ceo|cfo|coo|cto|chief|chair)\b", r"\bhired (?:a )?(?:new )?(?:ceo|cfo|coo|cto|chief)\b", r"\bnamed (?:a )?(?:new )?(?:ceo|cfo|coo|cto|chief)\b")),
    ("acquisition", (r"\bacquired\b", r"\bacquisition of\b", r"\bbought (?:a |the )?[\w -]+(?:company|vendor|business)\b")),
    ("layoffs", (r"\blayoffs?\b", r"\bcut \d+ jobs\b", r"\bredundancies\b")),
    ("profit_warning", (r"\bprofit warning\b", r"\blowered (?:its )?guidance\b", r"\bwarned on profits?\b")),
    ("customer_loss", (r"\blost (?:its )?(?:largest |major )?customer\b", r"\bloses? (?:a |its )?(?:largest |major )?(?:customer|client)\b", r"\bwill not renew (?:the )?contract\b")),
    ("regulatory_issue", (r"\bregulator\b.*\b(?:investigation|fine|probe)\b", r"\bregulatory (?:investigation|fine|probe|issue)\b")),
    ("management_departure", (r"\b(?:ceo|cfo|coo|cto|chief|chair) stepped down\b", r"\b(?:ceo|cfo|coo|cto|chief|chair) resigned\b", r"\bmanagement departure\b")),
    ("cyber_incident", (r"\bcyber(?:security)? (?:breach|incident|attack)\b", r"\bransomware\b", r"\bdata breach\b")),
    ("litigation", (r"\bwas sued\b", r"\blawsuit\b", r"\blitigation\b")),
)


class RuleTriggerProvider:
    version = RULE_VERSION

    def extract(self, article: NewsArticle) -> list[TriggerCandidate]:
        sentences: list[str] = []
        for part in (article.title, article.summary or ""):
            sentences.extend(
                normalize_text(sentence, max_length=2_000)
                for sentence in re.split(r"(?<=[.!?])\s+|\n+", part)
                if sentence.strip()
            )
        candidates: list[TriggerCandidate] = []
        emitted: set[str] = set()
        for trigger_type, patterns in RULES:
            for sentence in sentences:
                if any(re.search(pattern, sentence, re.IGNORECASE) for pattern in patterns):
                    if trigger_type in emitted:
                        break
                    emitted.add(trigger_type)
                    candidates.append(
                        TriggerCandidate(
                            trigger_type=trigger_type,
                            title=normalize_text(article.title, max_length=500),
                            description=normalize_text(
                                article.summary, max_length=5_000
                            )
                            or None,
                            confidence_score=0.86,
                            evidence_sentence=sentence,
                            event_date=self._event_date(
                                sentence, article.published_at
                            ),
                            extraction_method="rules",
                        )
                    )
                    break
        return candidates

    @staticmethod
    def _event_date(
        evidence: str,
        published_at: datetime | None,
    ) -> datetime:
        match = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", evidence)
        if match:
            return datetime(
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3)),
                tzinfo=timezone.utc,
            )
        if published_at is not None:
            if published_at.tzinfo is None:
                return published_at.replace(tzinfo=timezone.utc)
            return published_at.astimezone(timezone.utc)
        return datetime.now(timezone.utc)
