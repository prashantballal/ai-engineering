# Learning resources

A curated, link-checked list for mastering everything the AI Engineer program uses. Phase 1 is covered in full; later phases will add to the same topic sections.

> **Every link below was opened and checked on 2026-11-18.** YouTube links come from the video pages themselves (title, channel, and upload date confirmed), never from guessed IDs.

## How to use this list

- **Entry format:** `Title — type · level — why it matters for this build`.
  - Types: *official docs*, *course*, *video*, *article*, *repo*, *spec*.
  - Levels: *beginner → intermediate → advanced*.
- **⭐ = start here.** If you only have an hour for a topic, do the starred items.
- **⚠️ = outdated or a known pitfall.** Still useful, but read the note first.
- **Suggested routine for each training day:**
  1. Before you build, do the ⭐ items for that day in the [Phase 1 study path](#phase-1-study-path).
  2. Build. Read the matching section of the [build guide](docs/phase-1/BUILD-GUIDE.md).
  3. After you build, go through the rest of the topic section to go deeper.
  4. Answer the guide's "Check your understanding" questions without looking.
- **Docs that moved** (older tutorials still point at the old URLs):
  - LangGraph docs moved from `langchain-ai.github.io/langgraph` to **docs.langchain.com**.
  - LangChain concept pages moved to **reference.langchain.com**.
  - Anthropic's agents article moved from /engineering to **/research**.
  - The OpenAI Cookbook moved to **developers.openai.com**.
  - Presidio moved to **data-privacy-stack**.
  - NeMo Guardrails moved to **NVIDIA-NeMo/Guardrails**.

## Phase 1 study path

| Day | Theme | Read / watch first (⭐) | Then go deeper |
|---|---|---|---|
| 1 | Orchestration skeleton | [Building effective AI agents](https://www.anthropic.com/research/building-effective-agents) · [LangGraph quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart) · [Graph API overview](https://docs.langchain.com/oss/python/langgraph/graph-api) · [uv: working on projects](https://docs.astral.sh/uv/guides/projects/) · [FastAPI lifespan events](https://fastapi.tiangolo.com/advanced/events/) | [Workflows vs agents](#workflows-vs-agents), [uv](#uv), [LangGraph](#langgraph) state and reducers, [FastAPI](#fastapi) dependencies and async tests |
| 2 | Deterministic routing | [Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents) (the *routing* pattern) · [Sequences, branches, loops](https://docs.langchain.com/oss/python/langgraph/graph-api-control-flow) · [pytest parametrize](https://docs.pytest.org/en/stable/how-to/parametrize.html) | [Factor 8: own your control flow](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-08-own-your-control-flow.md), [Visualize your graph](https://docs.langchain.com/oss/python/langgraph/graph-api-visualize) |
| 3 | Bringing in a real model | [Ollama quickstart](https://docs.ollama.com/quickstart) · [LiteLLM CLI quick start](https://docs.litellm.ai/docs/proxy/quick_start) · [LiteLLM YAML config](https://docs.litellm.ai/docs/proxy/configs) · [LiteLLM + Ollama](https://docs.litellm.ai/docs/providers/ollama) · [LangChain models](https://docs.langchain.com/oss/python/langchain/models) | [Ollama](#ollama) FAQ (keep_alive, memory), [LiteLLM](#litellm) fallbacks and timeouts, [LangChain core](#langchain-core) ChatOpenAI |
| 4 | Streaming | [MDN: Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) · [LangGraph streaming](https://docs.langchain.com/oss/python/langgraph/streaming) · [sse-starlette README](https://github.com/sysid/sse-starlette) | [Server-Sent Events](#server-sent-events) spec and clients, [FastAPI SSE](https://fastapi.tiangolo.com/tutorial/server-sent-events/), the [ASGITransport pitfall](https://github.com/encode/httpx/issues/2186) |
| 5 | Guardrails and wrap-up | [OWASP Top 10 for LLM apps](https://genai.owasp.org/llm-top-10/) · [Prompt injection explained](https://simonwillison.net/2023/May/2/prompt-injection-explained/) · [LangChain guardrails](https://docs.langchain.com/oss/python/langchain/guardrails) | [Guardrails](#guardrails): streaming vs moderation, Presidio, frameworks |

## Workflows vs agents

*Why Phase 1 deliberately keeps the model **out** of control flow.*

- ⭐ [Building effective AI agents](https://www.anthropic.com/research/building-effective-agents) — article · beginner — The workflows vs agents distinction. TrailMate's rule-based router is its "routing" workflow, with the classifier written as plain code.
- ⭐ [Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents) — official docs · beginner/intermediate — Every pattern as a LangGraph `StateGraph`. Its routing example uses an LLM to pick the route; Phase 1 replaces that with a plain Python function.
- [12-Factor Agents](https://github.com/humanlayer/12-factor-agents) — repo · intermediate — Principles for production LLM software.
- [Factor 8: Own your control flow](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-08-own-your-control-flow.md) — article · intermediate — The case for keeping the loop in your own code. This is Phase 1's thesis.
- [How to think about agent frameworks](https://www.langchain.com/blog/how-to-think-about-agent-frameworks) — article · intermediate — Harrison Chase (Apr 2025) on why low-level control and "workflows first" matter.
- [Anthropic agent pattern notebooks](https://github.com/anthropics/claude-cookbooks/tree/main/patterns/agents) — repo · intermediate — The same patterns with no framework at all. Good for seeing what LangGraph adds.
- [Agents (Chip Huyen)](https://huyenchip.com/2025/01/07/agents.html) — article · intermediate — Optional deep dive (Jan 2025).

## uv

- ⭐ [Working on projects](https://docs.astral.sh/uv/guides/projects/) — official docs · beginner — `uv init`, `uv.lock`, `.python-version`, `uv run`.
- ⭐ [Managing dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/) — official docs · intermediate — `uv add`, `--dev`, `[dependency-groups]`.
- [Locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/) — official docs · intermediate — `--locked` / `--frozen` for CI.
- [Running commands](https://docs.astral.sh/uv/concepts/projects/run/) — official docs · beginner — What `uv run` does before running your command.
- [Python versions](https://docs.astral.sh/uv/concepts/python-versions/) and [Installing Python](https://docs.astral.sh/uv/guides/install-python/) — official docs · intermediate — `uv python pin`.
- [Using tools](https://docs.astral.sh/uv/guides/tools/) — official docs · beginner — `uvx` / `uv tool install`. This is how the LiteLLM proxy runs without touching the service's dependencies.
- [Using uv with FastAPI](https://docs.astral.sh/uv/guides/integration/fastapi/) — official docs · beginner.
- [PEP 735: Dependency Groups](https://peps.python.org/pep-0735/) — spec · intermediate — The standard behind `[dependency-groups]`.
- [uv: an in-depth guide (SaaS Pegasus)](https://www.saaspegasus.com/guides/uv-deep-dive/) — article · beginner — ⚠️ Written before uv 0.13 (Dec 2024 / Jan 2025); check flags against the docs.

## LangGraph

*Current: langgraph 1.2.22. Code written for 0.x often still runs, but `MessageGraph` and `create_react_agent` are deprecated.*

**Core docs**
- ⭐ [Quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart) — official docs · beginner.
- ⭐ [Graph API overview](https://docs.langchain.com/oss/python/langgraph/graph-api) — official docs · beginner/intermediate — `StateGraph`, state schemas, **reducers** (`Annotated[..., operator.add]`), START/END, conditional edges, `Send`, `Command`, compile, recursion limit. It recommends TypedDict or dataclass state over Pydantic for speed.
- [Thinking in the Graph API](https://docs.langchain.com/oss/python/langgraph/thinking-in-graph-api) — official docs · beginner — How to break a problem into nodes.
- [Define and update state](https://docs.langchain.com/oss/python/langgraph/graph-api-state) — official docs · intermediate.
- [Build sequences, branches, and loops](https://docs.langchain.com/oss/python/langgraph/graph-api-control-flow) — official docs · intermediate — Routers typed with `Literal`, plus async. **This is Day 2.**
- [Use Send and Command](https://docs.langchain.com/oss/python/langgraph/graph-api-send-command) — official docs · intermediate.
- [Configure nodes](https://docs.langchain.com/oss/python/langgraph/graph-api-nodes) — official docs · intermediate — Retries, per-node timeouts, error handlers, caching.
- [Visualize your graph](https://docs.langchain.com/oss/python/langgraph/graph-api-visualize) — official docs · beginner — `draw_mermaid()`. ⚠️ `draw_mermaid_png()` calls the external mermaid.ink API by default.
- ⭐ [Streaming](https://docs.langchain.com/oss/python/langgraph/streaming) — official docs · intermediate — Modes `values` / `updates` / `messages` / `custom` / `checkpoints` / `tasks` / `debug`, several at once, `version="v2"`. **This is Day 4.**
- [Event streaming](https://docs.langchain.com/oss/python/langgraph/event-streaming) — official docs · advanced — The newer `astream_events(..., version="v3")` (1.2+, still marked experimental).
- [Test](https://docs.langchain.com/oss/python/langgraph/test) — official docs · intermediate — Testing graphs and single nodes.

**Tooling (optional)**
- [LangSmith Studio](https://docs.langchain.com/oss/python/langgraph/studio) — official docs · intermediate — A visual graph debugger.
- [Run a local server](https://docs.langchain.com/oss/python/langgraph/local-server) — official docs · intermediate — `langgraph dev`; needs `langgraph-cli[inmem]` and a free LangSmith key.
- [Trace LangGraph agents](https://docs.langchain.com/langsmith/trace-with-langgraph) — official docs · intermediate — ⚠️ Tracing sends your prompts to LangSmith's cloud.

**Release notes, for spotting outdated tutorials**
- [What's new in v1](https://docs.langchain.com/oss/python/releases/langgraph-v1) · [Migration guide](https://docs.langchain.com/oss/python/migrate/langgraph-v1) · [Changelog](https://docs.langchain.com/oss/python/releases/changelog) — official docs · intermediate.

**Courses**
- ⭐ [Introduction to LangGraph (LangChain Academy)](https://academy.langchain.com/courses/intro-to-langgraph) — course · beginner→intermediate — Free, 55 lessons, about 6 h.
  - The videos predate 1.0, but the [notebooks](https://github.com/langchain-ai/langchain-academy) were updated to langchain-core 1.2+ in 2026.
  - Module 3 (streaming) still applies.
- [LangGraph Essentials (Python)](https://academy.langchain.com/courses/langgraph-essentials-python) — course · beginner — The newer ~1 h course.
- [Ambient Agents with LangGraph](https://academy.langchain.com/courses/ambient-agents) — course · advanced — For later phases.
- ⚠️ [AI Agents in LangGraph (DeepLearning.AI)](https://www.deeplearning.ai/courses/ai-agents-in-langgraph) — course · intermediate — 2024, pre-1.0.

## LangChain core

*Current: langchain-core 1.8.3, langchain-openai 1.8.2. Phase 1 uses messages, chat models and `ChatOpenAI` pointed at the LiteLLM proxy.*

- ⭐ [Messages](https://docs.langchain.com/oss/python/langchain/messages) — official docs · beginner — `SystemMessage` / `HumanMessage` / `AIMessage`, and **`AIMessageChunk` `+` aggregation**, which the reply nodes use to rebuild the full streamed message.
- ⭐ [Models](https://docs.langchain.com/oss/python/langchain/models) — official docs · beginner/intermediate — invoke / stream / batch, "base URL and proxy settings".
- [ChatOpenAI integration](https://docs.langchain.com/oss/python/integrations/chat/openai) — official docs · intermediate.
  - ⚠️ Non-standard proxy fields such as `reasoning_content` are dropped. That's one reason Phase 1 uses non-thinking models.
  - The `base_url` argument wins over env vars.
- [Streaming](https://docs.langchain.com/oss/python/langchain/streaming) and [event streaming](https://docs.langchain.com/oss/python/langchain/event-streaming) — official docs · intermediate.
- API reference (the v1 docs dropped the conceptual Runnable pages, so these are the source now) · intermediate/advanced:
  - [Runnable](https://reference.langchain.com/python/langchain-core/runnables/base/Runnable)
  - [astream_events](https://reference.langchain.com/python/langchain-core/runnables/base/Runnable/astream_events)
  - [Callbacks](https://reference.langchain.com/python/langchain-core/callbacks)
- [LiteLLM: calling the proxy from the OpenAI SDK and LangChain](https://docs.litellm.ai/docs/proxy/user_keys) — official docs · beginner.
- [ChatLiteLLM integration](https://docs.langchain.com/oss/python/integrations/chat/litellm) — official docs · intermediate — An alternative that calls LiteLLM as a library, with no proxy.
- [LangChain Essentials (Python)](https://academy.langchain.com/courses/langchain-essentials-python) — course · beginner — Free; built around `create_agent` (later phases).

## FastAPI

*Current: fastapi 0.164.0.*

- ⭐ [Server-Sent Events](https://fastapi.tiangolo.com/tutorial/server-sent-events/) and [SSE reference](https://fastapi.tiangolo.com/reference/sse/) — official docs · intermediate.
  - **FastAPI has had native SSE since 0.135.0 (Mar 2026)**: `from fastapi.sse import EventSourceResponse`.
  - It includes 15 s pings and POST support.
  - Phase 1 uses **sse-starlette** because the program specifies it; knowing both is a plus.
- [Stream data](https://fastapi.tiangolo.com/advanced/stream-data/) and [Custom response](https://fastapi.tiangolo.com/advanced/custom-response/) — official docs · intermediate — `StreamingResponse`.
- [Concurrency and async / await](https://fastapi.tiangolo.com/async/) — official docs · beginner.
- ⭐ [Lifespan events](https://fastapi.tiangolo.com/advanced/events/) — official docs · intermediate — The graph is compiled once here.
- [Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/) and [Dependencies with yield](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/) — official docs · beginner.
- [Settings and environment variables](https://fastapi.tiangolo.com/advanced/settings/) and [pydantic-settings](https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/) — official docs · beginner.
- ⭐ [Async tests](https://fastapi.tiangolo.com/advanced/async-tests/) — official docs · intermediate — `AsyncClient` + `ASGITransport`.
  - ⚠️ The lifespan is **not** run this way; see [asgi-lifespan](https://github.com/florimondmanca/asgi-lifespan).
  - Phase 1 overrides the graph dependency instead.
- [Testing dependencies with overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/) and [Testing events](https://fastapi.tiangolo.com/advanced/testing-events/) — official docs · intermediate.
- [HTTPX transports](https://www.python-httpx.org/advanced/transports/) and [HTTPX async](https://www.python-httpx.org/async/) — official docs · intermediate.
- ⚠️ [Pitfall: ASGITransport does not stream responses](https://github.com/encode/httpx/issues/2186) — issue · intermediate.
  - Test clients get the whole body at once, so endless SSE streams hang in tests. See also [this discussion](https://github.com/encode/httpx/discussions/1787).
  - Phase 1's streams always end, so its tests are safe.

## Server-Sent Events

- ⭐ [Using server-sent events (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) — official docs · beginner — The `event:` / `data:` / `id:` / `retry:` fields, comments, and reconnection.
- [WHATWG HTML standard: server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html) — spec · advanced — Read [parsing an event stream](https://html.spec.whatwg.org/multipage/server-sent-events.html#parsing-an-event-stream) and the [authoring notes](https://html.spec.whatwg.org/multipage/server-sent-events.html#authoring-notes) (keep-alive comments). The terminal client's parser follows these rules.
- [EventSource (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/EventSource) — official docs · beginner — ⚠️ GET only, no custom headers. That's why POST chat clients use `fetch` instead.
- ⭐ [sse-starlette](https://github.com/sysid/sse-starlette) — repo · intermediate — `EventSourceResponse`, the 15 s ping default, disconnect handling, nginx buffering, and testing notes. [Releases](https://github.com/sysid/sse-starlette/releases).
- [httpx-sse](https://github.com/florimondmanca/httpx-sse) — repo · intermediate — `aconnect_sse`. ⚠️ [Issue #4](https://github.com/florimondmanca/httpx-sse/issues/4): an infinite generator over `ASGITransport` yields nothing.
- [Using readable streams (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Streams_API/Using_readable_streams) and [TextDecoderStream](https://developer.mozilla.org/en-US/docs/Web/API/TextDecoderStream) — official docs · intermediate — For a POST + streaming browser client.
  - Ready-made parsers: [fetch-event-source](https://github.com/Azure/fetch-event-source), [eventsource-parser](https://github.com/rexxars/eventsource-parser).
- [curl manpage: `-N` / `--no-buffer`](https://curl.se/docs/manpage.html#-N) — official docs · beginner — Why `curl -N` is needed to watch a stream live.
- [SSE vs WebSockets (freeCodeCamp)](https://www.freecodecamp.org/news/server-sent-events-vs-websockets/) and [WebSockets vs SSE vs polling vs WebRTC (RxDB)](https://rxdb.info/articles/websockets-sse-polling-webrtc-webtransport.html) — articles · beginner.
- [Stream updates with server-sent events (web.dev)](https://web.dev/articles/eventsource-basics) — article · beginner — From 2010, but the protocol hasn't changed.

## Ollama

*Current: Ollama v0.40.16.*

- ⭐ [Quickstart](https://docs.ollama.com/quickstart) and [macOS](https://docs.ollama.com/macos) — official docs · beginner.
- ⭐ [OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility) — official docs · beginner — What LiteLLM and every OpenAI-style client rely on.
- API reference · intermediate: [Introduction](https://docs.ollama.com/api/introduction) · [Chat](https://docs.ollama.com/api/chat) · [Streaming](https://docs.ollama.com/api/streaming) · [ps](https://docs.ollama.com/api/ps).
- ⭐ [FAQ](https://docs.ollama.com/faq) — official docs · intermediate.
  - `keep_alive` defaults to 5 minutes; this is the cause of cold starts.
  - Defaults: `OLLAMA_MAX_LOADED_MODELS` 3, `OLLAMA_NUM_PARALLEL` 1.
  - Covers memory use and setting env vars on macOS with `launchctl setenv`.
- [Thinking](https://docs.ollama.com/capabilities/thinking) — official docs · intermediate — Which models "think" by default and how to switch it off.
- [Context length](https://docs.ollama.com/context-length) — official docs · intermediate.
- [Model library](https://ollama.com/library) and [thinking models](https://ollama.com/search?c=thinking) — official · beginner — Tag pages list sizes.
- [MLX on Apple Silicon](https://ollama.com/blog/mlx) and [MLX performance](https://ollama.com/blog/mlx-performance) — official blog · intermediate — The `-mlx` model tags are larger than the default tags.
- Repos: [ollama/ollama](https://github.com/ollama/ollama) · [ollama-python](https://github.com/ollama/ollama-python).

## LiteLLM

*Current: litellm 1.110.0 (LTS line 1.108.11). Supports Python 3.14 since 1.93/1.94.*

- ⭐ [CLI quick start](https://docs.litellm.ai/docs/proxy/quick_start) — official docs · beginner — Runs the proxy on port 4000 with no Docker.
- ⭐ [YAML configuration](https://docs.litellm.ai/docs/proxy/configs) — official docs · intermediate — `model_list`, `model_name` as an alias (**our tiers `fast` / `smart`**), `os.environ/VAR`, `general_settings.master_key`.
- ⭐ [Ollama provider](https://docs.litellm.ai/docs/providers/ollama) — official docs · beginner — ⚠️ Use the `ollama_chat/` prefix (calls `/api/chat`), not `ollama/` (calls `/api/generate`). `keep_alive` goes in `litellm_params`.
- [Fallbacks and reliability](https://docs.litellm.ai/docs/proxy/reliability) — official docs · intermediate — `fallbacks`, `num_retries`, cooldowns. This is our `smart → fast` fallback.
- [Timeouts](https://docs.litellm.ai/docs/proxy/timeout) — official docs · intermediate — `request_timeout` vs `stream_timeout` (time to the first chunk; cold model loads can exceed it).
- [Health checks](https://docs.litellm.ai/docs/proxy/health) — official docs · beginner — `/health/liveliness` needs no auth; `/health` makes real model calls.
- [Routing](https://docs.litellm.ai/docs/routing) and [proxy load balancing](https://docs.litellm.ai/docs/proxy/load_balancing) — official docs · intermediate.
- [Virtual keys](https://docs.litellm.ai/docs/proxy/virtual_keys) — official docs · intermediate — The master key must start with `sk-`. Virtual keys need Postgres (later phases).
- [Streaming + async](https://docs.litellm.ai/docs/completion/stream) — official docs · beginner.
- [v1.94.0 release notes](https://docs.litellm.ai/release_notes/v1.94.0/v1-94-0) (Python 3.14 support) · [changelog](https://docs.litellm.ai/release_notes) · [repo](https://github.com/BerriAI/litellm).

## Guardrails

- ⭐ [OWASP Top 10 for LLM Applications (2025)](https://genai.owasp.org/llm-top-10/) — standard · beginner — Still the current edition. Most relevant here:
  - [LLM01 Prompt injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
  - [LLM02 Sensitive information disclosure](https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/)
  - [LLM05 Improper output handling](https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/)
  - For later phases: [Agentic Top 10 for 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
- ⭐ [Prompt injection explained (Simon Willison)](https://simonwillison.net/2023/May/2/prompt-injection-explained/) — article · beginner — Why pattern-matching guardrails can be bypassed, and why defence in depth matters.
- [The lethal trifecta](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) · [Design patterns for securing LLM agents](https://simonwillison.net/2025/Jun/13/prompt-injection-design-patterns/) ([paper](https://arxiv.org/abs/2506.08837)) · [prompt-injection tag archive](https://simonwillison.net/tags/prompt-injection/) — articles · intermediate→advanced.
- ⭐ [Guardrails (LangChain docs)](https://docs.langchain.com/oss/python/langchain/guardrails) — official docs · intermediate.
  - Covers deterministic vs model-based checks and PII redact / mask / hash / block.
  - **Their streaming PII check holds back the last 128 characters**, the same idea as TrailMate's 48-character `StreamGuard` holdback.
  - It's middleware for `create_agent`; in a custom graph you write guardrail nodes instead. See also [built-in middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in).
- [Unicode general categories (UAX #44)](https://www.unicode.org/reports/tr44/#General_Category_Values) · [Python `unicodedata.category`](https://docs.python.org/3/library/unicodedata.html#unicodedata.category) — standard / official docs · intermediate — Why `normalize.py` drops every character in category `Cf` ("format": zero-width characters, the soft hyphen, bidirectional marks…) instead of a hand-made list. This was review fix 1.
- [Unicode Security Considerations (UTS #36)](https://www.unicode.org/reports/tr36/) — standard · advanced — Look-alike letters (a Cyrillic "о" for a Latin "o") and invisible characters: what normalization does and doesn't fold, and why regex guardrails stay a first layer.
- [Microsoft Presidio](https://presidio.dataprivacystack.org/) ([repo](https://github.com/data-privacy-stack/presidio)) — docs · intermediate — Production-grade PII detection, the upgrade path from regexes. Supports Python 3.11–3.14.
- **Guardrails with streaming** (the Day 5 conflict):
  - [OpenAI Guardrails: streaming vs blocking](https://openai.github.io/openai-guardrails-python/streaming_output/) — docs · advanced — It says that when streaming, "violative content may briefly appear".
  - [NeMo Guardrails: output rail streaming](https://docs.nvidia.com/nemo/guardrails/latest/configure-guardrails/yaml-schema/streaming/output-rail-streaming) — docs · advanced — `chunk_size`, `context_size`, `stream_first`.
  - [NVIDIA blog: safer LLM output streaming](https://developer.nvidia.com/blog/stream-smarter-and-safer-learn-how-nvidia-nemo-guardrails-enhance-llm-output-streaming/) — article · advanced.
- [How to implement LLM guardrails (OpenAI Cookbook, archived)](https://developers.openai.com/cookbook/examples/how_to_use_guardrails) — notebook · intermediate — Input checks that run alongside the main call, and output scoring.
- **Frameworks, for context** (Phase 1 writes rule-based checks by hand):
  - [NeMo Guardrails](https://github.com/NVIDIA-NeMo/Guardrails) — ⚠️ needs Python < 3.14.
  - [Guardrails AI](https://github.com/guardrails-ai/guardrails) ([Hub](https://guardrailsai.com/hub)) — ⚠️ needs Python < 3.14.
  - [LlamaFirewall](https://meta-llama.github.io/PurpleLlama/LlamaFirewall/)
  - [Llama Guard 4](https://dev.meta.ai/llama/docs/model-cards-and-prompt-formats/llama-guard-4) ([Llama Guard 3 on Ollama](https://ollama.com/library/llama-guard3))
  - [OpenAI Agents SDK guardrails](https://openai.github.io/openai-agents-python/guardrails/)
- ⚠️ [LLM Guard](https://github.com/protectai/llm-guard) — repo — Archived (last release May 2025, Python < 3.13). Read it for ideas only.

## Testing

- ⭐ [pytest-asyncio](https://pytest-asyncio.readthedocs.io/en/stable/) ([concepts](https://pytest-asyncio.readthedocs.io/en/stable/concepts.html), [changelog](https://pytest-asyncio.readthedocs.io/en/stable/reference/changelog.html)) — official docs · intermediate — ⚠️ 1.0 removed the `event_loop` fixture, so older tutorials break. Phase 1 uses `asyncio_mode = "auto"`.
- [AnyIO testing](https://anyio.readthedocs.io/en/stable/testing.html) — official docs · intermediate — FastAPI's docs use `@pytest.mark.anyio`; pick one plugin, not both.
- [pytest docs](https://docs.pytest.org/en/stable/) — official docs · beginner/intermediate:
  - [fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
  - ⭐ [parametrize](https://docs.pytest.org/en/stable/how-to/parametrize.html): the table-driven classifier and guardrail tests
  - [monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)
- [GenericFakeChatModel](https://reference.langchain.com/python/langchain-core/language_models/fake_chat_models/GenericFakeChatModel) — reference · intermediate — A fake chat model that streams, so you can test token streaming without Ollama. The retract demo script uses it.
- ⭐ [Hypothesis](https://hypothesis.readthedocs.io/en/latest/) — official docs · intermediate — Property-based testing: the library generates inputs, and you state a rule that must always hold. `test_any_chunking_shows_what_the_full_reply_check_shows` is a hand-rolled version. A fuzz run built the same way found the "link that ends in a digit" bug during the final review.
- [mutmut](https://mutmut.readthedocs.io/) — docs · intermediate — Mutation testing: change the code on purpose and check that some test fails. Review fix 6 did one mutation by hand (a shared StreamGuard) to prove the new concurrency test can fail.
- [RESPX](https://lundberg.github.io/respx/) — docs · intermediate — Mock HTTPX calls, such as calls to the proxy.
- [Developing with asyncio](https://docs.python.org/3/library/asyncio-dev.html) — official docs · intermediate — Debug mode, and finding never-awaited coroutines.
- [Ruff](https://docs.astral.sh/ruff/) ([configuration](https://docs.astral.sh/ruff/configuration/), [rules](https://docs.astral.sh/ruff/rules/), [formatter](https://docs.astral.sh/ruff/formatter/)) — official docs · beginner.

## Videos

*Watch pages opened 2026-11-18; dates are upload dates. Watch at 1.25×, with the code open.*

**Workflows vs agents**
- ⭐ [How We Build Effective Agents: Barry Zhang, Anthropic](https://www.youtube.com/watch?v=D7_ipDqhtwk) — AI Engineer, 2025-04, 15 min · beginner.
- [12-Factor Agents: Patterns of reliable LLM applications (Dex Horthy)](https://www.youtube.com/watch?v=8kMaTybvDUw) — AI Engineer, 2025-07, 17 min · intermediate.
- [Building Effective Agents with LangGraph](https://www.youtube.com/watch?v=aHCDrAbH_go) — LangChain, 2025-01, 31 min · intermediate · ⚠️ pre-1.0 code.

**LangGraph**
- ⭐ [LangGraph Complete Course for Beginners](https://www.youtube.com/watch?v=jGg_1h0qzaM) — freeCodeCamp.org, 2025-05, 3 h 10 min · beginner — Pre-1.0, but its StateGraph, conditional edges and `add_messages` code still runs on 1.x.
- [LangGraph Crash Course: Agent Workflows in Python](https://www.youtube.com/watch?v=uWLJAtMOVT0) — NeuralNine, 2026-05, 53 min · beginner.
- [Building LangChain and LangGraph 1.0](https://www.youtube.com/watch?v=r5Z_gYZb4Ns) — LangChain, 2025-10, 19 min · intermediate — What changed in 1.0.
- [Build Better Agent UX: Streaming Progress, Status, and File Ops](https://www.youtube.com/watch?v=3daSUNpWErQ) — LangChain, 2026-01, 6 min · intermediate — Custom progress streaming, like TrailMate's `step` events.
- [LangSmith Studio v2](https://www.youtube.com/watch?v=Mi1gSlHwZLM) — LangChain, 2025-05, 8 min · beginner.
- [LangChain vs. LangGraph vs. Deep Agents](https://www.youtube.com/watch?v=ty8i2zl9q2c) — LangChain, 2026-11, 3 min · beginner.
- [LangGraph Complete Course (From ZERO to HERO)](https://www.youtube.com/watch?v=DtW_Lc9hYoU) — Ansh Lamba, 2026-02, 6 h 12 min · beginner — The long alternative.
- Channel: [LangChain on YouTube](https://www.youtube.com/@LangChain).

**FastAPI**
- ⭐ [Python FastAPI Tutorial: Full Course for Beginners](https://www.youtube.com/watch?v=iukOehU5aF4) — Corey Schafer, 2026-04, 14 h 24 min · beginner→intermediate.
- [FastAPI Part 7: Sync vs Async](https://www.youtube.com/watch?v=2JPDt-Jp6fM) — Corey Schafer, 2026-01, 32 min · intermediate.
- [What's New in FastAPI (Sebastián Ramírez, PyAI Conf 2026)](https://www.youtube.com/watch?v=T3De9qEPgFc) — 2026-11, 22 min · intermediate — Native SSE plus an LLM-streaming demo.
- [FastAPI Crash Course](https://www.youtube.com/watch?v=8TMQcRcBnW8) — Traversy Media, 2026-01, 60 min · beginner.
- ⚠️ [Python API Development: Comprehensive Course](https://www.youtube.com/watch?v=0sOvCWFmrtA) — freeCodeCamp.org, 2021-11, 19 h — Outdated.

**Server-Sent Events**
- ⭐ [Server-Sent Events Crash Course](https://www.youtube.com/watch?v=4HlNv1qpZFY) — Hussein Nasser, 2020-07, 30 min · beginner — Old, but the protocol hasn't changed.
- [Server-Sent Events vs WebSockets](https://www.youtube.com/watch?v=X_DdIXrmWOo) — System Design School, 2024-08, 6 min · beginner.
- [WebSockets vs Polling vs Server Sent Events](https://www.youtube.com/watch?v=WS352jTTkPU) — Piyush Garg, 2025-12, 27 min · beginner.

**Ollama and LiteLLM**
- [Learn Ollama in 15 Minutes](https://www.youtube.com/watch?v=UtSSMs6ObqY) — Tech With Tim, 2025-01 · beginner — ⚠️ Model names are dated.
- ⭐ [LiteLLM Proxy Tutorial](https://www.youtube.com/watch?v=9t-W51EHgzY) — Ready Tensor, 2026-01, 14 min · intermediate.
- [LiteLLM Crash Course for Complete Beginners](https://www.youtube.com/watch?v=WyW4Ifu4rSo) — Data Science Basics | AI, 2025-06, 43 min · beginner.
- [Open WebUI + LiteLLM](https://www.youtube.com/watch?v=nQCOTzS5oU0) — NetworkChuck, 2025-03 — Optional; uses cloud models.
- No good video covers Ollama behind the LiteLLM proxy. Use the [Ollama](#ollama) and [LiteLLM](#litellm) docs.

**Guardrails**
- ⭐ [Prompt Injection, explained](https://www.youtube.com/watch?v=FgxwCaL6UTA) — Simon Willison, 2023-05, 12 min · beginner.
- [OWASP's Top 10 Ways to Attack LLMs](https://www.youtube.com/watch?v=gUNXZMcd2jU) — IBM Technology, 2026-03, 25 min · beginner.
- [Guardrails with LangChain: A Complete Crash Course](https://www.youtube.com/watch?v=ruiLq0OzjkI) — Krish Naik, 2026-03, 38 min · intermediate — Uses LangChain v1 middleware.
- [$1 AI Guardrails with fine-tuned ModernBERTs (Diego Carpintero)](https://www.youtube.com/watch?v=YZHPEkfy2kc) — AI Engineer, 2026-04, 44 min · advanced — Where classifier-based guardrails go next.

**uv and testing**
- [UV: A Faster, All-in-One Package Manager](https://www.youtube.com/watch?v=AMdG7IjgSPM) — Corey Schafer, 2025-04, 27 min · beginner.
- [How to Test Asynchronous Code in Python](https://www.youtube.com/watch?v=n1nqgMtWRwg) — ArjanCodes, 2024-03, 7 min · intermediate — ⚠️ Predates pytest-asyncio 1.0.

## Version notes

*Checked 2026-11-18 (PyPI JSON API and GitHub releases).*

| Package | Version | Notes |
|---|---|---|
| langgraph | 1.2.22 | `astream(..., version="v2")` (since 1.1) gives typed `{type, ns, data}` parts; the v1 tuple format is still the default |
| langchain-core | 1.8.3 | Requires Python 3.11+; `AIMessageChunk.text` is a property |
| langchain-openai | 1.8.2 | `ChatOpenAI(base_url=…)` for the LiteLLM proxy |
| fastapi | 0.164.0 | Native SSE since 0.135.0 |
| sse-starlette | 3.7.0 | Pings every 15 s by default |
| litellm | 1.110.0 | Python 3.14 OK (1.83.8–1.92.x refused 3.14). The `[proxy]` extra now also installs a Rust `litellm-proxy` package |
| Ollama | 0.40.16 | `qwen3.5` tags need ≥ 0.30.0 |
| pytest / pytest-asyncio | 9.2.0 / 1.5.0 | — |
| httpx | 0.28.1 | Pydantic maintains a successor, `httpx2` |

**Small Ollama chat models for 16 GB Apple Silicon (late 2026)**

| Use | Tag | Size | Thinks by default? |
|---|---|---|---|
| fast | `llama3.2:1b` *(TrailMate's `fast`)* | ~1.3 GB | No |
| smart | `qwen3:4b-instruct` *(TrailMate's `smart`)* | 2.5 GB | No (Qwen3-4B-Instruct-2507) |
| alternative | `granite4:3b` · `phi4-mini` · `llama3.2:3b` | 2.1 · 2.5 · 2.0 GB | No |
| alternative | `gemma4:e2b` / `gemma4:e4b` | 4.6 / 6.6 GB | No (opt-in thinking) |
| ⚠️ avoid here | `qwen3:4b` | — | **Yes**: now points to the always-reasoning Thinking-2507 build |
| ⚠️ avoid here | `qwen3.5:*`, `qwen3:8b` | 2.7–6.6 GB | **Yes**, unless you send `think=false` |
| too big for 16 GB alongside an IDE | `gpt-oss:20b`, `gemma4:26b`, `*:27b` | 14–18 GB | — |
