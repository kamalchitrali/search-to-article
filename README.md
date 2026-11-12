# Search to Article

A React and FastAPI app that turns ranked Google organic results into a cited article. The built-in demo runs with no API keys and uses a fixed meal-prep topic and sample results.

## Local setup

Use Python 3.11+ and Node 22.12+.

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

Keep that backend terminal running. Open a **second terminal tab** (`Cmd+T` on
macOS), then run these commands from the project root:

```bash
npm --prefix frontend ci
npm --prefix frontend run dev
```

Open http://localhost:5173 and click **Run demo**. Vite proxies API traffic to FastAPI on port 8000.
Opening port 8000 directly only shows backend status; the web interface is on
port 5173.

After the first installation, restart the app with:

```bash
# Terminal 1
cd /Users/apple/Documents/search-to-article
source .venv/bin/activate
python -m uvicorn backend.main:app --reload

# Terminal 2
cd /Users/apple/Documents/search-to-article
npm --prefix frontend run dev
```

## Live mode

Set `DEMO_MODE=false` in `.env`, add both keys, and restart FastAPI. Enter a topic, optionally expand the preferences, and generate. Country and language use codes such as `US` and `en`.

| Variable | Purpose |
| --- | --- |
| `DEMO_MODE` | Defaults to `true`. |
| `SEARCH_API_URL` | Defaults to the SerpApi endpoint. Alternatives must accept SerpApi Google search parameters and return `organic_results` entries with `title`, `link`, and optional `snippet`. |
| `SEARCH_API_KEY` | Server-side search key. |
| `LLM_API_URL` | OpenAI-compatible Chat Completions endpoint with JSON-object output support. |
| `LLM_API_KEY` | Server-side generation key. |
| `LLM_MODEL` | Model ID, defaults to `gpt-4.1-mini`. |

The backend checks robots.txt and validates public destinations at each redirect and during DNS resolution. At most four pages are fetched concurrently per job. Pages with insufficient readable text retain their original search rank and fall back to snippet or unavailable status. Live generation requires three distinct reviewed texts. The backend checks citation ranks deterministically and asks the model to audit the cited evidence before returning the draft. The evidence audit is model-based. Word counting includes body headings and excludes numeric references and separately returned metadata.

## Checks

```bash
.venv/bin/python -m pytest -q
npm --prefix frontend run build
```

The built frontend is in `frontend/dist`. To preview it locally while FastAPI is running, run `npm exec -- vite preview` from the frontend directory.
