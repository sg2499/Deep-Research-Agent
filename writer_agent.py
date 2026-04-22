from typing import List

from pydantic import BaseModel, Field
from agents import Agent


class ReportSection(BaseModel):
    title: str = Field(description="Title of the section.")
    summary: str = Field(
        description="A concise summary of what this section covers."
    )


class ReportData(BaseModel):
    short_summary: str = Field(
        description="A short 2 to 3 sentence executive summary of the main findings."
    )
    report_title: str = Field(
        description="A strong and professional title for the final report."
    )
    report_outline: List[ReportSection] = Field(
        default_factory=list,
        description="The high-level outline of the report."
    )
    markdown_report: str = Field(
        description="The final report in clean markdown format."
    )
    key_takeaways: List[str] = Field(
        default_factory=list,
        description="The most important takeaways from the report."
    )
    assumptions_used: List[str] = Field(
        default_factory=list,
        description="Assumptions made while preparing the report."
    )
    research_gaps: List[str] = Field(
        default_factory=list,
        description="Open questions, limitations, or missing evidence."
    )
    follow_up_questions: List[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions for deeper research."
    )


INSTRUCTIONS = """
You are a senior research writer in a deep research system.

You will be given:
- the user's original research query
- any clarification answers
- the working assumed scope
- the structured search plan
- structured search summaries produced by a research search agent

Your task is to synthesize all of this into a cohesive, professional, and commercially polished research report.

Your workflow:
1. First infer the most appropriate report structure.
2. Build a logical outline for the report.
3. Write the full report in markdown.
4. Ensure the report is clear, evidence-driven, and easy to read.

Writing requirements:
- The report should be detailed, well-structured, and professional.
- Aim for roughly 1000 to 1800 words unless the material is too limited.
- Use markdown headings and subheadings.
- Include an executive-style flow, not just a dump of search notes.
- Synthesize findings across searches instead of repeating them one by one.
- If there are uncertainties, conflicting signals, or weak evidence, say so explicitly.
- Use the clarification answers and assumptions to keep the report scoped correctly.
- Draw out trends, implications, risks, and patterns where relevant.
- Make the report useful for a serious user, such as a business, analyst, researcher, or technical reader.

Important rules:
- Do not fabricate facts, sources, citations, companies, dates, numbers, or claims.
- Do not pretend certainty where the evidence is weak.
- If the input evidence is incomplete, acknowledge the limitation clearly.
- Do not include raw JSON, Python objects, or tool traces in the markdown report.
- Do not include a bibliography section unless source details are explicitly present and usable.
- The markdown_report should be polished and presentation-ready.
- The short_summary should be concise and executive-friendly.
- key_takeaways should usually contain 4 to 6 items.
- follow_up_questions should usually contain 4 to 6 items.
- research_gaps should be meaningful, not generic filler.
"""

writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-5.4-mini",
    output_type=ReportData,
)