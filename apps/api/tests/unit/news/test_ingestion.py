from app.integrations.news.normalization import content_hash


def test_content_identity_collapses_normalized_syndicated_copy() -> None:
    assert content_hash("Asteria expands", "New office opened") == content_hash(
        "  ASTERIA   EXPANDS ", "new office\nopened"
    )
