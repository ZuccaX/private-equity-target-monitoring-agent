from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.integrations.news.base import RawNewsItem
from app.integrations.news.config import NewsSourceConfig
from app.integrations.news.normalization import sanitize_html


class PublicPageNewsAdapter:
    def __init__(self, source: NewsSourceConfig, client) -> None:
        self.source = source
        self.client = client

    def fetch(self, *, max_items: int) -> list[RawNewsItem]:
        if not self.source.url:
            raise ValueError("public page source URL is missing")
        document = self.client.get(self.source.url)
        soup = BeautifulSoup(document.body, "html.parser")
        selectors = self.source.selectors
        output: list[RawNewsItem] = []
        for node in soup.select(selectors["item"]):
            title_node = node.select_one(selectors["title"])
            link_node = node.select_one(selectors["link"])
            link = link_node.get("href") if link_node else None
            title = sanitize_html(str(title_node or ""), max_length=500)
            if not title or not isinstance(link, str):
                continue
            summary_node = (
                node.select_one(selectors["summary"])
                if selectors.get("summary")
                else None
            )
            time_node = (
                node.select_one(selectors["published_at"])
                if selectors.get("published_at")
                else None
            )
            published_at = None
            if time_node:
                published_at = time_node.get("datetime") or time_node.get_text(
                    " ", strip=True
                )
            absolute_link = urljoin(document.url, link)
            output.append(
                RawNewsItem(
                    source_item_id=absolute_link,
                    title=title,
                    url=absolute_link,
                    summary=sanitize_html(
                        str(summary_node or ""), max_length=5_000
                    ),
                    published_at=published_at,
                    language=self.source.language,
                    company_domain=self.source.company_domain,
                )
            )
            if len(output) >= max_items:
                break
        return output
