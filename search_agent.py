from typing import List, Literal, Optional

from pydantic import BaseModel, Field
from agents import Agent, ModelSettings, WebSearchTool


class EvidenceSource(BaseModel):
    title: str = Field(description="Title of the source or webpage.")
    url: str = Field(description="Direct URL of the source.")
    source_type: str = Field(
        description=(
            "Type of source, such as news article, blog, official documentation, "
            "research paper, company page, or report."
        )
    )
    publisher: Optional[str] = Field(
        default=None,
        description="Publisher, organization, or website name if identifiable."
    )


class EvidenceFinding(BaseModel):
    finding: str = Field(
        description="A concise factual finding extracted from the search results."
    )
    relevance_reason: str = Field(
        description="Why this finding is relevant to the research query."
    )
    confidence: Literal["high", "medium", "low"] = Field(
        description="Confidence level based on source quality and consistency."
    )


class SearchResultSummary(BaseModel):
    search_term: str = Field(
        description="The exact search query that was executed."
    )
    category: str = Field(
        description=(
            "The category assigned by the planner, such as background, competitors, "
            "risks, latest_updates, or technical_details."
        )
    )
    priority: int = Field(
        description="Priority assigned by the planner for this search."
    )
    concise_summary: str = Field(
        description="A concise synthesis of the most important takeaways from the search results."
    )
    key_findings: List[EvidenceFinding] = Field(
        default_factory=list,
        description="A list of the most relevant findings from this search."
    )
    notable_sources: List[EvidenceSource] = Field(
        default_factory=list,
        description="A list of the most useful sources found during this search."
    )
    gaps_or_uncertainties: List[str] = Field(
        default_factory=list,
        description=(
            "Any important missing information, conflicting signals, or uncertainty "
            "observed in the search results."
        )
    )


INSTRUCTIONS = """
You are a research search-and-summarization agent in a deep research system.

You will receive:
- a search term
- the reason for the search
- the priority of the search
- the category of the search

Your job is to:
1. Use the web search tool to search for the topic.
2. Review the most relevant results.
3. Produce a structured evidence summary for downstream report generation.

Important requirements:
- Focus on relevance to the stated search reason.
- Extract only the most useful information for a later report writer.
- Prefer concrete facts, developments, entities, trends, and evidence over fluff.
- Capture uncertainty where relevant.
- Include a short list of notable sources where possible.
- Be concise but information-dense.
- Do not add commentary outside the required structured output.
- Do not fabricate sources, URLs, publishers, or findings.
- If the search results are weak, reflect that clearly in gaps_or_uncertainties.
- The concise_summary should usually be one short paragraph.
- key_findings should usually contain 3 to 6 items.
- notable_sources should usually contain 2 to 5 items.
- Prefer high-signal sources and avoid repeating the same point across findings.
"""

search_agent = Agent(
    name="SearchAgent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="medium")],
    model="gpt-5.4-mini",
    model_settings=ModelSettings(tool_choice="required"),
    output_type=SearchResultSummary,
)