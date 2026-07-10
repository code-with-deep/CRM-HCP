#!/usr/bin/env python3
"""End-to-end API smoke tests for Healthcare CRM HCP module."""

from __future__ import annotations

import json
import sys
import time
import uuid
from dataclasses import dataclass, field

import httpx

BASE_URL = "http://localhost:8000"
USER_ID = "00000000-0000-0000-0000-000000000001"
HEADERS = {"X-User-Id": USER_ID, "Content-Type": "application/json"}


@dataclass
class TestResult:
    name: str
    passed: bool
    detail: str = ""
    ms: float = 0.0


@dataclass
class E2EReport:
    results: list[TestResult] = field(default_factory=list)

    def add(self, result: TestResult) -> None:
        self.results.append(result)
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name} ({result.ms:.0f}ms)")
        if result.detail:
            print(f"       {result.detail}")

    @property
    def ok(self) -> bool:
        return all(r.passed for r in self.results)


def _chat(client: httpx.Client, message: str, **kwargs) -> dict:
    payload = {
        "message": message,
        "user_id": USER_ID,
        "conversation_id": kwargs.get("conversation_id"),
        "current_interaction": kwargs.get("current_interaction") or {},
        "current_hcp": kwargs.get("current_hcp"),
    }
    started = time.perf_counter()
    response = client.post("/chat", json=payload, headers=HEADERS, timeout=60.0)
    elapsed = (time.perf_counter() - started) * 1000
    response.raise_for_status()
    body = response.json()
    assert body.get("success") is True, body
    data = body["data"]
    return data, elapsed


def run_e2e() -> E2EReport:
    report = E2EReport()

    with httpx.Client(base_url=BASE_URL, timeout=60.0) as client:
        # 1. Health
        try:
            started = time.perf_counter()
            health = client.get("/health", headers=HEADERS)
            elapsed = (time.perf_counter() - started) * 1000
            health.raise_for_status()
            data = health.json()["data"]
            db_ok = data.get("database") in {"connected", "healthy"} and data.get("status") == "healthy"
            report.add(
                TestResult(
                    "Health check + DB",
                    db_ok,
                    f"status={data.get('status')}",
                    elapsed,
                ),
            )
        except Exception as exc:
            report.add(TestResult("Health check + DB", False, str(exc)))

        # 2. Application info
        try:
            started = time.perf_counter()
            info = client.get("/", headers=HEADERS)
            elapsed = (time.perf_counter() - started) * 1000
            info.raise_for_status()
            report.add(
                TestResult(
                    "Application metadata",
                    info.json().get("success") is True,
                    info.json()["data"].get("name", ""),
                    elapsed,
                ),
            )
        except Exception as exc:
            report.add(TestResult("Application metadata", False, str(exc)))

        conversation_id: str | None = None
        draft: dict = {}

        # 3. Log interaction (dental - local planner path)
        try:
            data, elapsed = _chat(
                client,
                "i meet Dr. Aman abou the dentail and teet issue",
            )
            conversation_id = data["conversation_id"]
            draft = data.get("interaction_draft") or {}
            hcp_ok = "aman" in (draft.get("hcp_name") or "").lower()
            topics = draft.get("topics_discussed") or []
            topics_ok = any("dental" in t.lower() or "teeth" in t.lower() for t in topics)
            no_cardio = not any("cardio" in t.lower() for t in topics)
            report.add(
                TestResult(
                    "Log interaction (Dr Aman dental)",
                    hcp_ok and topics_ok and no_cardio,
                    f"hcp={draft.get('hcp_name')}, topics={topics}, tool={data.get('selected_tool')}",
                    elapsed,
                ),
            )
        except Exception as exc:
            report.add(TestResult("Log interaction (Dr Aman dental)", False, str(exc)))

        # 4. Follow-up continuation (same doctor)
        try:
            data, elapsed = _chat(
                client,
                "he told me to meet agin on next monday",
                conversation_id=conversation_id,
                current_interaction=draft,
            )
            draft = data.get("interaction_draft") or draft
            follow_up = draft.get("follow_up_actions") or ""
            hcp_still = "aman" in (draft.get("hcp_name") or "").lower()
            follow_ok = bool(follow_up) and ("monday" in follow_up.lower() or "follow" in follow_up.lower())
            report.add(
                TestResult(
                    "Follow-up continuation (same HCP)",
                    hcp_still and follow_ok,
                    f"hcp={draft.get('hcp_name')}, follow_up={follow_up[:80]}",
                    elapsed,
                ),
            )
        except Exception as exc:
            report.add(TestResult("Follow-up continuation (same HCP)", False, str(exc)))

        # 5. New doctor replaces draft
        try:
            data, elapsed = _chat(
                client,
                "i meet Dr. Deep regarding the stomach pain he was neutral",
                conversation_id=conversation_id,
                current_interaction=draft,
            )
            draft = data.get("interaction_draft") or {}
            hcp_ok = "deep" in (draft.get("hcp_name") or "").lower()
            topics = draft.get("topics_discussed") or []
            stomach_ok = any("stomach" in t.lower() for t in topics)
            no_aman = "aman" not in (draft.get("hcp_name") or "").lower()
            report.add(
                TestResult(
                    "New log replaces draft (Dr Deep)",
                    hcp_ok and stomach_ok and no_aman,
                    f"hcp={draft.get('hcp_name')}, topics={topics}",
                    elapsed,
                ),
            )
            conversation_id = data["conversation_id"]
        except Exception as exc:
            report.add(TestResult("New log replaces draft (Dr Deep)", False, str(exc)))

        # 6. Session restore
        if conversation_id:
            try:
                started = time.perf_counter()
                session = client.get(
                    f"/chat/session/{conversation_id}",
                    params={"user_id": USER_ID},
                    headers=HEADERS,
                )
                elapsed = (time.perf_counter() - started) * 1000
                session.raise_for_status()
                restored = session.json()["data"]
                hcp_ok = "deep" in (restored.get("interaction_draft", {}).get("hcp_name") or "").lower()
                history_ok = len(restored.get("conversation_history") or []) >= 2
                report.add(
                    TestResult(
                        "Session restore API",
                        hcp_ok and history_ok,
                        f"messages={len(restored.get('conversation_history') or [])}",
                        elapsed,
                    ),
                )
            except Exception as exc:
                report.add(TestResult("Session restore API", False, str(exc)))

        # 7. HCP search
        try:
            started = time.perf_counter()
            search = client.get(
                "/hcp/search",
                params={"doctor_name": "Sharma"},
                headers=HEADERS,
            )
            elapsed = (time.perf_counter() - started) * 1000
            search.raise_for_status()
            items = search.json()["data"]["items"]
            report.add(
                TestResult(
                    "HCP search",
                    len(items) > 0,
                    f"found={len(items)}",
                    elapsed,
                ),
            )
        except Exception as exc:
            report.add(TestResult("HCP search", False, str(exc)))

        # 8. Save interaction (seeded HCP required)
        try:
            save_draft = {
                "hcp_name": "Dr Sharma",
                "interaction_type": "Meeting",
                "interaction_date": draft.get("interaction_date") or "2026-07-10",
                "interaction_time": None,
                "attendees": [],
                "topics_discussed": ["CardioMax efficacy"],
                "materials_shared": [],
                "samples_distributed": [],
                "sentiment": "positive",
                "outcomes": None,
                "follow_up_actions": draft.get("follow_up_actions"),
                "additional_notes": None,
            }
            started = time.perf_counter()
            save = client.post(
                "/interaction/save",
                json={
                    "user_id": USER_ID,
                    "conversation_id": conversation_id,
                    "interaction_draft": save_draft,
                    "status": "completed",
                },
                headers=HEADERS,
            )
            elapsed = (time.perf_counter() - started) * 1000
            save.raise_for_status()
            saved = save.json()["data"]
            report.add(
                TestResult(
                    "Save interaction",
                    bool(saved.get("id")),
                    f"id={saved.get('id')}",
                    elapsed,
                ),
            )
        except Exception as exc:
            report.add(TestResult("Save interaction", False, str(exc)))

        # 9. Edit sentiment via chat
        try:
            data, elapsed = _chat(
                client,
                "update sentiment to positive",
                conversation_id=conversation_id,
                current_interaction=save_draft,
            )
            draft2 = data.get("interaction_draft") or {}
            report.add(
                TestResult(
                    "Edit sentiment via chat",
                    draft2.get("sentiment") == "positive",
                    f"sentiment={draft2.get('sentiment')}",
                    elapsed,
                ),
            )
        except Exception as exc:
            report.add(TestResult("Edit sentiment via chat", False, str(exc)))

    return report


if __name__ == "__main__":
    print(f"E2E smoke tests against {BASE_URL}\n")
    report = run_e2e()
    passed = sum(1 for r in report.results if r.passed)
    total = len(report.results)
    print(f"\n{'=' * 50}")
    print(f"Results: {passed}/{total} passed")
    sys.exit(0 if report.ok else 1)
