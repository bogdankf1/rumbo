from pydantic import BaseModel


class ChunkDraft(BaseModel):
    idx: int
    section: str
    content: str


def _tokens(s: str) -> int:
    return max(1, len(s) // 4)


def chunk_text(
    text: str,
    sections: list[str] | None = None,
    target_tokens: int = 400,
) -> list[ChunkDraft]:
    """Group paragraphs into chunks of roughly target_tokens, never splitting a paragraph.

    A paragraph that starts with one of the section hints opens a new chunk
    labeled with that hint; everything else inherits the current label.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    hints = sections or []
    drafts: list[ChunkDraft] = []
    current: list[str] = []
    current_section = "body"

    def flush() -> None:
        nonlocal current
        if current:
            drafts.append(
                ChunkDraft(idx=len(drafts), section=current_section, content="\n\n".join(current))
            )
            current = []

    for para in paragraphs:
        label = next((h for h in hints if para.startswith(h)), None)
        if label is not None:
            flush()
            current_section = label
        elif current and _tokens("\n\n".join(current)) + _tokens(para) > target_tokens:
            flush()
        current.append(para)
    flush()
    return drafts
