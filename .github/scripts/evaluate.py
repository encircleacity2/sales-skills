#!/usr/bin/env python3
"""
BytePlus Sales Skills Evaluator
Pipeline: introspect → generate tests → simulate execution → judge → score → write report
"""

import os
import json
import sys
import textwrap
from pathlib import Path
from datetime import datetime

import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-opus-4-6"

SKILL_FILE = os.environ.get("SKILL_FILE", "")
META_FILE  = os.environ.get("META_FILE", "")

BYTEPLUS_CONTEXT = """
BytePlus is a B2B technology company that sells AI products including:
- SeedDream: AI image generation model
- SeedAnce: AI video generation model
- Seed: foundation LLM / language model API
- Other AI APIs and enterprise AI solutions

Target customers: tech companies, enterprises, startups across industries like
e-commerce, gaming, fintech, media, healthcare, logistics.
Typical deal sizes: $50K–$2M ARR. Sales cycles: 1–6 months.
Geographies: SEA, MENA, Europe, US.
"""

# ─────────────────────────────────────────────
# Helper: call Claude
# ─────────────────────────────────────────────

def llm(system: str, user: str, temperature: float = 0.3) -> str:
    resp = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text.strip()


def llm_json(system: str, user: str) -> dict | list:
    raw = llm(system, user + "\n\nRespond ONLY with valid JSON. No markdown fences, no explanation.", temperature=0.1)
    # Strip any accidental fences
    raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
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

    system = f"""You are an expert evaluator for AI-powered sales productivity tools at a B2B tech company.
{BYTEPLUS_CONTEXT}
Analyze submitted Claude Code skills (prompt templates / slash commands) built by sales reps."""

    user = f"""Analyze this skill file and extract its spec as JSON.

SKILL FILE:
{skill_content}

SUBMITTED RATIONALE (from the sales rep):
{meta.get('rationale', 'Not provided')}

Return JSON with exactly these fields:
{{
  "purpose": "one sentence — what task does this skill automate for a sales rep?",
  "category": "the most fitting category from: Lead Generation | Market Research | Outreach / Email | Call Prep | Proposal Writing | Competitive Analysis | Account Research | Customer Feedback | Other",
  "required_inputs": ["list", "of", "inputs", "the user must provide"],
  "expected_output": "description of what a good output from this skill looks like",
  "success_criteria": ["3-5 specific, observable criteria for a high-quality output"],
  "complexity_assessment": "trivial | low | medium | high",
  "complexity_reasoning": "1-2 sentences explaining the complexity rating",
  "sales_relevance": "how directly useful is this for B2B SaaS / AI product sales?",
  "ambition_score": <integer 0-20>
}}

For ambition_score (0-20):
- 0-5: trivially simple (reformatting, fill-in-the-blank template)
- 6-10: basic but useful (single-step task with some domain knowledge)
- 11-15: solid (multi-step, requires reasoning or data synthesis)
- 16-20: impressive (complex workflow, deep domain knowledge, highly specific to sales context)"""

    return llm_json(system, user)


# ─────────────────────────────────────────────
# Step 2: Test Case Generator
# ─────────────────────────────────────────────

def generate_tests(spec: dict) -> list[dict]:
    print("→ Step 2: Generating test cases...")

    system = f"""You are generating realistic test cases for a sales productivity skill evaluation.
{BYTEPLUS_CONTEXT}
Test cases must reflect real sales scenarios a BytePlus sales rep would encounter."""

    user = f"""Generate exactly 4 diverse test cases for this skill.

SKILL SPEC:
{json.dumps(spec, indent=2)}

Each test case must vary along at least two of these dimensions:
- Industry: fintech, e-commerce, gaming, healthcare, logistics, media, SaaS, retail
- Company size: startup (<50), mid-market (50-2000), enterprise (2000+)
- Geography: SEA (Singapore, Indonesia, Thailand), MENA (UAE, Saudi), Europe, US
- Deal stage: cold outreach, discovery, active evaluation, POC, negotiation, renewal

Test case difficulties: cases 1-2 should be straightforward, case 3 medium, case 4 should be a harder/edge case.

Return a JSON array of exactly 4 objects, each with:
{{
  "id": <1-4>,
  "scenario": "2-3 sentence description of the sales scenario",
  "difficulty": "easy | medium | hard",
  "inputs": {{ ...matches required_inputs from spec, with realistic values... }},
  "what_good_looks_like": "1-2 sentences on what an excellent output would contain for this specific scenario"
}}"""

    return llm_json(system, user)


# ─────────────────────────────────────────────
# Step 3: Simulated Execution
# ─────────────────────────────────────────────

def simulate_execution(skill_content: str, spec: dict, test_case: dict) -> str:
    print(f"  → Simulating execution for test case {test_case['id']} ({test_case['difficulty']})...")

    system = f"""You are simulating the execution of a Claude Code skill for a BytePlus sales rep.
{BYTEPLUS_CONTEXT}
Your job: follow the skill's instructions exactly, using the provided test inputs, and produce the output the skill would generate.
Be realistic — produce output as if you were the AI agent running this skill for a real sales scenario.
Do not summarize or describe the output; actually produce it."""

    user = f"""Execute this skill with the given test inputs.

SKILL CONTENT:
{skill_content}

TEST SCENARIO: {test_case['scenario']}

TEST INPUTS:
{json.dumps(test_case['inputs'], indent=2)}

Execute the skill now. Produce the full output."""

    return llm(system, user, temperature=0.4)


# ─────────────────────────────────────────────
# Step 4: LLM-as-Judge
# ─────────────────────────────────────────────

def judge_output(spec: dict, test_case: dict, execution_output: str) -> dict:
    system = """You are an expert judge evaluating AI-generated sales tool outputs.
Score objectively and critically. A score of 3 should require genuinely excellent output, not just adequate."""

    user = f"""Evaluate this skill execution output.

SKILL PURPOSE: {spec['purpose']}
SUCCESS CRITERIA:
{json.dumps(spec['success_criteria'], indent=2)}
EXPECTED OUTPUT: {spec['expected_output']}

TEST SCENARIO: {test_case['scenario']}
WHAT GOOD LOOKS LIKE FOR THIS SCENARIO: {test_case['what_good_looks_like']}
TEST INPUTS: {json.dumps(test_case['inputs'], indent=2)}

ACTUAL OUTPUT:
{execution_output[:3000]}

Score each dimension (0-3):
- 0: completely missing or wrong
- 1: partial / superficial
- 2: mostly satisfies
- 3: fully satisfies with good quality

Return JSON:
{{
  "criteria_scores": [
    {{"criterion": "<criterion text>", "score": <0-3>, "note": "brief reason"}}
  ],
  "specificity_score": <0-3>,
  "specificity_note": "is output tailored to the specific inputs or generic boilerplate?",
  "actionability_score": <0-3>,
  "actionability_note": "could a sales rep use this directly with minimal editing?",
  "overall_note": "1-2 sentence summary of this test case result"
}}"""

    return llm_json(system, user)


def score_test_case(judgement: dict, spec: dict) -> float:
    """Convert a judgement dict into a 0-1 normalized score for one test case."""
    criteria_total = sum(c["score"] for c in judgement["criteria_scores"])
    criteria_max   = len(judgement["criteria_scores"]) * 3
    criteria_pct   = criteria_total / criteria_max if criteria_max > 0 else 0

    specificity_pct   = judgement["specificity_score"]   / 3
    actionability_pct = judgement["actionability_score"] / 3

    # Weighted: 60% criteria, 20% specificity, 20% actionability
    return (criteria_pct * 0.6) + (specificity_pct * 0.2) + (actionability_pct * 0.2)


# ─────────────────────────────────────────────
# Step 5: Authenticity Scorer
# ─────────────────────────────────────────────

def score_authenticity(skill_content: str, meta: dict, spec: dict) -> dict:
    print("→ Step 5: Scoring authenticity...")

    system = f"""You are evaluating whether a submitted skill was genuinely built by a sales rep for their own workflow,
vs downloaded/copied with minimal changes from a public template.
{BYTEPLUS_CONTEXT}"""

    user = f"""Assess the authenticity of this skill submission.

SKILL CONTENT:
{skill_content}

REP'S RATIONALE (their own words — why they built it):
{meta.get('rationale', 'Not provided')}

SKILL PURPOSE (extracted): {spec.get('purpose', '')}
SKILL CATEGORY: {spec.get('category', '')}

Evaluate:
1. Does the rationale describe a specific, believable personal workflow problem? (not generic)
2. Does the skill show domain-specific knowledge relevant to selling AI products?
3. Does the skill appear to be a generic/public template (suspiciously polished, no BytePlus context, overly generic)?
4. Is there evidence the rep thought about their actual use case (specific inputs, realistic outputs, relevant examples)?

Return JSON:
{{
  "rationale_quality": <0-10>,
  "rationale_note": "is the rationale specific and believable?",
  "domain_specificity": <0-10>,
  "domain_note": "does the skill show genuine sales domain knowledge?",
  "originality_indicator": <0-10>,
  "originality_note": "does this look like original work vs a downloaded template?",
  "authenticity_score": <0-30>,
  "authenticity_summary": "2-3 sentence overall assessment"
}}

For authenticity_score (0-30):
- 25-30: clearly original, specific rationale, domain knowledge evident
- 18-24: likely original with some generic elements
- 10-17: unclear — could be adapted from template, rationale is vague
- 0-9: appears to be a downloaded/copied template with minimal customization"""

    return llm_json(system, user)


# ─────────────────────────────────────────────
# Step 6: Compose Report
# ─────────────────────────────────────────────

def compose_report(spec, meta, test_cases, judgements, authenticity, final_scores) -> str:
    total       = final_scores["total"]
    tier        = final_scores["tier"]
    effectiveness = final_scores["effectiveness"]
    ambition    = final_scores["ambition"]
    auth_score  = final_scores["authenticity"]

    tier_emoji = {"Excellent": "🏆", "Good": "✅", "Borderline": "⚠️", "Does not meet bar": "❌"}.get(tier, "📋")

    lines = []
    lines.append("<!-- evaluation-result -->")
    lines.append(f"## {tier_emoji} Skill Evaluation Results — {tier}")
    lines.append("")
    lines.append(f"| Dimension | Score | Max |")
    lines.append(f"|---|---|---|")
    lines.append(f"| Authenticity | **{auth_score}** | 30 |")
    lines.append(f"| Effectiveness | **{effectiveness:.0f}** | 40 |")
    lines.append(f"| Skill Ambition | **{ambition}** | 20 |")
    lines.append(f"| **Total** | **{total}** | **90** |")
    lines.append("")
    lines.append(f"**Skill:** {meta.get('skillName', spec.get('purpose',''))}  ")
    lines.append(f"**Category:** {spec.get('category', 'N/A')}  ")
    lines.append(f"**Submitted by:** {meta.get('repName', 'N/A')} ({meta.get('repEmail', '')})")
    lines.append("")

    # Authenticity section
    lines.append("### Authenticity")
    lines.append(authenticity.get("authenticity_summary", ""))
    lines.append("")
    lines.append(f"- **Rationale quality:** {authenticity.get('rationale_quality', 0)}/10 — {authenticity.get('rationale_note', '')}")
    lines.append(f"- **Domain specificity:** {authenticity.get('domain_specificity', 0)}/10 — {authenticity.get('domain_note', '')}")
    lines.append(f"- **Originality:** {authenticity.get('originality_indicator', 0)}/10 — {authenticity.get('originality_note', '')}")
    lines.append("")

    # Effectiveness section
    lines.append("### Effectiveness — Test Case Results")
    lines.append("")
    for i, (tc, j) in enumerate(zip(test_cases, judgements)):
        tc_score_pct = score_test_case(j, spec)
        tc_score_pts = tc_score_pct * 10  # each test case worth ~10 pts toward effectiveness
        badge = "🟢" if tc_score_pct >= 0.75 else ("🟡" if tc_score_pct >= 0.5 else "🔴")
        lines.append(f"**Test {tc['id']} ({tc['difficulty'].capitalize()})** {badge} {tc_score_pts:.1f}/10")
        lines.append(f"> {tc['scenario']}")
        lines.append("")
        for c in j["criteria_scores"]:
            star = "✓" if c["score"] >= 2 else "✗"
            lines.append(f"  - {star} {c['criterion']}: {c['score']}/3 — {c['note']}")
        lines.append(f"  - Specificity: {j['specificity_score']}/3 — {j['specificity_note']}")
        lines.append(f"  - Actionability: {j['actionability_score']}/3 — {j['actionability_note']}")
        lines.append(f"  - *{j['overall_note']}*")
        lines.append("")

    # Ambition section
    lines.append("### Skill Ambition")
    lines.append(f"**Complexity:** {spec.get('complexity_assessment', 'N/A').capitalize()} — {spec.get('complexity_reasoning', '')}")
    lines.append(f"**Sales relevance:** {spec.get('sales_relevance', '')}")
    lines.append("")

    # Tier guidance
    guidance = {
        "Excellent":           "Skill meets the bar for full bonus consideration. Ops will confirm final approval.",
        "Good":                "Strong submission. Eligible for bonus consideration pending ops review.",
        "Borderline":          "Skill shows promise but needs improvement. Ops will reach out with feedback.",
        "Does not meet bar":   "Skill did not meet the minimum bar. One resubmission is allowed with improvements.",
    }
    lines.append(f"### Next Steps")
    lines.append(guidance.get(tier, ""))
    lines.append("")

    # Machine-readable scores block (parsed by the portal webhook)
    scores_json = {
        "authenticity":  auth_score,
        "effectiveness": round(effectiveness),
        "ambition":      ambition,
        "demo":          0,
        "total":         total,
        "tier":          tier,
        "breakdown":     (
            authenticity.get("authenticity_summary", "") + " " +
            spec.get("complexity_reasoning", "") + " " +
            spec.get("sales_relevance", "")
        ).strip()
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

    # Load
    skill_content, meta = load_inputs()
    print(f"Skill loaded: {len(skill_content)} chars | Rep: {meta.get('repName', 'unknown')}")

    # Step 1: Introspect
    spec = introspect(skill_content, meta)
    print(f"  Purpose:    {spec['purpose']}")
    print(f"  Category:   {spec['category']}")
    print(f"  Complexity: {spec['complexity_assessment']}")
    print(f"  Ambition:   {spec['ambition_score']}/20")

    # Step 2: Generate tests
    test_cases = generate_tests(spec)
    print(f"  Generated {len(test_cases)} test cases")

    # Step 3 + 4: Execute + Judge each test case
    print("→ Step 3+4: Executing and judging test cases...")
    judgements = []
    tc_scores  = []
    for tc in test_cases:
        output    = simulate_execution(skill_content, spec, tc)
        judgement = judge_output(spec, tc, output)
        judgements.append(judgement)
        tc_scores.append(score_test_case(judgement, spec))
        print(f"  Test {tc['id']}: {tc_scores[-1]*100:.1f}%")

    # Effectiveness: average across test cases, scaled to 40 pts
    effectiveness_pct = sum(tc_scores) / len(tc_scores) if tc_scores else 0
    effectiveness_pts = effectiveness_pct * 40

    # Step 5: Authenticity
    authenticity = score_authenticity(skill_content, meta, spec)
    auth_score   = authenticity.get("authenticity_score", 0)
    print(f"  Authenticity: {auth_score}/30")

    # Ambition (already in spec, capped to 20)
    ambition_score = min(int(spec.get("ambition_score", 0)), 20)

    # Total (out of 90 — demo is 10, submitted separately)
    total = round(auth_score + effectiveness_pts + ambition_score)
    total = max(0, min(total, 90))

    tier = (
        "Excellent"         if total >= 77 else  # ~85% of 90
        "Good"              if total >= 59 else  # ~65% of 90
        "Borderline"        if total >= 41 else  # ~45% of 90
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
    print(f"FINAL SCORE: {total}/90 — {tier}")
    print(f"  Auth:          {auth_score}/30")
    print(f"  Effectiveness: {effectiveness_pts:.1f}/40")
    print(f"  Ambition:      {ambition_score}/20")
    print(f"{'='*50}\n")

    # Step 6: Write report
    report = compose_report(spec, meta, test_cases, judgements, authenticity, final_scores)
    Path("/tmp/evaluation-results.md").write_text(report, encoding="utf-8")
    Path("/tmp/evaluation-score.txt").write_text(str(total), encoding="utf-8")

    print("Report written to /tmp/evaluation-results.md")


if __name__ == "__main__":
    main()
