from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Literal, Optional

from pydantic import BaseModel, Field
from agents import Agent, Runner, function_tool, gen_trace_id, trace

from planner_agent import (
    ClarificationDecision,
    WebSearchItem,
    WebSearchPlan,
    clarification_agent,
    planner_agent,
)
from search_agent import SearchResultSummary, search_agent
from writer_agent import ReportData, writer_agent
from email_agent import email_agent


@dataclass
class ResearchSessionState:
    original_query: str
    clarification_needed: bool = False
    clarification_questions: list[dict[str, str]] = field(default_factory=list)
    clarification_answers: dict[str, str] = field(default_factory=dict)
    assumed_scope: str = ""
    search_plan: Optional[WebSearchPlan] = None
    search_results: list[dict[str, Any]] = field(default_factory=list)
    final_report: Optional[ReportData] = None
    trace_id: Optional[str] = None


class EmailDeliveryResult(BaseModel):
    status: str = Field(description="success or error")
    message: str = Field(description="Human-readable delivery status")
    recipient: Optional[str] = Field(default=None, description="Recipient email if available")
    status_code: Optional[str] = Field(default=None, description="Provider response code if available")


class OrchestratorResponse(BaseModel):
    stage: Literal["clarification", "planning", "search", "writing", "delivery"] = Field(
        description="Which orchestration stage this response belongs to."
    )
    status_message: str = Field(
        description="Concise status message summarizing what the orchestrator completed."
    )
    clarification_decision: Optional[ClarificationDecision] = Field(
        default=None,
        description="Clarification-stage result."
    )
    search_plan: Optional[WebSearchPlan] = Field(
        default=None,
        description="Planning-stage result."
    )
    search_result: Optional[SearchResultSummary] = Field(
        default=None,
        description="Search-stage result."
    )
    report: Optional[ReportData] = Field(
        default=None,
        description="Writing-stage result."
    )
    delivery_result: Optional[EmailDeliveryResult] = Field(
        default=None,
        description="Delivery-stage result."
    )


@function_tool
async def clarification_tool(query: str) -> dict[str, Any]:
    result = await Runner.run(
        clarification_agent,
        f"User query:\n{query}",
    )
    decision = result.final_output_as(ClarificationDecision)
    return decision.model_dump()


@function_tool
async def planning_tool(
    query: str,
    clarification_answers: str,
    assumed_scope: str,
) -> dict[str, Any]:
    planner_input = f"""
Original query:
{query}

Clarification answers:
{clarification_answers}

Working assumed scope:
{assumed_scope}
""".strip()

    result = await Runner.run(planner_agent, planner_input)
    plan = result.final_output_as(WebSearchPlan)
    return plan.model_dump()


@function_tool
async def search_tool(
    search_term: str,
    reason: str,
    priority: int,
    category: str,
) -> dict[str, Any]:
    search_input = f"""
Search term: {search_term}
Reason for searching: {reason}
Priority: {priority}
Category: {category}
""".strip()

    result = await Runner.run(search_agent, search_input)
    search_result = result.final_output_as(SearchResultSummary)
    return search_result.model_dump()


@function_tool
async def writing_tool(
    query: str,
    clarification_answers: str,
    assumed_scope: str,
    search_plan: str,
    search_results: str,
) -> dict[str, Any]:
    writer_input = f"""
Original query:
{query}

Clarification answers:
{clarification_answers}

Working assumed scope:
{assumed_scope}

Search plan:
{search_plan}

Structured search summaries:
{search_results}
""".strip()

    result = await Runner.run(writer_agent, writer_input)
    report = result.final_output_as(ReportData)
    return report.model_dump()


@function_tool
async def delivery_tool(
    report_title: str,
    short_summary: str,
    markdown_report: str,
) -> dict[str, Any]:
    email_input = f"""
Report title:
{report_title}

Short summary:
{short_summary}

Markdown report:
{markdown_report}
""".strip()

    result = await Runner.run(email_agent, email_input)
    final_output = result.final_output

    if isinstance(final_output, dict):
        return final_output

    return {
        "status": "success",
        "message": str(final_output),
    }


ORCHESTRATOR_INSTRUCTIONS = """
You are the top-level research orchestrator for a deep research system.

You coordinate specialist agents through:
1. tools that wrap specialist agents
2. handoffs to specialist agents when appropriate

Your role is not to do the research yourself. Your role is to route work to the right specialist
and return a structured orchestration response.

Available stages:
- clarification
- planning
- search
- writing
- delivery

Rules:
- Use the specialist tool that matches the requested stage.
- You may conceptually hand off to the matching specialist when useful, but the final response must always be a valid OrchestratorResponse object.
- Preserve specialist outputs faithfully; do not invent fields.
- Populate only the field relevant to the current stage.
- Always include a concise status_message.
- For clarification, return clarification_decision.
- For planning, return search_plan.
- For search, return search_result.
- For writing, return report.
- For delivery, return delivery_result.
"""

research_orchestrator_agent = Agent(
    name="ResearchOrchestratorAgent",
    instructions=ORCHESTRATOR_INSTRUCTIONS,
    tools=[
        clarification_tool,
        planning_tool,
        search_tool,
        writing_tool,
        delivery_tool,
    ],
    handoffs=[
        clarification_agent,
        planner_agent,
        search_agent,
        writer_agent,
        email_agent,
    ],
    model="gpt-5.4-mini",
    output_type=OrchestratorResponse,
)


class ResearchManager:
    """
    Streaming manager around the top-level orchestrator agent.

    The orchestrator agent is now the primary coordination layer.
    This class remains responsible for:
    - session state
    - pause/resume for clarification
    - concurrent search execution
    - streaming updates to the UI
    """

    async def run(
        self,
        query: str,
        clarification_answers: Optional[dict[str, str]] = None,
        send_email: bool = True,
    ) -> AsyncGenerator[str, None]:
        state = ResearchSessionState(
            original_query=(query or "").strip(),
            clarification_answers=clarification_answers or {},
        )

        if not state.original_query:
            yield "Please enter a research query."
            return

        trace_id = gen_trace_id()
        state.trace_id = trace_id

        try:
            with trace("Research trace", trace_id=trace_id):
                trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
                print(f"View trace: {trace_url}")
                yield f"View trace: {trace_url}"

                yield "Analyzing the query and checking whether clarification is needed..."
                clarification = await self.get_clarification_decision(state.original_query)
                state.clarification_needed = clarification.needs_clarification
                state.assumed_scope = clarification.assumed_scope
                state.clarification_questions = [
                    {"question": q.question, "reason": q.reason}
                    for q in clarification.questions
                ]

                if state.clarification_needed and not state.clarification_answers:
                    yield "Clarification needed before research can continue."
                    yield self.format_clarification_prompt(clarification)
                    return

                if state.clarification_needed and state.clarification_answers:
                    yield "Clarifications received. Tuning the research plan..."
                else:
                    yield "No clarification needed. Building the research plan..."

                search_plan = await self.plan_searches(
                    query=state.original_query,
                    clarification_answers=state.clarification_answers,
                    assumed_scope=state.assumed_scope,
                )
                state.search_plan = search_plan
                yield self.format_search_plan_summary(search_plan)

                yield "Searches planned. Running web research..."
                search_results = await self.perform_searches(search_plan)
                state.search_results = search_results

                if not search_results:
                    yield "No search results were returned successfully, so the report could not be generated."
                    return

                yield (
                    f"Search complete. Collected {len(search_results)} structured research summaries. "
                    "Writing the report..."
                )

                report = await self.write_report(
                    query=state.original_query,
                    search_plan=search_plan,
                    search_results=search_results,
                    clarification_answers=state.clarification_answers,
                    assumed_scope=state.assumed_scope,
                )
                state.final_report = report

                if send_email:
                    yield "Report written. Formatting and sending email..."
                    email_result = await self.send_email(report)
                    yield self.format_email_status(email_result)
                else:
                    yield "Report written. Email sending skipped."

                yield "Research complete."
                yield report.markdown_report

        except Exception as exc:
            error_message = f"Research failed: {str(exc)}"
            print(error_message)
            yield error_message
            return

    async def get_clarification_decision(self, query: str) -> ClarificationDecision:
        orchestrator_input = f"""
Stage: clarification

User query:
{query}

Use the clarification tool or hand off to the clarification specialist.
Return a clarification-stage OrchestratorResponse only.
""".strip()

        result = await Runner.run(research_orchestrator_agent, orchestrator_input)
        orchestrated = result.final_output_as(OrchestratorResponse)

        if orchestrated.clarification_decision is None:
            raise ValueError("Orchestrator did not return a clarification decision.")

        return orchestrated.clarification_decision

    async def plan_searches(
        self,
        query: str,
        clarification_answers: Optional[dict[str, str]] = None,
        assumed_scope: str = "",
    ) -> WebSearchPlan:
        clarification_block = self.format_clarification_answers(clarification_answers or {})

        orchestrator_input = f"""
Stage: planning

Original query:
{query}

Clarification answers:
{clarification_block}

Working assumed scope:
{assumed_scope}

Use the planning tool or hand off to the planning specialist.
Return a planning-stage OrchestratorResponse only.
""".strip()

        result = await Runner.run(research_orchestrator_agent, orchestrator_input)
        orchestrated = result.final_output_as(OrchestratorResponse)

        if orchestrated.search_plan is None:
            raise ValueError("Orchestrator did not return a search plan.")

        return orchestrated.search_plan

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[dict[str, Any]]:
        print("Searching...")
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]

        results: list[dict[str, Any]] = []
        num_completed = 0

        for task in asyncio.as_completed(tasks):
            result = await task
            num_completed += 1

            if result:
                results.append(result)

            print(f"Searching... {num_completed}/{len(tasks)} completed")

        print("Finished searching")
        return results

    async def search(self, item: WebSearchItem) -> Optional[dict[str, Any]]:
        orchestrator_input = f"""
Stage: search

Search term:
{item.query}

Reason for searching:
{item.reason}

Priority:
{item.priority}

Category:
{item.category}

Use the search tool or hand off to the search specialist.
Return a search-stage OrchestratorResponse only.
""".strip()

        try:
            result = await Runner.run(research_orchestrator_agent, orchestrator_input)
            orchestrated = result.final_output_as(OrchestratorResponse)

            if orchestrated.search_result is None:
                raise ValueError("Orchestrator did not return a search result.")

            return orchestrated.search_result.model_dump()

        except Exception as exc:
            print(f"Search failed for query '{item.query}': {exc}")
            return None

    async def write_report(
        self,
        query: str,
        search_plan: WebSearchPlan,
        search_results: list[dict[str, Any]],
        clarification_answers: Optional[dict[str, str]] = None,
        assumed_scope: str = "",
    ) -> ReportData:
        clarification_block = self.format_clarification_answers(clarification_answers or {})
        search_plan_block = self.format_search_plan_for_writer(search_plan)
        search_results_block = self.format_search_results_for_writer(search_results)

        orchestrator_input = f"""
Stage: writing

Original query:
{query}

Clarification answers:
{clarification_block}

Working assumed scope:
{assumed_scope}

Search plan:
{search_plan_block}

Structured search summaries:
{search_results_block}

Use the writing tool or hand off to the writing specialist.
Return a writing-stage OrchestratorResponse only.
""".strip()

        result = await Runner.run(research_orchestrator_agent, orchestrator_input)
        orchestrated = result.final_output_as(OrchestratorResponse)

        if orchestrated.report is None:
            raise ValueError("Orchestrator did not return a final report.")

        return orchestrated.report

    async def send_email(self, report: ReportData) -> Any:
        orchestrator_input = f"""
Stage: delivery

Report title:
{getattr(report, "report_title", "Research Report")}

Short summary:
{report.short_summary}

Markdown report:
{report.markdown_report}

Use the delivery tool or hand off to the delivery specialist.
Return a delivery-stage OrchestratorResponse only.
""".strip()

        try:
            result = await Runner.run(research_orchestrator_agent, orchestrator_input)
            orchestrated = result.final_output_as(OrchestratorResponse)

            if orchestrated.delivery_result is None:
                raise ValueError("Orchestrator did not return a delivery result.")

            return orchestrated.delivery_result.model_dump()

        except Exception as exc:
            print(f"Email sending failed: {exc}")
            return {
                "status": "error",
                "message": f"Email sending failed: {str(exc)}",
            }

    @staticmethod
    def format_clarification_prompt(clarification: ClarificationDecision) -> str:
        lines = ["I need a bit more detail before I start the research.\n"]
        for idx, item in enumerate(clarification.questions, start=1):
            lines.append(f"{idx}. {item.question}")
            lines.append(f"   Why this matters: {item.reason}")
        lines.append("\nIf you do not answer, I will proceed with this assumed scope:")
        lines.append(clarification.assumed_scope)
        return "\n".join(lines)

    @staticmethod
    def format_clarification_answers(answers: dict[str, str]) -> str:
        if not answers:
            return "No clarification answers were provided."

        lines = []
        for question, answer in answers.items():
            lines.append(f"- Question: {question}")
            lines.append(f"  Answer: {answer}")
        return "\n".join(lines)

    @staticmethod
    def format_search_plan_summary(search_plan: WebSearchPlan) -> str:
        lines = [
            "Research plan ready.",
            f"Refined query: {search_plan.refined_query}",
            f"Research goal: {search_plan.research_goal}",
        ]

        if search_plan.assumptions:
            lines.append("Assumptions:")
            lines.extend([f"- {item}" for item in search_plan.assumptions])

        lines.append("Planned searches:")
        for item in search_plan.searches:
            lines.append(f"- [Priority {item.priority}] {item.query} ({item.category})")

        return "\n".join(lines)

    @staticmethod
    def format_search_plan_for_writer(search_plan: WebSearchPlan) -> str:
        lines = [
            f"Refined query: {search_plan.refined_query}",
            f"Research goal: {search_plan.research_goal}",
        ]

        if search_plan.assumptions:
            lines.append("Assumptions:")
            lines.extend([f"- {a}" for a in search_plan.assumptions])

        lines.append("Constraints:")
        lines.append(f"- Geography: {search_plan.constraints.geography or 'Not specified'}")
        lines.append(f"- Time range: {search_plan.constraints.time_range or 'Not specified'}")
        lines.append(f"- Domain or industry: {search_plan.constraints.domain_or_industry or 'Not specified'}")
        lines.append(f"- Source preferences: {search_plan.constraints.source_preferences or 'Not specified'}")
        lines.append(f"- Output focus: {search_plan.constraints.output_focus or 'Not specified'}")

        lines.append("Searches:")
        for item in search_plan.searches:
            lines.append(
                f"- Query: {item.query} | Reason: {item.reason} | "
                f"Priority: {item.priority} | Category: {item.category}"
            )

        return "\n".join(lines)

    @staticmethod
    def format_search_results_for_writer(search_results: list[dict[str, Any]]) -> str:
        if not search_results:
            return "No search results were available."

        formatted_blocks = []
        for idx, result in enumerate(search_results, start=1):
            formatted_blocks.append(
                f"Search Result {idx}:\n{json.dumps(result, indent=2, ensure_ascii=False)}"
            )

        return "\n\n".join(formatted_blocks)

    @staticmethod
    def format_email_status(email_result: Any) -> str:
        if isinstance(email_result, dict):
            status = email_result.get("status", "unknown")
            message = email_result.get("message", "No message returned.")
            recipient = email_result.get("recipient")

            if recipient:
                return f"Email status: {status}. {message} Recipient: {recipient}"
            return f"Email status: {status}. {message}"

        return f"Email step completed: {email_result}"