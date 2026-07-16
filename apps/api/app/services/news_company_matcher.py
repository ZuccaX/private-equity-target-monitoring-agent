import re
from dataclasses import dataclass

from app.integrations.news.base import RawNewsItem
from app.integrations.news.config import NewsSourceConfig
from app.models.company import Company


@dataclass(frozen=True, slots=True)
class CompanyMatch:
    company_id: int | None
    confidence: float
    method: str
    category: str | None = None

    @property
    def accepted(self) -> bool:
        return self.company_id is not None


class NewsCompanyMatcher:
    def __init__(self, *, threshold: float = 0.8) -> None:
        self.threshold = threshold

    def match(
        self,
        item: RawNewsItem,
        source: NewsSourceConfig,
        companies: list[Company],
    ) -> CompanyMatch:
        active = [company for company in companies if company.deleted_at is None]
        by_domain = {
            (company.domain or "").casefold(): company
            for company in active
            if company.domain
        }
        direct_domain = source.company_domain or item.company_domain
        if direct_domain:
            company = by_domain.get(direct_domain.casefold())
            if company is None:
                return CompanyMatch(None, 0, "direct", "company_not_found")
            return CompanyMatch(company.id, 1.0, "source_binding")

        text = " ".join((item.title, item.summary or "", item.content or ""))
        matches: list[tuple[Company, float, str]] = []
        for company in active:
            candidates: list[tuple[str, float, str]] = [
                (company.name, 0.95, "name"),
            ]
            if company.domain:
                candidates.append((company.domain, 0.95, "domain"))
            aliases = company.extra_data.get("aliases", [])
            if isinstance(aliases, list):
                candidates.extend(
                    (str(alias), 0.9, "alias") for alias in aliases if alias
                )
            best: tuple[float, str] | None = None
            for phrase, confidence, method in candidates:
                if self._contains_phrase(text, phrase):
                    if best is None or confidence > best[0]:
                        best = (confidence, method)
            if best and best[0] >= self.threshold:
                matches.append((company, *best))
        if len(matches) != 1:
            category = "ambiguous_company" if matches else "company_not_found"
            return CompanyMatch(None, 0, "aggregate", category)
        company, confidence, method = matches[0]
        return CompanyMatch(company.id, confidence, method)

    @staticmethod
    def _contains_phrase(text: str, phrase: str) -> bool:
        pattern = rf"(?<![\w]){re.escape(phrase.casefold())}(?![\w])"
        return re.search(pattern, text.casefold()) is not None
