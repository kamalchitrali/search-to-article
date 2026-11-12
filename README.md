# Search to Article

Turn ranked Google search results into a researched, cited article through a
React interface and a FastAPI backend.

Search to Article searches for up to 10 organic results, reviews the source
pages it can safely access, drafts an article from the reviewed evidence, and
checks the citations before returning the result. A built-in demo works without
API keys, so you can explore the complete interface immediately.

## Features

- Built-in demo mode with sample research and a prepared article
- Live Google-result retrieval through SerpApi or a compatible provider
- Review of up to 10 ranked organic results
- Concurrent source fetching with `robots.txt` checks
- Protection against private-network and unsafe redirect destinations
- Article generation through an OpenAI-compatible Chat Completions endpoint
- Numbered citations tied to original search-result ranks
- Evidence audit before a live article is returned
- Progress streaming from search through verification
- SEO title and meta-description generation
- Copy and Markdown download actions
- Configurable country, language, audience, and tone

## How it works

1. The backend requests up to 10 organic Google results for the topic.
2. It validates each destination and checks the site's `robots.txt` policy.
3. Public pages are fetched concurrently and converted into readable text.
4. At least three distinct reviewed sources are required for live generation.
5. The language model analyzes the evidence and writes a 760–840 word draft.
6. Citation ranks are checked deterministically.
7. A final model-based evidence audit checks claims against cited source text.
8. The interface displays the article, source statuses, SEO metadata, and word
   count.

## Technology

- **Frontend:** React, TypeScript, Vite, React Markdown
- **Backend:** Python, FastAPI, Uvicorn, HTTPX, aiohttp
- **Extraction:** Trafilatura
- **Testing:** Pytest and TypeScript compiler checks

## Requirements

- Python 3.11 or newer
- Node.js 22.12 or newer
- npm

API keys are not required for demo mode.

## Quick start

Clone the repository and enter the project directory:

```bash
git clone https://github.com/kamalchitrali/search-to-article.git
cd search-to-article
```

Create the local environment file:

```bash
cp .env.example .env
```

### 1. Start the backend

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

The backend runs at http://localhost:8000. Its interactive API documentation is
available at http://localhost:8000/docs.

### 2. Start the frontend

Keep the backend terminal running. Open a second terminal tab or window, enter
the same project directory, and run:

```bash
npm --prefix frontend ci
npm --prefix frontend run dev
```

Open http://localhost:5173 in your browser. Do not use port `8000` for the web
interface; that port belongs to the backend API.

## Using demo mode

Demo mode is enabled by default in `.env`:

```dotenv
DEMO_MODE=true
```

To try it:

1. Start both servers using the instructions above.
2. Open http://localhost:5173.
3. Click **Run demo**.
4. Follow the search, review, draft, and verification progress.
5. Review the generated article and ranked source list.
6. Use **Copy** or **Download Markdown** to export the result.

The demo uses a fixed meal-preparation topic and local fixtures. It does not
call a search provider or language model.

## Using live mode

Edit `.env`, disable demo mode, and supply both provider keys:

```dotenv
DEMO_MODE=false
SEARCH_API_URL=https://serpapi.com/search.json
SEARCH_API_KEY=your_search_api_key
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_API_KEY=your_llm_api_key
LLM_MODEL=gpt-4.1-mini
```

Restart the backend after changing `.env`. The interface will then accept your
own topic and show optional search and writing preferences.

Never commit `.env`. It is excluded by `.gitignore`; `.env.example` documents
the required settings without containing credentials.

### Environment variables

| Variable | Required | Description |
| --- | --- | --- |
| `DEMO_MODE` | No | Use local demo fixtures when `true`; defaults to `true`. |
| `SEARCH_API_URL` | Live mode | SerpApi or a compatible Google-search endpoint. |
| `SEARCH_API_KEY` | Live mode | Server-side search-provider credential. |
| `LLM_API_URL` | Live mode | OpenAI-compatible Chat Completions endpoint. |
| `LLM_API_KEY` | Live mode | Server-side language-model credential. |
| `LLM_MODEL` | Live mode | Provider model identifier; defaults to `gpt-4.1-mini`. |

The search endpoint must accept SerpApi-style `engine`, `api_key`, `q`, `gl`,
`hl`, and `num` parameters. Its JSON response must contain an
`organic_results` array whose entries have `title`, `link`, and optional
`snippet` fields.

The language-model endpoint must support OpenAI-compatible Chat Completions and
JSON-object response formatting.

## Using the application

In live mode:

1. Enter a topic or target keyword.
2. Optionally open **Search and writing preferences**.
3. Enter a two-letter country code such as `US` or `GB`.
4. Enter a language code such as `en`, `de`, or `en-US`.
5. Optionally describe the audience and adjust the tone.
6. Click **Generate article**.
7. Watch each research stage and review the status of every source.
8. Copy the finished article or download it as `article.md`.

Source statuses mean:

- **Reviewed:** enough readable page content was extracted and can support
  citations.
- **Snippet only:** only search-result context is available; it cannot support
  factual claims in the generated article.
- **Unavailable:** neither sufficient page text nor a usable snippet is
  available.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Backend status and frontend location. |
| `GET` | `/api/health` | Minimal health check. |
| `GET` | `/api/config` | Current mode and demo topic. |
| `POST` | `/api/articles` | Start an article job and stream NDJSON events. |
| `GET` | `/docs` | Interactive FastAPI documentation. |

Example health check:

```bash
curl http://localhost:8000/api/health
```

Example demo request:

```bash
curl -N http://localhost:8000/api/articles \
  -H 'Content-Type: application/json' \
  --data '{"topic":"weekly meal preparation"}'
```

The article endpoint streams newline-delimited JSON events with `stage`,
`sources`, `result`, or `error` types.

## Restarting the app

After the first installation, dependencies do not need to be installed again.

Backend terminal:

```bash
cd search-to-article
source .venv/bin/activate
python -m uvicorn backend.main:app --reload
```

Frontend terminal:

```bash
cd search-to-article
npm --prefix frontend run dev
```

## Tests and production build

Run the backend test suite:

```bash
.venv/bin/python -m pytest -q
```

Type-check and build the frontend:

```bash
npm --prefix frontend run build
```

The frontend build is written to `frontend/dist`. To preview it while the
backend is running:

```bash
npm --prefix frontend run preview
```

## Project structure

```text
search-to-article/
├── backend/
│   ├── main.py          # FastAPI routes and article workflow
│   ├── research.py      # Search, URL validation, fetching, and extraction
│   ├── generation.py    # Drafting, citation validation, and evidence audit
│   ├── demo.py          # Local demo fixtures
│   └── test_app.py      # Backend tests
├── frontend/
│   ├── src/main.tsx     # React application
│   ├── src/style.css    # Interface styling
│   └── vite.config.ts   # Development proxy configuration
├── .env.example         # Safe configuration template
└── README.md
```

## Security and limitations

- API keys remain on the backend and are not sent to the browser.
- URLs are restricted to public HTTP and HTTPS destinations.
- DNS results and every redirect destination are validated to reduce SSRF risk.
- Fetching respects `robots.txt` and uses a named user agent.
- Response size, redirects, timeouts, and fetch concurrency are limited.
- Retrieved pages and user preferences are treated as untrusted model input.
- Live mode requires three distinct reviewed sources.
- Citation rank validation is deterministic, but the final evidence audit is
  model-based and can still make mistakes.
- Generated content should be reviewed by a person before publication,
  especially for medical, legal, financial, or other high-stakes topics.

## Troubleshooting

### `zsh: command not found: python`

Use `python3` to create the virtual environment. After activation, `python`
will refer to `.venv/bin/python`.

### `.venv/bin/activate: no such file or directory`

The environment was not created. From the repository root, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Port 8000 shows JSON instead of the application

That is the backend status response. Open http://localhost:5173 for the React
interface.

### The frontend cannot connect to the backend

Confirm that Uvicorn is still running in the first terminal, then visit
http://localhost:8000/api/health. It should return `{"status":"ok"}`.

### `Address already in use`

Another server is already using the port. Return to the terminal running the
old process and press `Ctrl+C`, then start the server again.

### Live mode reports missing keys

Set both `SEARCH_API_KEY` and `LLM_API_KEY` in `.env`, set `DEMO_MODE=false`,
and restart the backend.

## License

This project is available under the [MIT License](LICENSE).

Copyright (c) 2026 Kamal Chitrali.
