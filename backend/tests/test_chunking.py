from app.services.chunking import chunk_text


def test_groups_short_paragraphs() -> None:
    text = "\n\n".join(
        f"Paragraph number {i} with a little bit of text." for i in range(6)
    )
    chunks = chunk_text(text, target_tokens=400)
    assert 1 <= len(chunks) < 6


def test_never_splits_a_paragraph_and_respects_target() -> None:
    para = "word " * 300
    text = "\n\n".join([para, para, para])
    chunks = chunk_text(text, target_tokens=400)
    assert len(chunks) == 3
    assert all(len(c.content) // 4 <= 600 for c in chunks)


def test_section_labels_from_hints() -> None:
    text = "Experience at Acme\n\nDid things.\n\nEducation\n\nBS in CS."
    chunks = chunk_text(
        text, sections=["Experience at Acme", "Education"], target_tokens=50
    )
    assert chunks[0].section == "Experience at Acme"
    assert chunks[-1].section == "Education"


def test_indexes_sequential() -> None:
    text = "\n\n".join("p" * 100 for _ in range(5))
    chunks = chunk_text(text, target_tokens=10)
    assert [c.idx for c in chunks] == list(range(len(chunks)))
