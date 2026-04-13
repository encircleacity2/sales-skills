---
name: playable-creative-direction
description: Design the complete interactive ad experience and all its assets, then lock it as a Creative Direction Document that gates downstream production. Use this skill between ad-research and playable-ads-maker. It owns the creative concept (visual world and theme), interaction blueprint, copy map, and full Seedream/Seedance asset briefs with prompts. The output is a single locked document that tells playable-ads-maker exactly what to build — including which Seedream stills to generate, which Seedance videos to create, and how every asset integrates into the interaction. Not a mood board, not advice, not options to explore.
---

# Playable Creative Direction

This skill sits between research and execution. Its one job is to turn upstream evidence and product facts into a locked creative specification that downstream skills can execute without creative guessing.

The output is the **Creative Direction Document**. Nothing in `playable-ads-maker` should start until this document exists and is approved by the user or explicitly waived.

## Hard Rules

Do not start this skill if the product intake gate (defined in `playable-ads-maker`) is not complete. This skill requires confirmed product details before any creative decision can be made.

Do not produce a mood board, a concept note, or a list of "directions to explore." The output must be a single locked document with decisions, not options menus.

Do not leave any visual field as "TBD" or "to be determined." Every visual decision that affects asset generation must be resolved before this document is handed off. If a decision cannot be made without missing product information, stop and ask.

Do not write Seedream or Seedance prompts before the interaction blueprint is locked. Prompts are downstream of creative decisions, not a substitute for them.

Do not recommend a `tap-transform` loop for a recommendation-led product. If the product's value depends on "finding the right match," default to `personalized-survey` or `drag-compare`.

Do not invent a visual palette that contradicts known brand rules. If brand rules are absent, derive the palette from the product's physical appearance, target context, and emotional register — not from generic ad aesthetics.

Do not produce a tap loop or generic click mechanic when no strong game idea emerges. Default to `personalized-survey` instead. A survey with meaningfully different branch content is more engaging than a weak game with no payoff.

Do not settle for a single generic qualifier question when the upstream report contains multiple actionable insights. For `personalized-survey`, `quiz-reveal`, and other recommendation-led flows, default to `2-3` well-constructed questions sourced from the strongest report insights. Each question must be diagnostic, not filler.

Do not ship a playable where the user has no reason to participate. Every playable must offer at least one of: self-discovery, control fantasy, curiosity reveal, or comparison tension. If the concept offers none of these, reject it and redesign.

For problem-solving products (skincare, cleaning, health, wellness), evaluate `problem-build-solve` before any other archetype. Having the user construct their own problem state creates personal investment that `personalized-survey` alone cannot match. The transformation from user-built problem to product-solved result is the strongest emotional beat available in a short-form ad.

Do not plan a `problem-build-solve` playable without a Seedance transformation clip at the product activation moment. A static image swap at the payoff moment is a missed opportunity. The transformation video is what makes the emotional beat land.

Do not open directly on the interactive screen when the brief allows a video-led structure. Default to a `5-6s` embedded Seedance video lead-in first, then hand off into the interactive page. The opening video should establish scene, product, and emotional promise before the user is asked to act.

Do not use Seedream to generate UI elements, buttons, text cards, layout frames, or any element that is part of the interactive interface. Seedream generates scenes and products only. All UI elements are `code-ui`.

Do not mark an asset as `generation_mode: reference` without confirming that a reference photo exists. If the reference photo is missing and the asset requires the real product to be recognizable, stop and ask for the photo. Do not generate a generic substitute.

## Inputs Required

Before producing the Creative Direction Document, confirm these are available:

From `ad-research`:
- audience pain points and behavioral signals
- competitor hook patterns and visual conventions
- trend signals relevant to the category
- creative implications or recommended hooks from the research brief

From product intake:
- product name, category, and core selling points
- proof points for those selling points
- product visuals or explicit permission to use a generic substitute
- brand color, logo, or visual identity rules when available
- CTA destination or explicit demo-only declaration

If any of these are missing, ask before proceeding. Do not silently downgrade the brief.

## Output: Creative Direction Document

The Creative Direction Document is the only valid output of this skill. It must be complete, locked, and explicitly approved before handoff to `playable-ads-maker`.

Read [references/04-creative-direction-document.md](references/04-creative-direction-document.md) for the required sections and field-by-field rules.

At minimum the document must contain:
- Creative Thesis
- Research-to-Decision Summary (research signals → specific creative decisions)
- Creative Concept (scene, visual theme, hero moment, Seedance motion strategy, Seedream asset strategy)
- Visual Direction (palette with hex values, typography scale, motion register, mood, reference aesthetics)
- Interaction Blueprint (archetype, branch map, screen-by-screen flow with asset references)
- Copy Map (every text element per screen and per result branch, resolved to final wording)
- Asset Brief (every Seedream still and Seedance video with full prompts and consistency constraints)
- Implementation Contract (all decisions for `playable-ads-maker` — numeric values, no ambiguity)

## Position In The Pipeline

```
ad-research
    ↓ research brief with audience, competitor, trend signals
playable-creative-direction   ← this skill
    ↓ Creative Direction Document (locked)
playable-ads-maker
    ↓ Creative Direction Document + product assets
seedream / seedance-2-0
    ↓ generated stills and motion assets
playable-ads-maker (HTML integration)
    ↓ runnable index.html
```

This skill does not generate assets. It writes the briefs that make generation accurate and consistent. Asset generation is owned by `seedream` and `seedance-2-0` as delegated by `playable-ads-maker`.

## Workflow

### 1. Ingest and audit inputs

Read the research brief from `ad-research` and the confirmed product intake. Before doing any creative work:

- List which research signals are strong enough to drive a creative decision.
- List which product facts are confirmed versus inferred.
- Flag any critical gaps that would force a downstream guess.
- Identify which `2-3` strongest report insights can become branching questions, and which insight each question comes from.

If the research brief has no actionable signals, say so explicitly and ask the user whether to proceed with a category-level default or wait for better research.

### 2. Extract creative implications

Do not carry raw research into creative decisions. Translate each strong signal into exactly one of:

- mechanic choice (what the user does)
- visual motif (what the user sees)
- copy angle (what the user reads)
- CTA framing (what converts)
- pacing decision (how fast things move)

Kill research signals that cannot be translated into one of these five outputs. Do not include them in the document as background color.

For recommendation-led flows, at least `2` and at most `3` of the strongest translated signals should become actual user-facing questions. Those questions should work together as a diagnostic sequence, not as isolated trivia.

Read [references/01-research-translation.md](references/01-research-translation.md) for the translation rules.

### 3. Design the creative concept

This is the generative step. Before choosing an archetype or planning assets, actively design two things: the **visual world** the user enters, and the **reason they will want to participate**.

**Part A: Visual World**

Answer these questions:
- **What is the scene?** Where does the playable take place? (office morning, home kitchen, snowy outdoor café, warm living room, etc.)
- **What is the visual theme?** Is there a seasonal, emotional, or lifestyle theme that amplifies the product's appeal? (winter coziness, summer freshness, early-morning ritual, office productivity peak)
- **What is the hero moment?** The single most visually striking frame in the playable — the image or frame that would stop a user scrolling.
- **What motion brings this world to life?** Name the Seedance assets: ambient loops, environmental effects (falling snow, steam rising, light shifting), product reveals, reward animations.
- **What Seedream stills build this world?** Name the key still images: backgrounds by scene/state, product in-context renders, branch-state variations, result cards, end-card.

**Part B: Participation Hook**

Ask: why would this user stop and participate rather than swipe past?

The answer must be one of:
- **Self-discovery**: "I'll find out something real about my situation" — skin type diagnosis, office size fit, routine match
- **Control fantasy**: "I get to configure/build something" — coffee drink builder, routine constructor
- **Curiosity reveal**: "I want to see what's underneath / after this" — before/after drag, product reveal
- **Comparison tension**: "I can see the difference for myself" — side-by-side comparison

If no participation hook emerges from the product or research, default to **self-discovery via `personalized-survey`**. A `2-3` question survey with meaningfully different branch content (different Seedream image + different Seedance clip + different copy per result) is more engaging than a weak game with no real payoff.

Read [references/05-asset-generation-planning.md](references/05-asset-generation-planning.md) for concrete asset planning patterns by theme and archetype.

Do not shortcut this step. A generic gradient background with a product photo is not a creative concept. A winter-morning office scene with snow falling past the window, machine centered on the counter, warm amber light, and a quiz that tells the user which machine fits their team size — that is a creative concept with both a visual world and a participation hook.

### 4. Choose and justify the interaction archetype

Select one archetype from [references/03-interaction-blueprint.md](references/03-interaction-blueprint.md) after the creative concept is defined.

The archetype must fit both the product's value story and the visual world established in step 3. A winter-themed coffee machine ad in a cozy scene may use `quiz-reveal` ("find the right setup for your office size") with snowy state variations per answer branch.

Justify the choice in one sentence. Lock it.

If the archetype includes branching questions, lock the full `2-3` question sequence here before moving into screens, copy, or asset prompts. Every question should map back to a specific insight from the research brief.

Unless the user explicitly rejects a video opening, the first screen in the blueprint should be a Seedance-led video hook (`5-6s`) that transitions into the interactive screen. Use this duration window to stay compatible with Seedance's official duration constraints while still behaving like an ad hook. The interaction should begin only after that handoff, not under the opening video.

### 5. Define visual direction

Read [references/02-visual-design-system.md](references/02-visual-design-system.md).

The visual direction must be consistent with the creative concept designed in step 3 — not invented independently of it. If the concept is "winter morning office," the palette follows from that world: deep espresso browns, warm cream surfaces, cold blue-grey accents for the window/environment.

Produce:
- color palette (5 roles, hex values, traced to concept or brand)
- typography scale (sizes, weights, max lengths)
- motion register (energy level, timing values, easing)
- mood statement (one sentence)
- reference aesthetic (1–2 named real-world references)

### 6. Write the interaction blueprint

Screen by screen, define what the user sees and experiences at each moment. Every screen must specify:

- the visual state (which assets are visible, how the product appears)
- the interaction invite (what gesture the user is prompted to perform)
- the feedback (what changes visually, what copy changes, what state follows)

Use the format from [references/03-interaction-blueprint.md](references/03-interaction-blueprint.md).

As you write each screen, identify which assets from the creative concept (step 3) appear in it. This screen-to-asset mapping is what makes the implementation contract useful.

Every primary input must produce at least two of:
- visible state change or animation
- copy or HUD update
- branch progression or recommendation reveal

For question-led playables, design `2-3` questions total. The sequence should usually move from context or self-identification to pain point or priority to desired outcome or usage mode. Do not repeat the same dimension in multiple phrasings.

By default, the screen flow should begin as `video lead-in -> interactive screen(s) -> reward/result -> CTA/replay`. Make the opening video a distinct non-interactive beat, then hand off cleanly into the first interactive state.

### 7. Write the copy map

For every screen and state, write the actual final copy. Every text element resolved to final wording — not descriptions of what the copy should say.

- hook headline (≤8 words)
- body (≤20 words)
- question and choice labels for all `2-3` branching questions
- result or reward copy per branch (≤15 words each)
- CTA label (≤5 words)
- replay prompt (≤5 words)

### 8. Plan and brief all assets

This step translates the creative concept into a complete, generation-ready asset plan.

Read [references/05-asset-generation-planning.md](references/05-asset-generation-planning.md) before writing any prompts.

For every asset identified in steps 3 and 6:

- classify as `image` (Seedream), `video` (Seedance), `code-ui`, or `existing`
- write the creative description (what it looks like, what it communicates)
- write the full Seedream prompt or Seedance brief
- specify which screen(s) and state(s) it appears in
- specify whether it is critical for first paint or may be deferred

Minimum for a product-facing playable:
- 4–6 Seedream stills: first-screen hero, product cutout, ≥1 branch-state variation, result card, end-card
- 1–2 Seedance clips: ambient loop or reward motion (at minimum one motion asset that makes the world feel alive)

Every Seedream prompt must include the consistency constraint. Every Seedance brief must include scene, camera, duration, loop behavior, and motion description.

### 9. Write the implementation contract

Summarize every decision that `playable-ads-maker` must implement without creative interpretation:

- archetype and branch logic
- screen flow and transitions with timing
- asset-to-state mapping (which asset appears where)
- critical vs. deferred assets
- CTA wiring
- replay behavior
- mobile layout constraints

The coding step should not need to make any creative or design decisions after reading this contract.

### 10. Present and lock the document

Output the complete Creative Direction Document in one block. Ask the user to confirm, revise, or explicitly waive any section before downstream work begins.

When presenting a question-led creative direction, call out the `2-3` question sequence explicitly and explain, in one short line each, which report insight motivated each question.

Do not proceed to asset generation or HTML production until the user has confirmed the document or explicitly authorized the downstream skill to proceed without confirmation.

## What This Skill Does Not Do

- Does not generate images or video. That is owned by `seedream` and `seedance-2-0`.
- Does not write HTML, CSS, or JS. That is owned by `playable-ads-maker`.
- Does not do market research. That is owned by `ad-research`.
- Does not collect product intake. That is owned by `playable-ads-maker`.

## Output Contract

The only valid output of this skill is the Creative Direction Document described in [references/04-creative-direction-document.md](references/04-creative-direction-document.md).

Intermediate artifacts — insight lists, archetype comparisons, palette explorations — are working notes, not deliverables. Do not present them as output.

The document is locked when the user confirms it or explicitly authorizes downstream execution. A locked document does not change without user approval.