# 🔎 Deep Research Agent using Gradio, OpenAI Agents SDK, Web Search, and SendGrid

![GitHub repo size](https://img.shields.io/github/repo-size/sg2499/Deep-Research-Agent)
![GitHub stars](https://img.shields.io/github/stars/sg2499/Deep-Research-Agent?style=social)
![Last Commit](https://img.shields.io/github/last-commit/sg2499/Deep-Research-Agent)
![Built with Gradio](https://img.shields.io/badge/Built%20With-Gradio-orange)
![Powered by OpenAI Agents SDK](https://img.shields.io/badge/Powered%20By-OpenAI%20Agents%20SDK-black)

This repository hosts a **Deep Research Agent** built with **Gradio**, **OpenAI Agents SDK**, **Pydantic**, **SendGrid**, and **Web Search**.

The application is designed to behave like an agentic research assistant rather than a simple one-shot chatbot. It first checks whether the user’s query needs clarification, asks 3 to 4 targeted follow-up questions when necessary, generates a structured web research plan, runs multiple searches, synthesizes the findings into a long-form report, and can optionally send the final report by email.

The project now includes a **top-level orchestrator agent** that coordinates specialist agents using **agents-as-tools** and **handoffs**, making the overall architecture more modular, scalable, and portfolio-ready.

---

## 📁 Project Structure

```bash
📦Deep-Research-Agent/
├── deep_research.py        # Gradio UI and clarification/resume workflow
├── research_manager.py     # Streaming manager + orchestrator agent + stage routing
├── planner_agent.py        # Clarification agent + research planning agent
├── search_agent.py         # Web search summarization agent returning structured evidence
├── writer_agent.py         # Final report generation agent
├── email_agent.py          # Email formatting and SendGrid delivery agent
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment variable template
├── Deep Research Agent SS.png   # Screenshot of the final UI output
└── README.md               # Project documentation
```

---

## 🚀 Features

- 🧠 **Clarification-first workflow** for ambiguous or underspecified research queries
- 🗺️ **Structured planning layer** that generates a refined research objective and prioritized search plan
- 🌐 **Web search-based evidence gathering** using an agent dedicated to web research and evidence extraction
- 🧩 **Orchestrator agent architecture** with agents-as-tools and handoffs
- 📑 **Long-form markdown report generation** with executive summary, takeaways, assumptions, gaps, and follow-up questions
- 📬 **Optional email delivery** of the final report using SendGrid
- ⚡ **Concurrent search execution** for faster research runs
- 🔍 **Trace support** through the OpenAI trace system for debugging and observability
- 🖥️ **Interactive Gradio interface** with pause/resume flow for clarification answers

---

## 🏗️ System Architecture

This project is not a monolithic single-agent script. It is designed as a small multi-agent system.

### Core components

- **Gradio UI (`deep_research.py`)**
  - Accepts the initial research query
  - Displays clarification questions when needed
  - Resumes the research flow after user clarification
  - Streams workflow updates and shows the final report

- **Research Manager (`research_manager.py`)**
  - Maintains session state
  - Streams status updates to the UI
  - Uses a top-level orchestrator agent to coordinate the workflow
  - Handles pause/resume, concurrency, formatting, and delivery flow

- **Clarification Agent (`planner_agent.py`)**
  - Decides whether the query needs clarification
  - Produces 3 to 4 clarifying questions when the query is ambiguous
  - Defines a fallback assumed scope

- **Planner Agent (`planner_agent.py`)**
  - Converts the user query + clarification answers into a structured search plan
  - Produces refined query, research goal, assumptions, constraints, and prioritized searches

- **Search Agent (`search_agent.py`)**
  - Performs web searches
  - Extracts structured evidence including findings, sources, and uncertainties

- **Writer Agent (`writer_agent.py`)**
  - Synthesizes the structured research inputs into a polished long-form report

- **Email Agent (`email_agent.py`)**
  - Converts the report into clean HTML
  - Sends it using SendGrid

### End-to-end workflow

```text
User Query
   ↓
Clarification Check
   ↓
Clarifying Questions (if needed)
   ↓
Research Plan Generation
   ↓
Concurrent Web Searches
   ↓
Structured Evidence Collection
   ↓
Report Writing
   ↓
Optional Email Delivery
```

---

## 🧠 Agent Workflow Summary

### 1. Clarification stage
The system first checks if the query is too broad, vague, or underspecified.

Example:
- “Research AI opportunities” → likely needs clarification
- “Research AI agent opportunities in India for April 2026 focused on career paths and monetization” → may be clear enough to proceed directly

If clarification is needed, the user is asked a few targeted questions before any expensive research steps are run.

### 2. Planning stage
After the scope is clear, the planner generates:
- a refined query
- a research goal
- working assumptions
- research constraints
- a prioritized list of search terms

### 3. Search stage
Each search item is executed through the search agent. The search agent returns:
- concise summary
- key findings
- notable sources
- uncertainties or evidence gaps

### 4. Writing stage
The writer agent turns the collected research into a structured report with:
- report title
- executive summary
- outline
- markdown report
- key takeaways
- assumptions used
- research gaps
- follow-up questions

### 5. Delivery stage
If enabled, the email agent converts the markdown report into HTML and sends it to the configured recipient using SendGrid.

---

## 📸 Final Output Screenshot

<img src="Deep Research Agent SS.png" width="100%" alt="Deep Research Agent final output screenshot"/>

---

## 💻 How to Run the Project Locally

### 1) Clone the Repository

```bash
git clone https://github.com/sg2499/Deep-Research-Agent.git
cd Deep-Research-Agent
```

---

## 🐍 Environment Setup Options

Different developers use different workflows. This README covers the most common setup options.

### Option A — Using `uv` (fast and modern)

If you prefer `uv`, you can create and use a virtual environment like this:

```bash
uv venv
```

Activate it:

**Windows (PowerShell)**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
uv pip install -r requirements.txt
```

---

### Option B — Using standard Python `venv`

Create a virtual environment:

**Windows**

```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

### Option C — Using Conda

Create and activate a Conda environment:

```bash
conda create -n deep_research_env python=3.11 -y
conda activate deep_research_env
pip install -r requirements.txt
```

---

## 📦 Install Dependencies

The project dependencies are already listed in `requirements.txt`.

Current dependency file:

```txt
gradio>=5.0.0
python-dotenv>=1.0.0
pydantic>=2.0.0
sendgrid>=6.11.0
openai-agents>=0.0.17
```

Install them with:

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

This project depends on environment variables for authentication and email sending.

Create a `.env` file in the root of the project.

Example:

```env
OPENAI_API_KEY = your_openai_api_key_here
SENDGRID_API_KEY = your_sendgrid_api_key_here
DEFAULT_FROM_EMAIL = your_verified_sender_email_here
DEFAULT_TO_EMAIL = your_default_recipient_email_here
```

### What each variable means

- `OPENAI_API_KEY` → required to call the OpenAI API and run the agents
- `SENDGRID_API_KEY` → required only if you want email delivery enabled
- `DEFAULT_FROM_EMAIL` → must be an email identity verified inside SendGrid
- `DEFAULT_TO_EMAIL` → default recipient for the final email report

If you do not want email delivery during testing, you can still keep the fields present and simply uncheck **Send final report by email** in the UI.

---

## 🤖 OpenAI API Setup Guide

This project uses the OpenAI API through the Agents SDK.

### Step 1 — Create or sign in to your OpenAI Platform account
Go to the OpenAI developer platform and sign in:

- OpenAI API quickstart: https://developers.openai.com/api/docs/quickstart
- OpenAI API keys page: https://platform.openai.com/settings/organization/api-keys
- OpenAI pricing page: https://developers.openai.com/api/docs/pricing

### Step 2 — Create an API key
From the API keys page, create a new secret key and store it safely. Do not commit it to GitHub.

### Step 3 — Add the key to your `.env`

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### Step 4 — Alternative: export it as an environment variable directly

**macOS / Linux**

```bash
export OPENAI_API_KEY="your_api_key_here"
```

**Windows PowerShell**

```powershell
setx OPENAI_API_KEY "your_api_key_here"
```

### API cost guidance
This project uses multiple agent calls per run:
- clarification agent
- planner agent
- multiple search agent calls
- writer agent
- optional email agent

So the cost of each research run depends on:
- the length of the user query
- whether clarification is needed
- how many searches are run
- how much content comes back from search
- the length of the final report

As of the current OpenAI pricing page, `gpt-5.4-mini` is listed at **$0.75 / 1M input tokens** and **$4.50 / 1M output tokens** for standard short-context pricing, with separate batch/flex/priority pricing shown on the official pricing page. Pricing can change, so always verify current rates before publishing or scaling the project.

### Practical cost note
For personal demos and portfolio usage, costs are usually manageable, but do not assume “free” usage. Since the workflow can invoke several agents in one run, complex research prompts can consume noticeably more tokens than a simple chat app.

---

## 📬 SendGrid Setup Guide

This project uses SendGrid to send the final report by email.

### Official references

- Sender identity docs: https://www.twilio.com/docs/sendgrid/for-developers/sending-email/sender-identity
- API keys docs: https://www.twilio.com/docs/sendgrid/api-reference/api-keys
- Python quickstart: https://www.twilio.com/docs/sendgrid/for-developers/sending-email/quickstart-python

### Step 1 — Create a SendGrid account
Sign up for a SendGrid account and complete any onboarding steps required by SendGrid.

### Step 2 — Verify your sender identity
SendGrid requires sender identity verification before email sending.

You have two main options:

#### Option A — Single Sender Verification
This is the easiest option for testing and proof-of-concept work.

Use this when:
- you only need to send from one email address
- you want to get started quickly
- you do not have DNS access for your domain

SendGrid notes that Single Sender Verification is a quick way to start, but is recommended for testing only.

#### Option B — Domain Authentication
This is the preferred method for production use.

Use this when:
- you control a domain
- you can update DNS records
- you want better deliverability and sender reputation
- you want to send from any email address on your domain

SendGrid recommends Domain Authentication for production sending.

### Step 3 — Create an API key
Inside SendGrid, create an API key and store it securely.

A good practice for this project is to create a key with only the permissions you need instead of using a broader key than necessary.

### Step 4 — Add the SendGrid values to your `.env`

```env
SENDGRID_API_KEY=your_sendgrid_api_key_here
DEFAULT_FROM_EMAIL=your_verified_sender_email_here
DEFAULT_TO_EMAIL=your_default_recipient_email_here
```

### Step 5 — Make sure `DEFAULT_FROM_EMAIL` is verified
If the `DEFAULT_FROM_EMAIL` is not verified through SendGrid, email delivery will fail.

### Step 6 — Optional: disable email during development
If you only want to test the research flow, you can uncheck the **Send final report by email** option in the Gradio UI and avoid using SendGrid during your first runs.

---

## ▶️ Run the Application

Once your environment is active and the `.env` file is configured, start the app with:

```bash
python deep_research.py
```

Gradio will start a local server and print a local URL in the terminal.

Typically, you will see something like:

```text
Running on local URL:  http://127.0.0.1:7860
```

Open that in your browser.

---

## 🧪 Example Usage Flow

### Example query

```text
What are the applications of Autonomous Agentic AI as of April 2026 around the world that can help me make money?
```

### What the system will do

1. Check if your query needs clarification
2. Ask follow-up questions if the scope is too broad
3. Generate a structured research plan
4. Run multiple web searches
5. Build a detailed report
6. Optionally send the final report by email

### Example clarification answers

You can answer clarification questions in either of the following formats.

#### JSON format

```json
{
  "What geography should I focus on?": "Global",
  "What time range should I focus on?": "April 2026",
  "What angle should I prioritize?": "Income opportunities and monetization",
  "What level of detail do you want?": "Detailed but practical"
}
```

#### Line-by-line format

```text
1. Global
2. April 2026
3. Income opportunities and monetization
4. Detailed but practical
```

---

## 🧪 Troubleshooting Guide

### 1. `Missing OPENAI_API_KEY`
Cause:
- your OpenAI API key is not set

Fix:
- add `OPENAI_API_KEY` to `.env`
- or export it directly in your shell

### 2. `Missing SENDGRID_API_KEY environment variable`
Cause:
- SendGrid API key is missing, but email sending is enabled

Fix:
- add `SENDGRID_API_KEY` to `.env`
- or disable email sending in the UI

### 3. `Missing DEFAULT_FROM_EMAIL environment variable`
Cause:
- sender email is not configured

Fix:
- add `DEFAULT_FROM_EMAIL` to `.env`
- ensure it is verified in SendGrid

### 4. `Missing recipient email`
Cause:
- `DEFAULT_TO_EMAIL` is missing and no override recipient was supplied

Fix:
- add `DEFAULT_TO_EMAIL` to `.env`

### 5. SendGrid email fails even though the API key is present
Possible causes:
- sender email is not verified
- domain authentication not configured for production sending
- API key scopes are insufficient

Fix:
- verify the sender identity
- use a valid verified sender email
- check SendGrid dashboard and API key permissions

### 6. `handoffs` causes an error in the orchestrator agent
Cause:
- your installed version of the Agents SDK may not support `handoffs`

Fix:
- upgrade the package in your environment
- or temporarily remove the `handoffs=[...]` argument and keep the tool-based orchestrator logic

### 7. App installs but does not run correctly
Possible causes:
- wrong Python version
- stale virtual environment
- missing package install

Fix:
- use Python 3.11
- recreate the environment
- reinstall dependencies with `pip install -r requirements.txt`

---

## 📚 Why This Project Is Portfolio-Grade

This is not just a prompt wrapper or a one-call chatbot.

What makes it stand out:
- multi-agent architecture
- orchestrator agent with tools and handoffs
- clarification-aware planning
- structured evidence extraction
- long-form report synthesis
- optional delivery layer
- streaming UI with pause/resume user interaction

This makes it a strong project to showcase on:
- GitHub
- LinkedIn
- personal portfolio website
- resume
- technical blog posts

---

## 🧪 Dependencies

```txt
gradio>=5.0.0
python-dotenv>=1.0.0
pydantic>=2.0.0
sendgrid>=6.11.0
openai-agents>=0.0.17
```

> 📦 Full list in [`requirements.txt`](requirements.txt)

---

## 🔮 Future Improvements

Some strong next upgrades for this project would be:

- display source cards and URLs directly in the UI
- export reports as Markdown or PDF
- add research mode selection such as market research / competitor analysis / technical deep dive
- persist reports and sessions in a database
- add authentication and saved history
- add report comparison and evaluation dashboard
- add cost tracking per run

---

## ✍️ Author

Created with ❤️ by **Shailesh Gupta**  
🔗 GitHub: [sg2499](https://github.com/sg2499)  
📩 Email: shaileshgupta841@gmail.com

---

> Building agentic research workflows with structured planning, web evidence, and multi-step orchestration 🚀
