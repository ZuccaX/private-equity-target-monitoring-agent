from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

from app.integrations.news.base import RawNewsItem
from app.integrations.news.config import NewsSourceConfig
from app.integrations.news.normalization import sanitize_html


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(element, *names: str) -> str | None:
    accepted = set(names)
    for child in element:
        if _local_name(child.tag) in accepted:
            return (child.text or "").strip() or None
    return None


class RssNewsAdapter:
    def __init__(self, source: NewsSourceConfig, client) -> None:
        self.source = source
        self.client = client

    def fetch(self, *, max_items: int) -> list[RawNewsItem]:
        if not self.source.url:
            raise ValueError("RSS source URL is missing")
        document = self.client.get(self.source.url)
        if b"<!DOCTYPE" in document.body.upper() or b"<!ENTITY" in document.body.upper():
            raise ValueError("unsafe XML payload")
        try:
            root = ElementTree.fromstring(document.body)
        except (DefusedXmlException, ElementTree.ParseError) as exc:
            raise ValueError("invalid or unsafe XML payload") from exc

        entries = [
            element
            for element in root.iter()
            if _local_name(element.tag) in {"item", "entry"}
        ]
        output: list[RawNewsItem] = []
        for entry in entries:
            title = _child_text(entry, "title")
            link = _child_text(entry, "link")
            if not link:
                for child in entry:
                    if _local_name(child.tag) == "link" and child.get("href"):
                        link = child.get("href")
                        break
            if not title or not link:
                continue
            raw_summary = _child_text(entry, "description", "summary", "content")
            output.append(
                RawNewsItem(
                    source_item_id=_child_text(entry, "guid", "id"),
                    title=sanitize_html(title, max_length=500),
                    url=link,
                    summary=sanitize_html(raw_summary, max_length=5_000),
                    published_at=_child_text(
                        entry, "pubDate", "published", "updated"
                    ),
                    language=self.source.language,
                    company_domain=self.source.company_domain,
                )
            )
            if len(output) >= max_items:
                break
        return output
