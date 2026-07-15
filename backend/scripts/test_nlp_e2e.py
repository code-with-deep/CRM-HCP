"""
Standalone NLP E2E test — imports only the pure Python NLP modules
(no DB, no Groq, no FastAPI needed).
"""

import sys
import os
import re
from datetime import date, timedelta

# Point directly at the source files
BACKEND = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, BACKEND)

# Patch the langgraph __init__ so it doesn't try to import DB/LLM
import types, importlib

# Stub the heavy modules so imports don't cascade
for stub in [
    "app.langgraph",
    "app.database",
    "app.database.session",
    "app.config",
    "app.config.settings",
]:
    if stub not in sys.modules:
        sys.modules[stub] = types.ModuleType(stub)

# Now load exactly the modules we want
import importlib.util

def load(rel: str):
    path = os.path.join(BACKEND, rel.replace(".", os.sep) + ".py")
    spec = importlib.util.spec_from_file_location(rel, path)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[rel] = mod
    spec.loader.exec_module(mod)
    return mod

topic_mod   = load("app.langgraph.topic_extraction")
schemas_mod = load("app.langgraph.schemas")

# Minimal state stub
class InteractionDraft:
    def __init__(self, **kw):
        self.hcp_name = kw.get("hcp_name")
        self.interaction_date = kw.get("interaction_date")
        self.topics_discussed = kw.get("topics_discussed", [])

class AgentState(dict):
    pass

def get_interaction_draft(state):
    raw = state.get("interaction_draft", {})
    if isinstance(raw, dict):
        return InteractionDraft(**raw)
    return InteractionDraft()

# Patch the state module
state_stub = types.ModuleType("app.langgraph.state")
state_stub.AgentState = AgentState
state_stub.InteractionDraft = InteractionDraft
state_stub.get_interaction_draft = get_interaction_draft
sys.modules["app.langgraph.state"] = state_stub

# Stub draft_messages
dm = types.ModuleType("app.langgraph.draft_messages")
dm.draft_log_example = lambda d: "e.g. 'I met Dr Smith today to discuss Cardio.'"
dm.draft_rate_limit_message = lambda: ""
dm.draft_retry_message = lambda: ""
sys.modules["app.langgraph.draft_messages"] = dm

planner_mod = load("app.langgraph.local_planner")

# ── Helpers ──────────────────────────────────────────────────────────────────
extract_topics_from_message = topic_mod.extract_topics_from_message
normalize_topic_phrase       = topic_mod.normalize_topic_phrase
plan_from_local_rules        = planner_mod.plan_from_local_rules
_extract_hcp_name            = planner_mod._extract_hcp_name
_infer_interaction_type      = planner_mod._infer_interaction_type
_extract_soft_sentiment      = planner_mod._extract_soft_sentiment
_extract_time                = planner_mod._extract_time
_extract_location            = planner_mod._extract_location
_extract_products            = planner_mod._extract_products
_extract_sample_with_product = planner_mod._extract_sample_with_product

TODAY = date.today().isoformat()

# ── Test runner ───────────────────────────────────────────────────────────────
results = []

def report(label, got, expected, *, note=""):
    ok = got == expected
    icon = "✅" if ok else "❌"
    results.append({"label": label, "ok": ok, "got": got, "expected": expected})
    print(f"  {icon} {label}")
    if not ok:
        print(f"       Expected: {expected!r}")
        print(f"       Got:      {got!r}")
    if note:
        print(f"       ℹ  {note}")

def section(title):
    print(f"\n{'═'*62}")
    print(f"  {title}")
    print(f"{'═'*62}")

# ─────────────────────────────────────────────────────────────────────────────
section("TEST 1 — Multi-topic extraction (CardioMax efficacy AND dosing guidelines)")

msg = "I met Dr Sharma today to discuss CardioMax efficacy and dosing guidelines."
topics = extract_topics_from_message(msg)
hcp    = _extract_hcp_name(msg)
itype  = _infer_interaction_type(msg, msg.lower())

report("HCP name",         hcp,    "Dr Sharma")
report("Interaction type", itype,  "Meeting")
report("Topic count == 2", len(topics), 2, note=f"topics={topics}")
report("Topic[0]",         topics[0] if len(topics)>0 else None, "CardioMax efficacy")
report("Topic[1]",         topics[1] if len(topics)>1 else None, "Dosing guidelines")

# ─────────────────────────────────────────────────────────────────────────────
section("TEST 2 — Face to Face + implicit POSITIVE sentiment")

msg       = "Had a face-to-face with Dr Gupta — he was very interested in our product line."
itype     = _infer_interaction_type(msg, msg.lower())
sentiment = _extract_soft_sentiment(msg)
hcp       = _extract_hcp_name(msg)
topics    = extract_topics_from_message(msg)

report("HCP name",         hcp,       "Dr Gupta")
report("Interaction type", itype,     "Face to Face")
report("Soft sentiment",   sentiment, "positive")
print(f"       ℹ  Topics: {topics}")

# ─────────────────────────────────────────────────────────────────────────────
section("TEST 3 — Phone call + implicit NEGATIVE sentiment")

msg       = "Rang up Dr Patel about the quarterly review — he wasn't very receptive."
itype     = _infer_interaction_type(msg, msg.lower())
sentiment = _extract_soft_sentiment(msg)
hcp       = _extract_hcp_name(msg)
topics    = extract_topics_from_message(msg)

report("HCP name",         hcp,       "Dr Patel")
report("Interaction type", itype,     "Call")
report("Soft sentiment",   sentiment, "negative")
print(f"       ℹ  Topics: {topics}")

# ─────────────────────────────────────────────────────────────────────────────
section("TEST 4 — Virtual meeting (Zoom)")

msg    = "Had a Zoom call with Dr Mehta today to discuss hypertension treatment options."
itype  = _infer_interaction_type(msg, msg.lower())
hcp    = _extract_hcp_name(msg)
topics = extract_topics_from_message(msg)

report("HCP name",         hcp,   "Dr Mehta")
report("Interaction type", itype, "Virtual Meeting")
report("Topic count ≥ 1",  len(topics) >= 1, True, note=f"topics={topics}")

# ─────────────────────────────────────────────────────────────────────────────
section("TEST 5 — Conference + comma-separated multi-topic")

msg    = "Attended a conference with Dr Singh and Dr Roy about cardiovascular treatment, diabetes management."
itype  = _infer_interaction_type(msg, msg.lower())
topics = extract_topics_from_message(msg)

report("Interaction type",  itype,            "Conference")
report("Topic count ≥ 2",   len(topics) >= 2, True, note=f"topics={topics}")

# ─────────────────────────────────────────────────────────────────────────────
section("TEST 6 — HCP with initials, time, and location")

msg      = "I spoke with Dr A.K. Mehta at 10:30 AM at Fortis Hospital about Lipitor dosing."
hcp      = _extract_hcp_name(msg)
t        = _extract_time(msg)
loc      = _extract_location(msg)
topics   = extract_topics_from_message(msg)
products = _extract_products(msg, topics)

report("HCP name (initials)", hcp,      "Dr A.K. Mehta")
report("Time",                t,        "10:30 AM")
report("Location",            loc,      "Fortis Hospital")
report("Products",            products, ["Lipitor"])
print(f"       ℹ  Topics: {topics}")

# ─────────────────────────────────────────────────────────────────────────────
section("TEST 7 — Typo tolerance (dentail, teet, abou)")

msg    = "I meet Dr. Aman abou the dentail and teet issue"
hcp    = _extract_hcp_name(msg)
topics = extract_topics_from_message(msg)
norm   = normalize_topic_phrase("dentail and teet issue")

report("HCP name",               hcp,    "Dr Aman")
report("Topic[0]",               topics[0] if topics else None, "Dental and teeth issues")
report("normalize_topic_phrase", norm,   "Dental and teeth issues")

# ─────────────────────────────────────────────────────────────────────────────
section("TEST 8 — Samples with named product + Face to Face (popped by)")

msg     = "Popped by to see Dr Verma — gave 3 CardioMax samples and a brochure."
itype   = _infer_interaction_type(msg, msg.lower())
hcp     = _extract_hcp_name(msg)
samples = _extract_sample_with_product(msg)

report("HCP name",         hcp,     "Dr Verma")
report("Interaction type", itype,   "Face to Face")
report("Samples",          samples, ["CardioMax x3"])

# ─────────────────────────────────────────────────────────────────────────────
section("TEST 9 — plan_from_local_rules: new log with 3 comma topics")

state = AgentState()
msg   = "I met Dr Kapoor yesterday to discuss Rosuvastatin efficacy, dosing, and patient compliance."
plan  = plan_from_local_rules(state, msg)

if plan:
    ti = plan.tool_input
    report("Tool selected",      plan.selected_tool.value,        "log_interaction")
    report("HCP name",           ti.hcp_name,                     "Dr Kapoor")
    report("Topic count ≥ 2",    len(ti.topics_discussed) >= 2,   True, note=f"topics={ti.topics_discussed}")
    print(f"       ℹ  Products: {ti.products}")
    print(f"       ℹ  Date:     {ti.interaction_date}")
else:
    report("Planner returned output", False, True)

# ─────────────────────────────────────────────────────────────────────────────
section("TEST 10 — Reschedule → date edit intent")

state = AgentState()
state["interaction_draft"] = {
    "hcp_name": "Dr Sharma",
    "interaction_date": TODAY,
    "topics_discussed": ["CardioMax"],
}
msg  = "Reschedule the meeting to next Monday."
plan = plan_from_local_rules(state, msg)

if plan:
    report("Intent",         plan.primary_intent.value,             "edit_interaction")
    report("Date extracted", bool(plan.tool_input.interaction_date), True,
           note=f"new_date={plan.tool_input.interaction_date}")
else:
    report("Planner returned output", False, True)

# ─────────────────────────────────────────────────────────────────────────────
section("TEST 11 — Generic drug name as product (Metformin, Lipitor)")

msg      = "Discussed Metformin efficacy and Lipitor dosing with Dr Joshi today."
hcp      = _extract_hcp_name(msg)
topics   = extract_topics_from_message(msg)
products = _extract_products(msg, topics)

report("HCP name",       hcp, "Dr Joshi")
report("Lipitor in products",   "Lipitor" in products or "Lipitor".lower() in [p.lower() for p in products], True,
       note=f"products={products}")
report("Metformin in products", "Metformin" in products or "metformin" in [p.lower() for p in products], True)

# ─────────────────────────────────────────────────────────────────────────────
section("TEST 12 — 'As well as' topic split")

msg    = "Spoke to Dr Roy about hypertension management as well as the new dosing protocol."
topics = extract_topics_from_message(msg)

report("Topic count ≥ 2", len(topics) >= 2, True, note=f"topics={topics}")

# ─────────────────────────────────────────────────────────────────────────────
# FINAL SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
section("FINAL SUMMARY")

passed = sum(1 for r in results if r["ok"])
failed = sum(1 for r in results if not r["ok"])
total  = len(results)

print(f"\n  Total checks : {total}")
print(f"  ✅ Passed    : {passed}")
print(f"  ❌ Failed    : {failed}")

if failed == 0:
    print("\n  🎉 ALL CHECKS PASSED — NLP improvements verified end-to-end!")
else:
    print("\n  ⚠️  Failed checks:")
    for r in results:
        if not r["ok"]:
            print(f"    • {r['label']}")
            print(f"        expected: {r['expected']!r}")
            print(f"        got:      {r['got']!r}")
print()
