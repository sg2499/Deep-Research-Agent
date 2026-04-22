from typing import List, Literal, Optional

from pydantic import BaseModel, Field
from agents import Agent

DEFAULT_NUM_SEARCHES = 5
MIN_CLARIFYING_QUESTIONS = 3
MAX_CLARIFYING_QUESTIONS = 4


class ClarifyingQuestion(BaseModel):
    question: str = Field(
        description="A concise clarifying question that would help scope the research better."
    )
    reason: str = Field(
        description="Why this clarification matters for improving the research quality."
    )


class ClarificationDecision(BaseModel):
    needs_clarification: bool = Field(
        description="Whether the user's query is ambiguous enough to require clarification before research begins."
    )
    questions: List[ClarifyingQuestion] = Field(
        default_factory=list,
        description="3 to 4 clarifying questions to ask if clarification is needed."
    )
    assumed_scope: str = Field(
        description=(
            "If clarification is not needed, or if the system must proceed without user answers, "
            "state the working assumptions clearly."
        )
    )


class SearchConstraints(BaseModel):
    geography: Optional[str] = Field(
        default=None,
        description="Geographic scope for the research, if relevant."
    )
    time_range: Optional[str] = Field(
        default=None,
        description="Time period to focus on, if relevant."
    )
    domain_or_industry: Optional[str] = Field(
        default=None,
        description="Industry, domain, or subject area of focus."
    )
    source_preferences: Optional[str] = Field(
        default=None,
        description="Preferred source types such as news, research papers, company filings, blogs, or official documentation."
    )
    output_focus: Optional[str] = Field(
        default=None,
        description="Primary angle of the research such as market trends, technical explanation, competitor comparison, risks, or timeline."
    )


class WebSearchItem(BaseModel):
    query: str = Field(
        description="The exact web search query to run."
    )
    reason: str = Field(
        description="Why this search is important to answering the user's request."
    )
    priority: int = Field(
        ge=1,
        le=5,
        description="Priority of this search, where 1 is highest priority and 5 is lowest priority."
    )
    category: Literal[
        "background",
        "latest_updates",
        "technical_details",
        "market_landscape",
        "competitors",
        "risks",
        "regulatory",
        "evidence",
        "case_studies",
        "other",
    ] = Field(
        description="The role this search plays in the broader research plan."
    )


class WebSearchPlan(BaseModel):
    refined_query: str = Field(
        description="A cleaned-up and better-scoped restatement of the user's original query."
    )
    research_goal: str = Field(
        description="The core research objective in one or two sentences."
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Any assumptions used to proceed with planning."
    )
    constraints: SearchConstraints = Field(
        description="Structured research constraints inferred from the query and clarifications."
    )
    searches: List[WebSearchItem] = Field(
        description="A prioritized list of search queries to execute."
    )


CLARIFICATION_INSTRUCTIONS = f"""
You are a research planning assistant for a deep research system.

Your first responsibility is to decide whether the user's query is clear enough to begin research immediately.

If the query is ambiguous, underspecified, too broad, or missing important scope constraints,
you must say that clarification is needed and generate between {MIN_CLARIFYING_QUESTIONS} and {MAX_CLARIFYING_QUESTIONS}
high-value clarifying questions.

Good clarifying questions typically narrow:
- the objective of the research
- the target geography or market
- the time horizon
- the desired depth or report style
- the preferred perspective, such as technical, strategic, academic, or business

Rules:
- Ask only questions that materially improve the search quality.
- Keep each question concise and professional.
- Do not ask redundant questions.
- If the query is already sufficiently clear, set needs_clarification to false.
- Always provide an assumed_scope field, even if clarification is needed.
- assumed_scope should explain how the system would proceed if no user clarification is provided.
"""


PLANNER_INSTRUCTIONS = f"""
You are a senior research planner for a deep research system.

You will receive:
1. The user's original query
2. Any clarification answers, if available
3. A working assumed scope, if clarification was skipped or unavailable

Your job is to create a high-quality search plan for the research workflow.

Produce:
- a refined version of the query
- a clear research goal
- explicit assumptions
- structured constraints
- exactly {DEFAULT_NUM_SEARCHES} targeted web searches

Search planning rules:
- Tailor searches using the user query plus any clarifications.
- Avoid generic or overlapping searches.
- Make the search plan cover the most important dimensions of the topic.
- Prioritize searches that are likely to produce strong evidence and useful synthesis.
- Use a mix of background, current developments, evidence, risks, market/technical/regulatory angles where relevant.
- The searches should be specific enough to guide strong web retrieval.
- Each search must have a clear reason and a priority.
- Priority 1 means the most important search.
- If details are missing, use reasonable assumptions and surface them clearly.
"""

clarification_agent = Agent(
    name="ClarificationAgent",
    instructions=CLARIFICATION_INSTRUCTIONS,
    model="gpt-5.4-mini",
    output_type=ClarificationDecision,
)

planner_agent = Agent(
    name="PlannerAgent",
    instructions=PLANNER_INSTRUCTIONS,
    model="gpt-5.4-mini",
    output_type=WebSearchPlan,
)