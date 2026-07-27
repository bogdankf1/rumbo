"""Deterministic eval suite for the chat pipeline.

Runs against a live backend (default http://localhost:8000; override with
RUMBO_BASE_URL). Each case reseeds the demo dataset for isolation, activates
the named resume, streams one chat turn, and asserts structural properties:
set equality on skill gaps, verbatim grounding of citations, refusal events,
deterministic ranking, and router output. No LLM judges, no exact-string
comparisons on model prose.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx
import yaml

BASE_URL = os.environ.get("RUMBO_BASE_URL", "http://localhost:8000")
CASES_PATH = Path(__file__).with_name("cases.yaml")


def norm(s: str) -> str:
    return " ".join(s.split()).lower()


async def consume_chat(client: httpx.AsyncClient, message: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    async with client.stream(
        "POST", "/api/chat", json={"message": message}
    ) as resp:
        resp.raise_for_status()
        event = "message"
        async for line in resp.aiter_lines():
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                events.append((event, json.loads(line[5:])))
    return events


def get(events: list[tuple[str, dict]], name: str) -> list:
    return [data for ev, data in events if ev == name]


async def fetch_docs(client: httpx.AsyncClient) -> dict[str, str]:
    docs: dict[str, str] = {}
    for r in (await client.get("/api/resumes")).json():
        docs[r["id"]] = r["raw_text"]
    for j in (await client.get("/api/jobs")).json():
        docs[j["id"]] = j["raw_text"]
    return docs


def check(case: dict, events: list[tuple[str, dict]], docs: dict[str, str]) -> tuple[bool, str]:
    expect = case["expect"]
    kind = expect["kind"]
    errors = get(events, "error")
    if errors:
        return False, f"error event: {errors[0]['detail'][:80]}"

    if kind == "refusal":
        if not get(events, "refusal"):
            return False, "no refusal event"
        citation_frames = get(events, "citations")
        if citation_frames and citation_frames[0]:
            return False, "refusal carried citations"
        return True, "refused cleanly, no citations"

    if kind == "router":
        frames = get(events, "router")
        if not frames:
            return False, "no router event"
        r = frames[0]
        if r["intent"] != expect["intent"]:
            return False, f"intent={r['intent']} want={expect['intent']}"
        if r["job_seqs"] != expect["job_seqs"]:
            return False, f"job_seqs={r['job_seqs']} want={expect['job_seqs']}"
        return True, f"intent={r['intent']} seqs={r['job_seqs']}"

    if kind == "skill_gap":
        done = get(events, "done")
        meta = done[0]["meta"] if done else {}
        missing = sorted(meta.get("missing_required", []))
        want = sorted(expect["missing_required"])
        if missing != want:
            return False, f"missing={missing} want={want}"
        return True, f"missing={missing}"

    if kind == "ranking":
        done = get(events, "done")
        scores = (done[0]["meta"] if done else {}).get("scores", [])
        if not scores:
            return False, "no scores in done meta"
        top = max(scores, key=lambda s: s["score"])["job_seq"]
        if top != expect["top_job_seq"]:
            return False, f"top=#{top} want=#{expect['top_job_seq']}"
        return True, f"top=#{top} of {len(scores)} scored"

    if kind == "grounded":
        frames = get(events, "citations")
        citations = frames[0] if frames else []
        if not citations:
            return False, "answer carried no citations"
        for c in citations:
            raw = docs.get(c["doc_id"])
            if raw is None:
                return False, f"citation to unknown doc {c['doc_id'][:8]}"
            if norm(c["quote"]) not in norm(raw):
                return False, f"quote not in source: {c['quote'][:60]!r}"
        return True, f"{len(citations)} citations, all verbatim in sources"

    return False, f"unknown expectation kind {kind}"


async def run() -> int:
    cases = yaml.safe_load(CASES_PATH.read_text())
    results: list[tuple[str, str, bool, str]] = []
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=240) as client:
        for case in cases:
            (await client.post("/api/demo")).raise_for_status()
            resumes = (await client.get("/api/resumes")).json()
            target = next(
                r for r in resumes if r["name"] == case["active_resume"]
            )
            (
                await client.post(f"/api/resumes/{target['id']}/activate")
            ).raise_for_status()
            docs = await fetch_docs(client)
            ok, note = False, "not run"
            for attempt in range(3):
                try:
                    events = await consume_chat(client, case["question"])
                    ok, note = check(case, events, docs)
                except Exception as exc:
                    ok, note = False, f"exception: {exc}"
                # Assertion failures are final; only transient API overload
                # justifies retrying a case.
                if ok or "overloaded" not in note:
                    break
                print(f"  ....  {case['name']:34} overloaded, retrying", flush=True)
                await asyncio.sleep(15 * (attempt + 1))
            results.append((case["name"], case["expect"]["kind"], ok, note))
            status = "PASS" if ok else "FAIL"
            print(f"  {status}  {case['name']:34} {note}", flush=True)

    passed = sum(1 for _, _, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} cases passed")
    return 0 if passed == len(results) else 1


def main() -> None:
    print(f"Running evals against {BASE_URL}\n")
    sys.exit(asyncio.run(run()))


if __name__ == "__main__":
    main()
