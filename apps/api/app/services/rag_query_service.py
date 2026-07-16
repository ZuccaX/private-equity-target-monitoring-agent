from __future__ import annotations

from app.models.company import Company
from app.models.investment_mandate import InvestmentMandate
from app.models.trigger import Trigger


class RAGQueryService:
    def build(
        self,
        *,
        user_query: str,
        company: Company,
        mandate: InvestmentMandate | None,
        triggers: list[Trigger],
    ) -> str:
        facts = [
            user_query.strip(),
            f"Company: {company.name}",
            f"Sector: {company.sector}",
            f"Geography: {company.country}",
        ]
        if mandate is not None:
            facts.append(f"Mandate: {mandate.name}")
            if mandate.target_sectors:
                facts.append("Target sectors: " + ", ".join(mandate.target_sectors))
            if mandate.target_countries:
                facts.append(
                    "Target countries: " + ", ".join(mandate.target_countries)
                )
        for trigger in triggers[:5]:
            facts.append(f"Recent trigger: {trigger.title}")
        return "\n".join(facts)
