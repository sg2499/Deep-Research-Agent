import json
from typing import AsyncGenerator, Dict, Optional

import gradio as gr
from dotenv import load_dotenv

from research_manager import ResearchManager

load_dotenv(override=True)


DEFAULT_SESSION_STATE = {
    "original_query": "",
    "clarification_questions": [],
    "clarification_prompt": "",
    "awaiting_clarification": False,
    "report": "",
}


def parse_clarification_answers(raw_text: str) -> Dict[str, str]:
    """
    Parse clarification answers entered by the user.

    Supported formats:
    1. JSON object
    2. Simple numbered or line-based answers
    """
    raw_text = (raw_text or "").strip()
    if not raw_text:
        return {}

    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, dict):
            return {str(k).strip(): str(v).strip() for k, v in parsed.items()}
    except Exception:
        pass

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    cleaned_answers = []

    for line in lines:
        if ". " in line[:4]:
            cleaned_answers.append(line.split(". ", 1)[1].strip())
        else:
            cleaned_answers.append(line)

    return {"__ordered_answers__": cleaned_answers}


def map_ordered_answers_to_questions(
    ordered_answers: list[str],
    clarification_questions: list[dict],
) -> Dict[str, str]:
    """
    Map ordered answers back to the clarification questions shown in the UI.
    """
    mapped: Dict[str, str] = {}

    for idx, item in enumerate(clarification_questions):
        question = item.get("question", f"Question {idx + 1}")
        answer = ordered_answers[idx] if idx < len(ordered_answers) else ""
        mapped[question] = answer

    return mapped


async def stream_manager_run(
    query: str,
    clarification_answers: Optional[Dict[str, str]],
    send_email: bool,
) -> AsyncGenerator[str, None]:
    """
    Thin wrapper around ResearchManager.run to keep UI code cleaner.
    """
    async for chunk in ResearchManager().run(
        query=query,
        clarification_answers=clarification_answers,
        send_email=send_email,
    ):
        yield str(chunk)


def is_clarification_prompt(chunk_text: str) -> bool:
    return "I need a bit more detail before I start the research." in chunk_text


def is_status_message(chunk_text: str) -> bool:
    known_status_prefixes = [
        "View trace:",
        "Analyzing the query",
        "Clarification needed before research can continue.",
        "Clarifications received.",
        "No clarification needed.",
        "Research plan ready.",
        "Refined query:",
        "Research goal:",
        "Assumptions:",
        "Planned searches:",
        "- [Priority",
        "Searches planned.",
        "Search complete.",
        "Report written.",
        "Email status:",
        "Email step completed:",
        "Research complete.",
        "Please enter a research query.",
        "No search results were returned successfully",
        "Research failed:",
    ]
    return any(chunk_text.startswith(prefix) for prefix in known_status_prefixes)


def extract_questions_from_prompt(clarification_prompt: str) -> list[dict[str, str]]:
    question_lines = []

    for line in clarification_prompt.splitlines():
        stripped = line.strip()
        if stripped and stripped[0].isdigit() and ". " in stripped:
            question_lines.append({"question": stripped.split(". ", 1)[1].strip()})

    return question_lines


async def start_research(query: str, send_email: bool, session_state: dict):
    query = (query or "").strip()

    if not query:
        yield (
            gr.update(value="Please enter a research query."),
            gr.update(value="", visible=False),
            gr.update(value="", visible=False),
            gr.update(value="", visible=False),
            DEFAULT_SESSION_STATE.copy(),
        )
        return

    session_state = {
        "original_query": query,
        "clarification_questions": [],
        "clarification_prompt": "",
        "awaiting_clarification": False,
        "report": "",
    }

    status_chunks: list[str] = []
    report_chunks: list[str] = []
    clarification_prompt = ""

    async for chunk_text in stream_manager_run(
        query=query,
        clarification_answers=None,
        send_email=send_email,
    ):
        if is_clarification_prompt(chunk_text):
            clarification_prompt = chunk_text
            session_state["clarification_prompt"] = clarification_prompt
            session_state["awaiting_clarification"] = True
        elif is_status_message(chunk_text):
            status_chunks.append(chunk_text)
        else:
            report_chunks.append(chunk_text)

        yield (
            gr.update(value="\n\n".join(status_chunks).strip()),
            gr.update(value="", visible=False),
            gr.update(value="", visible=False),
            gr.update(value="", visible=False),
            session_state,
        )

    if clarification_prompt:
        session_state["clarification_questions"] = extract_questions_from_prompt(
            clarification_prompt
        )

        yield (
            gr.update(value="\n\n".join(status_chunks).strip()),
            gr.update(value=clarification_prompt, visible=True),
            gr.update(
                value="",
                visible=True,
                placeholder=(
                    "Answer the questions either as JSON or line by line.\n\n"
                    "Example:\n"
                    "1. India\n"
                    "2. Last 12 months\n"
                    "3. Focus on funding and top startups\n"
                    "4. Investor-style report"
                ),
            ),
            gr.update(value="", visible=False),
            session_state,
        )
        return

    final_report = "\n\n".join(chunk.strip() for chunk in report_chunks if chunk.strip()).strip()
    session_state["report"] = final_report

    yield (
        gr.update(value="\n\n".join(status_chunks).strip()),
        gr.update(value="", visible=False),
        gr.update(value="", visible=False),
        gr.update(value=final_report, visible=bool(final_report)),
        session_state,
    )


async def continue_with_clarifications(
    clarification_input: str,
    send_email: bool,
    session_state: dict,
):
    if not session_state or not session_state.get("original_query"):
        yield (
            gr.update(value="No active research session found. Please start again."),
            gr.update(value="", visible=False),
            gr.update(value="", visible=False),
            session_state,
        )
        return

    if not session_state.get("awaiting_clarification"):
        yield (
            gr.update(value="This session is not awaiting clarification."),
            gr.update(value="", visible=False),
            gr.update(value="", visible=False),
            session_state,
        )
        return

    parsed_answers = parse_clarification_answers(clarification_input)

    if "__ordered_answers__" in parsed_answers:
        parsed_answers = map_ordered_answers_to_questions(
            parsed_answers["__ordered_answers__"],
            session_state.get("clarification_questions", []),
        )

    original_query = session_state["original_query"]
    status_chunks = ["Clarifications received. Resuming research..."]
    report_chunks: list[str] = []

    async for chunk_text in stream_manager_run(
        query=original_query,
        clarification_answers=parsed_answers,
        send_email=send_email,
    ):
        if is_status_message(chunk_text):
            status_chunks.append(chunk_text)
        else:
            report_chunks.append(chunk_text)

        yield (
            gr.update(value="\n\n".join(status_chunks).strip()),
            gr.update(value="", visible=False),
            gr.update(value="", visible=False),
            session_state,
        )

    final_report = "\n\n".join(chunk.strip() for chunk in report_chunks if chunk.strip()).strip()

    session_state["awaiting_clarification"] = False
    session_state["report"] = final_report
    session_state["clarification_prompt"] = ""
    session_state["clarification_questions"] = []

    yield (
        gr.update(value="\n\n".join(status_chunks).strip()),
        gr.update(value="", visible=False),
        gr.update(value=final_report, visible=bool(final_report)),
        session_state,
    )


def reset_session():
    return (
        gr.update(value=""),
        gr.update(value="", visible=False),
        gr.update(value="", visible=False),
        gr.update(value="", visible=False),
        gr.update(value=""),
        DEFAULT_SESSION_STATE.copy(),
    )


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    session_state = gr.State(DEFAULT_SESSION_STATE.copy())

    gr.Markdown("# Deep Research Agent")
    gr.Markdown(
        "Enter a topic to research. If needed, the system will first ask clarifying questions before running the research workflow."
    )

    query_textbox = gr.Textbox(
        label="Research Query",
        placeholder="Example: Research the AI startup ecosystem in India over the last 12 months",
        lines=3,
    )

    send_email_checkbox = gr.Checkbox(
        label="Send final report by email",
        value=True,
    )

    with gr.Row():
        run_button = gr.Button("Start Research", variant="primary")
        continue_button = gr.Button("Continue Research")
        reset_button = gr.Button("Reset")

    status_box = gr.Markdown(label="Status / Workflow Updates")

    clarification_box = gr.Markdown(
        label="Clarification Questions",
        visible=False,
    )

    clarification_input = gr.Textbox(
        label="Your Clarification Answers",
        lines=8,
        visible=False,
    )

    report_box = gr.Markdown(
        label="Final Report",
        visible=False,
    )

    run_button.click(
        fn=start_research,
        inputs=[query_textbox, send_email_checkbox, session_state],
        outputs=[status_box, clarification_box, clarification_input, report_box, session_state],
    )

    query_textbox.submit(
        fn=start_research,
        inputs=[query_textbox, send_email_checkbox, session_state],
        outputs=[status_box, clarification_box, clarification_input, report_box, session_state],
    )

    continue_button.click(
        fn=continue_with_clarifications,
        inputs=[clarification_input, send_email_checkbox, session_state],
        outputs=[status_box, clarification_box, report_box, session_state],
    )

    reset_button.click(
        fn=reset_session,
        outputs=[status_box, clarification_box, clarification_input, report_box, query_textbox, session_state],
    )

ui.launch(inbrowser=True, share=True)