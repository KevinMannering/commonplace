---
title: Persona Intelligence Agent Idea
kind: idea-study
status: living
started: 2026-04-20
updated: 2026-04-29
why-kept: Pressure-tested exploration of an original idea, with the
  reasoning and counterarguments preserved. Worth keeping whether or not
  I act on it — the chain of thought itself is the artifact.
topics: [agent-architecture, knowledge-base-design, voice-capture]
related-entries:
  - Building Open Claw Agents for SnoBase Knowledge Base
---

# Persona Intelligence Agent – Working Notes

## 1. Core product idea

- Build a **continuously operating persona intelligence agent**, not a one-off persona generator.  
- The agent’s job:
  - Identify a buyer.
  - Model how they **work** (role, KPIs, pains, workflows, buying power).
  - Model how they **buy** (triggers, objections, proof needed, influencers, risk/urgency).
  - Model how they **consume media** (platforms, formats, creators, tone, context).
  - Model their **commercial profile** (budget sensitivity, willingness to pay, pricing preferences, ROI expectations).
  - Generate **content + conversion paths** to reach that buyer.
  - **Update the persona over time** as new signals appear, instead of regenerating from scratch.

Personas are “living” objects that evolve like a real person’s habits and context, not static slides.

***

## 2. Multi-layer persona model

Each persona has at least four layers:

1. **Work persona**
   - Role, function, seniority.
   - KPIs and success metrics.
   - Core pains, bottlenecks, “busywork.”
   - Existing workflows and tools.
   - Buying power and how they influence decisions.

2. **Buying persona**
   - Trigger events that make them consider a solution.
   - Objections and risks.
   - Proof needed (ROI, peer case studies, benchmarks, “cost of doing nothing”).
   - Decision criteria and internal influencers.
   - Procurement friction and urgency.

3. **Media persona**
   - Platforms: LinkedIn, TikTok, YouTube, Reddit, Slack, WhatsApp, podcasts, newsletters, etc.
   - Mode of consumption: short-form scroll, saved carousels, long-form reading, commute listening, lurking in groups, etc.
   - Trusted voices: peers, operators, founders, analysts, consultants, creators, customers.
   - Content appetite: tactical “how-to,” contrarian takes, comparisons, proof, humor, templates, trend commentary.
   - Context: work vs after-hours, device, public engagement vs dark social.

4. **Commercial profile**
   - Who owns budget and rough range.
   - Budget status (planned, discretionary, frozen).
   - Willingness to pay and **price sensitivity**.
   - Preferred models (seat, usage, outcome-based, pilots).
   - Expected payback period and ROI threshold.
   - Implementation sensitivity (how much friction they’ll tolerate).

Plus a **language profile**:
- Phrases they use, search terms, tone, jargon level, message do’s/don’ts.

***

## 3. System loop and behavior

High-level loop:

1. Identify a buyer / target account.
2. Ingest signals (site, problem description, notes, future: CRM, calls, engagement).
3. Generate or update the persona (all layers above).
4. Generate:
   - Message pillars.
   - Content ideas and concrete assets.
   - Recommended channels and formats.
   - Conversion paths (attention → trust → decision → CTA).
5. Run continuously so the persona **changes slightly over time** as inputs change.

Important nuances:

- Personae are **versioned**; the system keeps history and a change log:
  - What changed.
  - Previous vs new value.
  - Evidence that caused the change.
- Continuous operation doesn’t mean huge crawls at first; “continuous” MVP = on-demand or scheduled re-scans + incremental updates.

***

## 4. MVP scope and constraints

You iterated from “big system” to a concrete **MVP that should actually work**, not just validate:

### MVP capabilities

- Input:
  - `website_url` (optional).
  - `problem_statement` (optional) – “what problem are you solving?”
  - `notes` (optional).
  - At least one of URL or problem statement must be present.

- Behavior:
  - If the website is informative, use it (home page + possibly `/about`, `/product`, `/pricing`).
  - If the website is weak/early/nonexistent, lean on the problem statement.
  - If both exist, combine them; if they conflict, preserve the ambiguity rather than faking certainty.
  - Generate an **initial persona** in the multi-layer format.
  - Persist the persona.
  - Allow re-scan / re-run later.
  - Update the persona **incrementally** (new version), not from scratch.
  - Show a diff between persona versions.
  - Generate content from the latest persona.

### MVP outputs

For each run:

1. **Company summary**
   - What the company does.
   - Who they seem to sell to.
   - Important signals from inputs.

2. **Primary persona**
   - Title and summary.
   - Work persona.
   - Buying persona.
   - Media persona.
   - Commercial profile.
   - Language profile.

3. **Content strategy**
   - ~5 content ideas.
   - ~3 recommended channels.
   - ~3 hooks.
   - 1 LinkedIn post.
   - 1 cold outbound email.
   - 1 short founder-style video script.
   - 1 suggested CTA / simple funnel.

4. **Persona history / change log**
   - Current version.
   - Previous versions.
   - What changed and why (with evidence).

### Constraints you set

- Build to **work**, not just “test if valuable.”
- Keep architecture minimal but real:
  - Simple web app (e.g., Next.js + TS, Tailwind).
  - Simple backend (could be server actions or API routes).
  - One LLM integration, structured JSON + schema validation.
  - SQLite for persistence and persona version history.
- Explicitly **no**:
  - Auth, multi-tenancy, CRM integrations, outbound/publishing, approval workflows, heavy infra.
  - Over-architecting for hypothetical scale.
- LangGraph / agent frameworks are allowed **later**, but only if they’re clearly the simplest way to get the continuous update loop—otherwise skip in MVP.

***

## 5. Prompt for your AI coding agent

You converged on a concise master spec written as a **product-first prompt** for your “technical co-founder” coding agent:

- Start by defining the product (continuously operating persona intelligence agent).
- Describe the MVP behaviors and outputs clearly.
- Treat the agent as a technical co-founder with high upside, not a task-doer.
- Avoid fluff like “very small MVP”; MVP is already minimal by definition.
- Focus on:
  - Product behavior.
  - Inputs/outputs.
  - Data to persist (companies, scan runs, persona versions, generated content).
  - Constraints and what *not* to build.
  - Clear success criteria: user can input URL/problem, generate persona, later re-scan and see incremental changes + content that feels useful.

***

If you want, I can now turn this wiki summary into a **lightweight internal doc structure** (headings/sections you can drop into your actual wiki, plus a very short “v1 build checklist”).

Sources
