import asyncio
import json
import logging
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from . import demo, generation, research

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
app = FastAPI(title="Search to Article")
log = logging.getLogger(__name__)


class Brief(BaseModel):
    topic: str = Field(min_length=2, max_length=180)
    country: str = Field(default="US", pattern=r"^[A-Za-z]{2}$")
    language: str = Field(default="en", pattern=r"^[A-Za-z]{2}(?:-[A-Za-z]{2})?$")
    audience: str = Field(default="", max_length=120)
    tone: str = Field(default="Clear and conversational", max_length=80)

    @field_validator("topic", "country", "language", "audience", "tone", mode="before")
    @classmethod
    def trim(cls, value):
        return value.strip() if isinstance(value, str) else value


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Backend is running. Open http://localhost:5173 for the web app.",
        "docs": "/docs",
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


def settings():
    return dict(demo=os.getenv("DEMO_MODE", "true").lower() == "true",
                search_url=os.getenv("SEARCH_API_URL", "https://serpapi.com/search.json"),
                search_key=os.getenv("SEARCH_API_KEY"),
                llm_url=os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions"),
                llm_key=os.getenv("LLM_API_KEY"), model=os.getenv("LLM_MODEL", "gpt-4.1-mini"))


@app.get("/api/config")
def config():
    return {"demo": settings()["demo"], "demo_topic": demo.TOPIC}


def event(kind, **payload):
    return json.dumps({"type": kind, **payload}, ensure_ascii=False) + "\n"


async def run(brief, options):
    stage = "search"
    yield event("stage", stage=stage)
    try:
        if not options["demo"] and not (options["search_key"] and options["llm_key"]):
            yield event("error", message="Live mode requires search and article generation API keys.")
            return
        async with httpx.AsyncClient(timeout=60, trust_env=False) as client:
            if options["demo"]:
                await asyncio.sleep(0.25)
            sources = demo.fixtures() if options["demo"] else await research.search(client, options, brief)
            stage = "review"
            yield event("stage", stage=stage)
            if options["demo"]:
                await asyncio.sleep(0.25)
            else:
                await research.review(sources)
            yield event("sources", sources=[{key: s[key] for key in ("rank", "title", "url", "status")} for s in sources])
            reviewed = [s for s in sources if s["status"] == "Reviewed"]
            if len(reviewed) < 3:
                message = ("No organic results were found. Try another topic or location." if not sources
                           else f"Insufficient sources. Only {len(reviewed)} pages could be reviewed. At least three are required.")
                yield event("error", message=message)
                return
            stage = "draft"
            yield event("stage", stage=stage)
            if options["demo"]:
                await asyncio.sleep(0.25)
                article = demo.article()
            else:
                article, data = await generation.draft(client, options, brief, sources)
            stage = "verify"
            yield event("stage", stage=stage)
            if options["demo"]:
                await asyncio.sleep(0.25)
            else:
                article = await generation.verify(client, options, article, data)
            generation.validate(article, reviewed)
            count = generation.word_count(article["body"])
            yield event("result", article=article, count=count, within_target=760 <= count <= 840)
    except httpx.HTTPStatusError as error:
        message = ("The provider is rate-limiting requests. Wait a moment and retry."
                   if error.response.status == 429 else f"The provider returned an error during {stage}. Check its configuration and retry.")
        yield event("error", message=message)
    except httpx.TimeoutException:
        yield event("error", message="A provider timed out. Please retry.")
    except Exception as error:
        log.warning("Article job failed during %s (%s)", stage, type(error).__name__)
        yield event("error", message=f"The job could not finish during {stage}. Please retry.")


@app.post("/api/articles")
def create(brief: Brief):
    return StreamingResponse(run(brief, settings()), media_type="application/x-ndjson",
                             headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})
