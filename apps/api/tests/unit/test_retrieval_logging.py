import logging


def test_retrieval_log_contract_uses_digest_not_raw_query_or_passage(
    caplog,
) -> None:
    with caplog.at_level(logging.INFO, logger="rag.retrieval"):
        logging.getLogger("rag.retrieval").info(
            "retrieval company_id=%s requested_provider=%s "
            "effective_provider=%s fallback=%s result_count=%s query_digest=%s",
            1,
            "hashing",
            "hashing",
            False,
            1,
            "abcdef0123456789",
        )
    rendered = caplog.text
    assert "abcdef0123456789" in rendered
    assert "confidential passage" not in rendered
    assert "/Volumes/" not in rendered
