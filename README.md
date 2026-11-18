# AI Engineer program: IterForge capstone training

Hands-on work for the IterForge **AI Engineer** training program. It has four phases, and each one adds a piece to **TrailMate**, a small chat assistant that helps someone find a hiking trail. The domain is deliberately tiny, so you can hold the whole system in your head while it touches every part of a real applied-AI system.

| Phase | Theme | Status | Start here |
|---|---|---|---|
| 1 | Workflow orchestration with LangGraph: deterministic routing, a local LLM behind LiteLLM, SSE streaming, guardrails | ✅ complete (one live check is yours to run: [closing the live proxy check](docs/phase-1/BUILD-GUIDE.md#closing-the-live-proxy-check)) | [docs/phase-1/BUILD-GUIDE.md](docs/phase-1/BUILD-GUIDE.md) |
| 2 | (not started) | — | — |
| 3 | (not started) | — | — |
| 4 | (not started) | — | — |

## Where things live

| Path | What it is |
|---|---|
| [trailmate-workflow/](trailmate-workflow/) | **The Phase 1 service.** FastAPI + LangGraph. Its README has every step to run it. |
| [docs/phase-1/BUILD-GUIDE.md](docs/phase-1/BUILD-GUIDE.md) | **The learning guide.** What was built, step by step and day by day, with concepts, decisions, exercises, and self-check questions. |
| [docs/phase-1/walkthrough.md](docs/phase-1/walkthrough.md) | Script for the live Phase 1 walkthrough demo |
| [docs/phase-1/changes/](docs/phase-1/changes/) | One `.diff` per day: exactly what each day changed |
| [RESOURCES.md](RESOURCES.md) | Curated, link-checked learning resources (docs, courses, videos) |
| [docs/superpowers/](docs/superpowers/) | The Phase 1 design spec and implementation plan |

## Prerequisites (macOS)

- [uv](https://docs.astral.sh/uv/) 0.13+ (it installs and manages Python 3.14 for you)
- [Ollama](https://docs.ollama.com/macos), running locally
- ~5 GB of free disk space for two small local models

Then follow [trailmate-workflow/README.md](trailmate-workflow/README.md#run-it).
