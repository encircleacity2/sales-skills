#!/usr/bin/env python3
"""
BytePlus Sales Skills Evaluator
Uses Seed 2.0 Pro via the BytePlus ModelArk API (OpenAI-compatible).
Pipeline: introspect → generate tests → simulate execution → judge → score → write report
"""

import os
import json
import re
import sys
from pathlib import Path

from openai import OpenAI

ARK_API_KEY = os.environ["ARK_API_KEY"]
BASE_URL    = "https://ark.ap-southeast.bytepluses.com/api/v3"
MODEL       = "seed-2-0-pro-260328"

client = OpenAI(api_key=ARK_API_KEY, base_url=BASE_URL)

SKILL_FILE = os.environ.get("SKILL_FILE", "")
META_FILE  = os.environ.get("META_FILE", "")

BYTEPLUS_CONTEXT = """
BytePlus is a B2B technology company selling AI products:
- SeedDream: AI image generation model
- SeedAnce: AI video generation model
- Seed 2.0 Pro: flagship general-purpose large language model

Target customers: tech companies, enterprises, startups across e-commerce, gaming,
fintech, media, healthcare, logistics. Deal sizes: $50K–$2M ARR. Sales cycles: 1–6 months.
Key geographies: Southeast Asia, MENA, Europe, US.
"""

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def llm(system: str, user: str, temperature: float = 0.3) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=temperature,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
    )
    return resp.choices[0].message.content.strip()


def llm_json(system: str, user: str) -> dict | list:
    prompt = user + "\n\nRespond with ONLY valid JSON — no markdown fences, no explanation."
    raw = llm(system, prompt, temperature=0.1)
    raw = raw.strip()

    # Strip markdown code fences if present
    if "```" in raw:
        blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if blocks:
            raw = blocks[0].strip()

    # Extract the first complete JSON object or array using brace/bracket matching.
    # Prefer whichever delimiter appears first in the string so arrays aren't
    # accidentally parsed as objects (finding '{' inside '[{...}]').
    obj_idx   = raw.find('{')
    arr_idx   = raw.find('[')
    if arr_idx != -1 and (obj_idx == -1 or arr_idx < obj_idx):
        ordered = [('[', ']'), ('{', '}')]
    else:
        ordered = [('{', '}'), ('[', ']')]
    for start_char, end_char in ordered:
        idx = raw.find(start_char)
        if idx == -1:
            continue
        depth = 0
        in_string = False
        escape_next = False
        for i, ch in enumerate(raw[idx:], start=idx):
            if escape_next:
                escape_next = False
                continue
            if ch == '\\' and in_string:
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == start_char:
                depth += 1
            elif ch == end_char:
                depth -= 1
                if depth == 0:
                    raw = raw[idx:i+1]
                    break
        break

    return json.loads(raw)


# ─────────────────────────────────────────────
# Step 0: Load files
# ─────────────────────────────────────────────

def load_inputs():
    skill_path = Path(SKILL_FILE)
    meta_path  = Path(META_FILE)

    if not skill_path.exists():
        print(f"ERROR: skill file not found: {SKILL_FILE}")
        sys.exit(1)

    skill_content = skill_path.read_text(encoding="utf-8")
    meta = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

    return skill_content, meta


# ─────────────────────────────────────────────
# Step 1: Skill Introspector
# ─────────────────────────────────────────────

def introspect(skill_content: str, meta: dict) -> dict:
    print("→ Step 1: Introspecting skill...")

    system = f"""You are an expert evaluator for AI-powered sales productivity tools.
{BYTEPLUS_CONTEXT}
Analyze Claude Code skills (prompt templates / slash commands) built by sales reps."""

    user = f"""Analyze this skill file and extract its spec as JSON.

SKILL FILE:
{skill_content}

SUBMITTED RATIONALE (from the sales rep):
{meta.get('rationale', 'Not provided')}

Return a JSON object with exactly these fields:
{{
  "purpose": "one sentence — what task does this skill automate for a sales rep?",
  "category": "one of: Lead Generation | Market Research | Outreach / Email | Call Prep | Proposal Writing | Competitive Analysis | Account Research | Customer Feedback | Other",
  "required_inputs": ["list of inputs the user must provide to run this skill"],
  "expected_output": "description of what a good output from this skill looks like",
  "success_criteria": ["3-5 specific observable criteria for a high-quality output"],
  "complexity_assessment": "one of: trivial | low | medium | high",
  "complexity_reasoning": "1-2 sentences explaining the rating",
  "sales_relevance": "how directly useful is this for B2B AI product sales?",
  "ambition_score": <integer 0-20>
}}

Ambition score guide (0-20):
  0-5:   trivially simple (basic template fill-in)
  6-10:  basic but useful (single-step with some domain knowledge)
  11-15: solid (multi-step, requires reasoning or synthesis)
  16-20: impressive (complex workflow, deep domain knowledge, highly specific to sales)"""

    return llm_json(system, user)


# ─────────────────────────────────────────────
# Step 2: Test Case Generator
# ─────────────────────────────────────────────

def generate_tests(spec: dict) -> list:
    print("→ Step 2: Generating test cases...")

    system = f"""You generate realistic sales scenario test cases for evaluating AI productivity skills.
{BYTEPLUS_CONTEXT}"""

    user = f"""Generate exactly 4 diverse test cases for this skill.

SKILL SPEC:
{json.dumps(spec, indent=2)}

Vary across at least two dimensions per case:
- Industry: fintech, e-commerce, gaming, healthcare, logistics, media, SaaS
- Company size: startup (<50), mid-market (50-2000), enterprise (2000+)
- Geography: SEA (Singapore/Indonesia/Thailand), MENA (UAE/Saudi), Europe, US
- Deal stage: cold outreach, discovery, active evaluation, POC, negotiation, renewal

Difficulty distribution: cases 1-2 easy, case 3 medium, case 4 hard/edge-case.

Return a JSON array of exactly 4 objects:
[
  {{
    "id": 1,
    "scenario": "2-3 sentence description of the realistic sales scenario",
    "difficulty": "easy",
    "inputs": {{ ...key-value pairs matching the skill's required_inputs with realistic values... }},
    "what_good_looks_like": "1-2 sentences: what would an excellent skill output contain for this scenario?"
  }},
  ...
]"""

    result = llm_json(system, user)
    # Normalize: Seed 2.0 Pro sometimes returns {"1": {...}, ...} instead of [{...}]
    if isinstance(result, dict):
        result = list(result.values())
    return result


# ─────────────────────────────────────────────
# Step 3: Simulated Execution
# ─────────────────────────────────────────────

def simulate_execution(skill_content: str, test_case: dict) -> str:
    print(f"  → Simulating test case {test_case['id']} ({test_case['difficulty']})...")

    system = f"""You are simulating a Claude Code skill execution for a BytePlus sales rep.
{BYTEPLUS_CONTEXT}
Follow the skill's instructions exactly using the provided inputs.
Produce the actual output — do not describe or summarize what you would do."""

    user = f"""Execute this skill with the test inputs below.

SKILL:
{skill_content}

SCENARIO: {test_case['scenario']}

INPUTS:
{json.dumps(test_case['inputs'], indent=2)}

Produce the full skill output now."""

    return llm(system, user, temperature=0.4)


# ─────────────────────────────────────────────
# Step 4: LLM-as-Judge
# ─────────────────────────────────────────────

def judge_output(spec: dict, test_case: dict, output: str) -> dict:
    system = "You are an objective judge evaluating AI-generated sales tool outputs. Be critical — a score of 3 requires genuinely excellent output."

    user = f"""Evaluate this skill execution output.

SKILL PURPOSE: {spec['purpose']}
SUCCESS CRITERIA: {json.dumps(spec['success_criteria'])}
EXPECTED OUTPUT: {spec['expected_output']}

TEST SCENARIO: {test_case['scenario']}
WHAT GOOD LOOKS LIKE: {test_case['what_good_looks_like']}
TEST INPUTS: {json.dumps(test_case['inputs'])}

ACTUAL OUTPUT:
{output[:3000]}

Score each dimension 0-3 (0=missing, 1=partial, 2=mostly satisfies, 3=fully satisfies).

Return JSON:
{{
  "criteria_scores": [
    {{"criterion": "<text>", "score": <0-3>, "note": "brief reason"}}
  ],
  "specificity_score": <0-3>,
  "specificity_note": "tailored to these inputs, or generic boilerplate?",
  "actionability_score": <0-3>,
  "actionability_note": "could a sales rep use this directly?",
  "overall_note": "1-2 sentence summary"
}}"""

    return llm_json(system, user)


def score_test_case(judgement: dict) -> float:
    criteria_total = sum(c["score"] for c in judgement["criteria_scores"])
    criteria_max   = len(judgement["criteria_scores"]) * 3
    criteria_pct   = criteria_total / criteria_max if criteria_max > 0 else 0
    specificity_pct   = judgement["specificity_score"]   / 3
    actionability_pct = judgement["actionability_score"] / 3
    return (criteria_pct * 0.6) + (specificity_pct * 0.2) + (actionability_pct * 0.2)


# ─────────────────────────────────────────────
# Step 5: Authenticity
# ─────────────────────────────────────────────

def score_authenticity(skill_content: str, meta: dict, spec: dict) -> dict:
    print("→ Step 5: Scoring authenticity...")

    system = f"""You assess whether an AI skill was genuinely built by a sales rep for their own workflow,
vs downloaded or copied from a public template with minimal changes.
{BYTEPLUS_CONTEXT}"""

    user = f"""Assess the authenticity of this skill submission.

SKILL CONTENT:
{skill_content}

REP'S RATIONALE:
{meta.get('rationale', 'Not provided')}

EXTRACTED PURPOSE: {spec.get('purpose', '')}

Evaluate:
1. Is the rationale specific and believable (describes a real personal workflow problem)?
2. Does the skill show domain knowledge relevant to selling AI products?
3. Does it look like a generic/public template (no BytePlus context, suspiciously polished)?
4. Is there evidence the rep thought about their actual use case?

Return JSON:
{{
  "rationale_quality": <0-10>,
  "rationale_note": "is it specific and believable?",
  "domain_specificity": <0-10>,
  "domain_note": "genuine sales domain knowledge?",
  "originality_indicator": <0-10>,
  "originality_note": "original work vs downloaded template?",
  "authenticity_score": <0-30>,
  "authenticity_summary": "2-3 sentence overall assessment"
}}

Scoring guide (0-30):
  25-30: clearly original, specific rationale, strong domain knowledge
  18-24: likely original with some generic elements
  10-17: unclear — vague rationale or adapted from a template
  0-9:   appears to be a downloaded/copied template"""

    return llm_json(system, user)


# ─────────────────────────────────────────────
# Step 6: Compose Report
# ─────────────────────────────────────────────

def compose_report(spec, meta, test_cases, judgements, authenticity, final_scores) -> str:
    total         = final_scores["total"]
    tier          = final_scores["tier"]
    effectiveness = final_scores["effectiveness"]
    ambition      = final_scores["ambition"]
    auth_score    = final_scores["authenticity"]

    tier_emoji = {
        "Excellent":           "🏆",
        "Good":                "✅",
        "Borderline":          "⚠️",
        "Does not meet bar":   "❌",
    }.get(tier, "📋")

    lines = []
    lines.append("<!-- evaluation-result -->")
    lines.append(f"## {tier_emoji} Skill Evaluation Complete — {tier}")
    lines.append("")
    lines.append("| Dimension | Score | Max |")
    lines.append("|---|---|---|")
    lines.append(f"| Authenticity | **{auth_score}** | 30 |")
    lines.append(f"| Effectiveness | **{round(effectiveness)}** | 40 |")
    lines.append(f"| Skill Ambition | **{ambition}** | 20 |")
    lines.append(f"| **Total** | **{total}** | **90** |")
    lines.append("")
    lines.append(f"**Skill:** {meta.get('skillName', spec.get('purpose', ''))}  ")
    lines.append(f"**Category:** {spec.get('category', 'N/A')}  ")
    lines.append(f"**Submitted by:** {meta.get('repName', 'N/A')} ({meta.get('repEmail', '')})")
    lines.append("")

    # Authenticity
    lines.append("### Authenticity")
    lines.append(authenticity.get("authenticity_summary", ""))
    lines.append("")
    lines.append(f"- **Rationale quality:** {authenticity.get('rationale_quality', 0)}/10 — {authenticity.get('rationale_note', '')}")
    lines.append(f"- **Domain specificity:** {authenticity.get('domain_specificity', 0)}/10 — {authenticity.get('domain_note', '')}")
    lines.append(f"- **Originality:** {authenticity.get('originality_indicator', 0)}/10 — {authenticity.get('originality_note', '')}")
    lines.append("")

    # Effectiveness
    lines.append("### Effectiveness — Test Case Results")
    lines.append("")
    for tc, j in zip(test_cases, judgements):
        tc_pct = score_test_case(j)
        tc_pts = tc_pct * 10
        badge  = "🟢" if tc_pct >= 0.75 else ("🟡" if tc_pct >= 0.5 else "🔴")
        lines.append(f"**Test {tc['id']} ({tc['difficulty'].capitalize()})** {badge} `{tc_pts:.1f}/10`")
        lines.append(f"> {tc['scenario']}")
        lines.append("")
        for c in j["criteria_scores"]:
            icon = "✓" if c["score"] >= 2 else "✗"
            lines.append(f"  - {icon} **{c['criterion']}**: {c['score']}/3 — {c['note']}")
        lines.append(f"  - Specificity: {j['specificity_score']}/3 — {j['specificity_note']}")
        lines.append(f"  - Actionability: {j['actionability_score']}/3 — {j['actionability_note']}")
        lines.append(f"  - _{j['overall_note']}_")
        lines.append("")

    # Ambition
    lines.append("### Skill Ambition")
    lines.append(f"**Complexity:** {spec.get('complexity_assessment','').capitalize()} — {spec.get('complexity_reasoning','')}")
    lines.append(f"**Sales relevance:** {spec.get('sales_relevance','')}")
    lines.append("")

    # Next steps
    guidance = {
        "Excellent":         "Skill meets the bar for full bonus consideration. Ops will confirm final approval.",
        "Good":              "Strong submission. Eligible for bonus consideration pending ops review.",
        "Borderline":        "Skill shows promise but needs improvement. Ops will reach out with feedback.",
        "Does not meet bar": "Skill did not meet the minimum bar. One resubmission is allowed.",
    }
    lines.append("### Next Steps")
    lines.append(guidance.get(tier, ""))
    lines.append("")
    lines.append("---")
    lines.append("_Evaluated by BytePlus Skill Evaluator using Seed 2.0 Pro_")
    lines.append("")

    # Machine-readable JSON block — parsed by the portal webhook
    scores_json = {
        "authenticity":  auth_score,
        "effectiveness": round(effectiveness),
        "ambition":      ambition,
        "demo":          0,
        "total":         total,
        "tier":          tier,
        "breakdown": (
            authenticity.get("authenticity_summary", "") + " " +
            spec.get("complexity_reasoning", "")
        ).strip(),
    }
    lines.append("```json")
    lines.append(json.dumps(scores_json, indent=2))
    lines.append("```")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    print(f"Evaluating: {SKILL_FILE}")

    skill_content, meta = load_inputs()
    print(f"Loaded: {len(skill_content)} chars | Rep: {meta.get('repName', 'unknown')}")

    spec       = introspect(skill_content, meta)
    print(f"  Purpose:    {spec['purpose']}")
    print(f"  Complexity: {spec['complexity_assessment']} | Ambition: {spec['ambition_score']}/20")

    test_cases = generate_tests(spec)
    print(f"  Generated {len(test_cases)} test cases")

    print("→ Steps 3+4: Executing and judging...")
    judgements = []
    tc_scores  = []
    for tc in test_cases:
        output    = simulate_execution(skill_content, tc)
        judgement = judge_output(spec, tc, output)
        judgements.append(judgement)
        tc_scores.append(score_test_case(judgement))
        print(f"  Test {tc['id']}: {tc_scores[-1]*100:.0f}%")

    effectiveness_pct = sum(tc_scores) / len(tc_scores) if tc_scores else 0
    effectiveness_pts = effectiveness_pct * 40

    authenticity = score_authenticity(skill_content, meta, spec)
    auth_score   = authenticity.get("authenticity_score", 0)
    print(f"  Authenticity: {auth_score}/30")

    ambition_score = min(int(spec.get("ambition_score", 0)), 20)
    total = max(0, min(round(auth_score + effectiveness_pts + ambition_score), 90))

    tier = (
        "Excellent"         if total >= 77 else
        "Good"              if total >= 59 else
        "Borderline"        if total >= 41 else
        "Does not meet bar"
    )

    final_scores = {
        "authenticity":  auth_score,
        "effectiveness": effectiveness_pts,
        "ambition":      ambition_score,
        "total":         total,
        "tier":          tier,
    }

    print(f"\n{'='*50}")
    print(f"FINAL: {total}/90 — {tier}")
    print(f"  Auth {auth_score}/30 | Effectiveness {effectiveness_pts:.1f}/40 | Ambition {ambition_score}/20")
    print(f"{'='*50}")

    report = compose_report(spec, meta, test_cases, judgements, authenticity, final_scores)
    Path("/tmp/evaluation-results.md").write_text(report, encoding="utf-8")
    Path("/tmp/evaluation-score.txt").write_text(str(total), encoding="utf-8")
    print("Report written to /tmp/evaluation-results.md")


if __name__ == "__main__":
    main()
