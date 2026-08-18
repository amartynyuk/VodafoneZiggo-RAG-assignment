"""LLM section topic labeling and summarization."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm.client import get_chat_model
from app.llm.schemas import PageSectionEnrichment
from app.models.schemas import SectionBlock

_SECTION_SYSTEM = """You label and summarize sections from a Ziggo product/support web page.

For each section_id:
- topic: one of features, faq, how_to, pricing, overview, other
- summary: 1-2 concise sentences capturing facts stated in the section (Dutch or English matching source)

Rules:
- Summaries must be grounded in the section text only.
- Return every section_id provided.
"""


def enrich_sections(
    sections: list[SectionBlock],
) -> tuple[dict[str, str], dict[str, str]]:
    """
    Label topics and write summaries for all sections in one LLM call.

    Returns:
        (section_summaries, section_topics) keyed by section_id.
    """
    if not sections:
        return {}, {}

    llm = get_chat_model().with_structured_output(PageSectionEnrichment)
    section_block = "\n\n".join(
        f"### section_id: {s.section_id}\n"
        f"heading: {s.heading}\n"
        f"text:\n{s.text or '(heading only)'}"
        for s in sections
    )
    messages = [
        SystemMessage(content=_SECTION_SYSTEM),
        HumanMessage(content=f"Label and summarize these sections:\n\n{section_block}"),
    ]
    result: PageSectionEnrichment = llm.invoke(messages)

    summaries = {item.section_id: item.summary for item in result.sections}
    topics = {item.section_id: item.topic for item in result.sections}
    return summaries, topics
