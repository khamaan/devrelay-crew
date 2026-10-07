# DevRelay Crew

A small **browser-based multi-agent coding demo** built with the open-source CrewAI framework and Gemini. Give it a small Python utility request; a manager delegates research, coding, and review to three specialists. The result is a proposed `solution.py` and `test_solution.py` for **human review**.

## Is CrewAI suitable?

Yes, for this demonstration. CrewAI has role-based agents, custom tools, tasks, and a hierarchical process with an explicit manager agent. That gives a real orchestration framework rather than a few unrelated prompts. CrewAI also has a native Gemini provider, so the demo uses your Gemini API key. Its abstraction and dependency size are more than a single-agent utility needs, so keep the scope small and use it when distinct roles and handoffs add value.

## Run on Windows

1. Install Python 3.12 and [uv](https://docs.astral.sh/uv/getting-started/installation/) if needed.
2. Double-click **Start DevRelay.bat**. It runs `uv sync`, starts the local server, and opens `http://127.0.0.1:8766`.
3. Click **Use sample idea** or describe a small Python utility in your own words.
4. Choose a Gemini model. The default, `gemini-3.5-flash-lite`, is the lower-latency option.
5. Paste your Gemini API key into the form and click **Run the crew**. You can get a key from [Google AI Studio](https://aistudio.google.com/app/apikey). Keep the launcher window open while the app runs.
6. Watch the event list and review the code, tests, research notes, source links, and review notes. Copy code only after you inspect it.

The app binds to `127.0.0.1` only. Your key is used for the current run; it is not written to the repository or browser storage. You can alternatively set `GEMINI_API_KEY` in the server environment before launch. Each run makes multiple Gemini calls and may use quota or incur charges.

Manual launch: `uv sync`, then `uv run python -m devrelay.web`. Tests: `uv run python -m unittest discover -s tests -v`.

## What happens in the backend

1. `devrelay/web.py` validates the request and creates one background job. It allows only one crew run at a time, so a double-click cannot start two expensive runs.
2. `devrelay/crew.py` creates a fresh Gemini-backed CrewAI crew for that job. `Process.hierarchical` gives the **Engineering Manager** responsibility for delegation and checking task results.
3. The **Researcher** calls `lookup_python_reference`, which searches a small curated shelf of Python standard-library notes in `devrelay/references.py`. Each note points to official Python documentation. This is **not live internet research**.
4. The **Coder** proposes one Python module and one `unittest` file as text. The coder cannot write to disk or run code.
5. The **Reviewer** calls `check_python_syntax` on both proposals. That tool uses `ast.parse`; it never imports or executes generated code. The reviewer adds edge cases and limitations to the structured delivery.
6. After CrewAI returns, `run_crew` independently parses both files again and marks any syntax failure as `needs_revision`. It only shows source URLs that the reference tool actually returned. The browser polls the job endpoint for events and displays the final delivery.

The generated tests are **written, not executed**. Syntax validity does not prove correctness, security, or fitness for production. A human should review the code, then run it in a separate test environment if appropriate. Free-tier Gemini quotas can briefly pause a run or return a 429 error; the crew is limited to six model requests per minute to reduce bursts. The app never commits generated code to GitHub or modifies your other projects.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the data flow, agent responsibilities, and a code-reading guide.

## Why this is agentic

The manager delegates work to distinct specialists. The researcher and reviewer have different allowlisted tools. Outputs from one task feed the next task as context, and the final answer is checked before display. This is a small, inspectable example of multi-agent orchestration with bounded tools and a human approval point, not an autonomous coding platform.

## Sources

- [CrewAI hierarchical process](https://docs.crewai.com/en/learn/hierarchical-process)
- [CrewAI Gemini integration](https://docs.crewai.com/en/concepts/llms)
- [CrewAI custom tools](https://docs.crewai.com/en/concepts/tools)
- [CrewAI GitHub repository and MIT license](https://github.com/crewAIInc/crewAI)
