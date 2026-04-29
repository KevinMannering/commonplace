---
title: Building Open Claw Agents for SnoBase Knowledge Base
kind: project-study
status: living
started: 2026-04-26
updated: 2026-04-29
why-kept: Captures the reasoning, decisions, and architecture from the
  Remy build during Agent Week 2026 — single-KB-multi-agent design,
  context-stuffing over RAG, voice rules, edit-delta and post-performance
  feedback loops. The reference for any future agent project that starts
  from a knowledge base.
topics: [context-engineering, agent-architecture, knowledge-base-design, voice-capture, openclaw]
related-entries:
  - OpenClaw & AI Agentic Systems — Knowledge Base
  - Persona Intelligence Agent Idea
---

# Agent Week Wiki — First Pass

## Overview

This wiki is a first-pass canonical operating document built from the exported Agent Week thread. It captures the durable decisions, architecture, completed work, remaining work, and the OpenClaw debugging outcomes that are likely to matter again. It intentionally compresses back-and-forth discussion into decisions and resolved learnings rather than preserving the full conversational sequence.[cite:122]

## What Agent Week Became

Agent Week started as a plan to build GTM agents for sales and marketing workflows, initially centered on measurable demo-booking outcomes and a stack including HubSpot, Apollo, Granola/Gemini notes, Canva, Descript, OpenClaw, Perplexity Enterprise Max, Mixpanel, and Google Analytics.[cite:122] Over the course of the thread, the strategy evolved away from immediately wiring many execution agents and toward building a small number of tightly scoped agents on top of a strong shared knowledge base, because the quality of downstream outputs was judged to depend more on source knowledge quality than on orchestration complexity.[cite:122]

## Core Philosophy

### Product thesis

The central architectural decision was that the internal product should not be thought of as “a bunch of GTM automations,” but as an internal agent product whose durable advantage comes from structured, compounding knowledge: ICP truth, Kevin POV, voice-of-customer, competitor context, and current market signals.[cite:122] The working thesis became that agents are only as good as the knowledge they can read and update, so the first high-leverage work should strengthen that knowledge layer before optimizing broad execution flows.[cite:122]

### Knowledge-first over execution-first

The thread explicitly moved away from prioritizing KPI instrumentation, HubSpot/Apollo plumbing, and broad workflow automation in favor of knowledge-building loops: a voice-of-customer / ICP loop, a Kevin POV loop, and a competitor / market intelligence loop.[cite:122] Granola notes were identified as especially valuable because upcoming calls could strengthen ICP definitions, clarify forcing functions, and reveal pain severity and buying triggers in language close to the customer’s own wording.[cite:122]

### Karpathy-inspired but not raw-note-only

The conversation adopted Karpathy-style context engineering as an important influence, especially the idea of a wiki-first system and context stuffing rather than immediate RAG fragmentation for a still-manageable knowledge base.[cite:118][cite:122] But the final pressure-tested position was not “one growing pile of notes”; it was a wiki structure with raw material behind it, canonical pages in front of it, and periodic synthesis on top of it so the system compounds without turning into contradictory sludge.[cite:118][cite:119][cite:120][cite:122]

## Architectural Decisions

### Decision: one canonical SnoBase knowledge base for agents

One major decision was that the SnoBase content knowledge base already contained a large share of the ICP, POV, product, and call-note intelligence that new agents would need, so separate KBs should not be spun up prematurely for each agent.[cite:117][cite:122] The chosen principle became: one canonical KB, stuffed into context for each agent run, with agents differing by task and tool bindings rather than by owning separate knowledge silos.[cite:118][cite:122]

**Why this was chosen:**
- faster to maintain than multiple fragmented KBs[cite:122]
- edits propagate instantly to all agents on the next run[cite:122]
- better output consistency for a small enough KB[cite:118][cite:122]
- aligned with the observed quality benefits from Remy reading a coherent full bundle[cite:118][cite:122]

**What was explicitly deferred / rejected for now:**
- full RAG / chunk-retrieval as the default architecture[cite:118][cite:122]
- per-agent fragmented knowledge bases[cite:122]
- premature knowledge-layer complexity before proving value[cite:122]

### Decision: wiki-first knowledge system

The knowledge architecture evolved into a wiki-first model: raw source material lands in an inbox/raw layer, then gets distilled into maintained wiki pages and logged as changes over time.[cite:119][cite:120][cite:121][cite:122] The wiki was framed as the right mental model because it keeps durable truth legible for both humans and agents while still preserving raw context behind it.[cite:119][cite:120][cite:122]

**Why this was chosen:**
- conversation export already contained sufficient material to bootstrap a useful wiki[cite:122]
- markdown/wiki pages are easier to revise than sprawling raw notes[cite:119][cite:120]
- supports manual now, agents later[cite:121][cite:122]
- enables canonical revision rather than endless append-only accumulation[cite:120][cite:122]

### Decision: raw layer + canonical layer + synthesis layer

The pressure-tested conclusion was that pure append-heavy note accumulation was not enough for a constantly expanding KB, because it would create contradictions, freshness ambiguity, and noisy downstream retrieval.[cite:122] The recommended architecture became a three-layer system: a raw intake layer, a canonical maintained wiki layer, and a synthesis layer that answers what changed and what matters now.[cite:122]

### Decision: manual capture pipeline before full automation

The thread settled on building a manual capture pipeline first: capture, normalize, route, update wiki, and log changes.[cite:122] This was chosen because it creates a stable operating model immediately, and later each step can be agentized without changing the overall system design.[cite:122]

## Target Agent Set

The target v1 agent set shifted toward research-editor agents rather than pure execution agents.[cite:122] The recommended first set was:

| Agent | Job | Primary outputs |
|---|---|---|
| VOC / ICP Agent | Turn call notes into structured customer intelligence | ICP KB updates, pain/forcing-function updates, weekly insight deltas [cite:122] |
| POV Interviewer Agent | Capture Kevin’s thinking via Slack interviews and dictation | Kevin POV KB updates, beliefs, examples, quotable lines [cite:122] |
| Competitive Intelligence Agent | Monitor competitors and industry shifts | competitor cards, change summaries, narrative gaps [cite:122] |
| KB Synthesizer Agent | Combine KBs into useful GTM implications | weekly messaging memo, themes, positioning updates [cite:122] |

These agents were prioritized because they strengthen the shared knowledge substrate that later powers social drafting, outbound, website copy, objection handling, and demo prep.[cite:122]

## Sequence and Methods

### Initial GTM planning sequence

A detailed Day 1 content-planning process was completed before the reset. The sequence moved through defining ICPs, mining call notes, mapping pain themes to channels, building a Week 1 content calendar, setting up a Slack approval workflow, and drafting first manual posts for LinkedIn, Instagram, and TikTok.[cite:122] This work was useful both as operating material and as evidence that high-quality outputs depend on sharper source knowledge and Kevin POV, which later reinforced the knowledge-first reset.[cite:122]

### Post-reset sequence

After the reset, the intended sequence became:
1. strengthen the shared KB / wiki[cite:122]
2. wire manual capture of new call notes, POV, and competitor/news inputs[cite:122]
3. periodically distill new material into canonical pages[cite:122]
4. synthesize what changed and what themes matter[cite:122]
5. only then let downstream execution agents consume that intelligence[cite:122]

### Tools and interfaces

OpenClaw remained the execution/orchestration layer for agents, Slack was treated as the likely human interface for prompts and reviews, Granola notes were the highest-value customer-intelligence input source, and the SnoBase content KB / BOOTSTRAP bundle was the canonical knowledge substrate behind the agent Remy.[cite:122] HubSpot and Apollo were deliberately deprioritized in the later reset, to be revisited after the knowledge system became stronger.[cite:122]

## Key GTM / Content Decisions Already Made

### ICP framework

Three primary ICPs were defined from call-note analysis: Emerging CPG Brands, Scaling / PE-backed CPG Brands, and Regional / Growing CPG Brands.[cite:122] These were differentiated by company maturity, operational pain, buying triggers, proof needs, and content angle, and several calls were used to sharpen them, including Doughy, Joon, Somos, and Hillside Harvest.[cite:122]

### Priority pain themes

Across the analyzed calls, the thread identified a recurring pain-theme set: Form Hell, Fundraising / Investor Credibility, Broker Economics, Stockout Blindness, Data Chaos, and Deduction Prevention.[cite:122] Form automation emerged as especially universal, while broker economics, stockout visibility, and fundraising credibility differentiated specific segments and added more strategic narrative angles.[cite:122]

### Channel strategy and manual content planning

LinkedIn Founder was prioritized as the highest-value channel, with LinkedIn Company, Instagram, and TikTok supporting different parts of the narrative and audience mix.[cite:122] A detailed Week 1 content calendar and Slack review workflow were sketched, but later the thread deprioritized immediate execution complexity in favor of strengthening the underlying knowledge product.[cite:122]

## OpenClaw / Remy Debugging Wiki

This section intentionally collapses long debug threads into durable bug → solution notes.

### Debug 1: basic agent invocation and first test command

**Bug / uncertainty:** The exact CLI invocation and available commands for the OpenClaw agent flow were unclear early on, so there was uncertainty around how to run and validate the first generation end to end.[cite:122]

**What ended up working:** Inspecting `openclaw agent --help`, `openclaw tui --help`, and `openclaw sessions --help` provided the exact command shape needed to run the agent and produce the first test using `openclaw agent --agent snobase-content --thinking medium --message ... --json`.[cite:122]

**Durable takeaway:** When uncertain about OpenClaw command syntax, inspect the CLI help first and derive the production command from the actual binary rather than assumptions.[cite:122]

### Debug 2: agent routing and correct agent identifier

**Bug / uncertainty:** There was risk that the route name for the SnoBase agent might be wrong or not match the configured identifier.[cite:122]

**What ended up working:** Using the exact configured agent identifier `snobase-content` resolved routing, and the fallback diagnostic was `openclaw agents list` when there was risk of an “agent not found” path.[cite:122]

**Durable takeaway:** Treat the configured agent id as canonical and verify with the agent list when route mismatch is suspected.[cite:122]

### Debug 3: provider and auth binding

**Bug / uncertainty:** There was concern that missing model-provider configuration or API keys could cause generation failure or a silent fallback.[cite:122]

**What ended up working:** The SnoBase company OpenAI key was successfully bound to Remy, and the workspace had an isolated `snobase-content` setup with persona files and the BOOTSTRAP bundle loaded.[cite:122]

**Durable takeaway:** For OpenClaw agent failures involving provider errors, confirm the agent auth profile and model-provider binding before debugging prompts or KB retrieval.[cite:122]

### Debug 4: verifying full knowledge-base access / truncation concern

**Bug / uncertainty:** There was concern that the BOOTSTRAP bundle might be getting truncated, especially for content deeper in the bundle, which would undermine source-grounded generation.[cite:122]

**What ended up working:** A direct retrieval test asked Remy two knowledge questions, one about Kevin POV 10 on brokers and distributors and one about MCB cost calculations from the deeper `in-store-promotions` material, including the wholesale/catalog price nuance.[cite:122] Remy answered both correctly, including the deeper MCB nuance, which confirmed that the full bundle was accessible and that deeper material was not being silently lost.[cite:122]

**Durable takeaway:** The best way to test bundle access is to ask for a precise fact from material deep in the bundle rather than only testing high-level content from early sections.[cite:122]

### Debug 5: autonomy vs over-scoped prompt design

**Bug / uncertainty:** The first draft prompt over-specified the grounding source by forcing Hillside Harvest as the example, which made the test less representative of how the agent should operate in practice.[cite:122]

**What ended up working:** The prompt was revised to let Remy choose the angle and source grounding from the full KB while still requiring evidence discipline and a show-your-work section.[cite:122]

**Durable takeaway:** Production-like tests should let the agent choose among valid grounded sources unless the explicit goal is to debug one constraint in isolation.[cite:122]

### Debug 6: Slack / pong timeout and default thinking level

**Bug / uncertainty:** The gateway / Slack flow produced pong-timeout noise during generation, and there was an attempt to reduce reasoning effort by setting a default thinking level in config rather than relying on CLI flags.[cite:122]

**What ended up working:** The investigation showed that the CLI `--thinking` flag exists for direct calls, GPT-5.4 supports reasoning, but OpenClaw’s config schema did not accept a `thinking` key under the tested agent/default paths despite some dry-run oddities.[cite:122] The durable conclusion was to stop pushing on the config-based fix for now, accept pong-timeout noise as mostly cosmetic unless it causes real delivery loss, and defer deeper debugging until there is actual production impact.[cite:122]

**Durable takeaway:** Use `--thinking` per CLI call when needed; do not assume a per-agent config key is supported just because a dry-run path appears to validate; and avoid spending more debugging time on reconnect noise until it affects message delivery.[cite:122]

### Debug 7: model capability inspection

**Bug / uncertainty:** There was uncertainty about whether the selected OpenAI model supported reasoning and whether the command syntax for capability inspection was correct.[cite:122]

**What ended up working:** `openclaw capability model inspect --model openai/gpt-5.4` returned model details confirming a large context window and reasoning support.[cite:122]

**Durable takeaway:** Use capability inspection to verify model features before blaming routing or prompt behavior for reasoning-related output differences.[cite:122]

### Debug 8: end-state confirmation

**Resolved end state:** By the end of the debug sequence, the thread concluded that gateway pairing was functional, the full bundle was loading, the persona files were being applied, source-grounding behavior was working, and Remy had already produced at least one publishable draft.[cite:122] The main remaining infrastructure item at that moment was Slack integration / routing for content review, not core model or KB functionality.[cite:122]

## What Was Completed

### Strategy and content planning completed

The following planning work was completed in the thread:
- definition of three ICPs[cite:122]
- mining multiple call notes into a voice-of-customer language library[cite:122]
- identification and prioritization of pain themes[cite:122]
- mapping themes to channels[cite:122]
- building a detailed Week 1 content plan[cite:122]
- designing a Slack-based content approval workflow[cite:122]
- drafting first manual founder posts[cite:122]

### Agent / KB groundwork completed

The following technical / architectural work was completed:
- OpenClaw agent skeleton and auth setup for `snobase-content`[cite:122]
- BOOTSTRAP knowledge base bundle loaded with 12 files and roughly 92K characters[cite:122]
- Remy persona files configured: identity, soul, and user[cite:122]
- gateway pairing functional[cite:122]
- full-bundle knowledge access verified with direct retrieval tests[cite:122]
- conclusion reached that one canonical KB should back multiple agents for now[cite:118][cite:122]
- knowledge-first reset and wiki-first architectural direction established[cite:122]

### Decision clarity completed

The thread also completed several important meta-decisions:
- deprioritize KPI-first thinking for now[cite:122]
- deprioritize HubSpot / Apollo wiring for the moment[cite:122]
- focus next on strengthening the knowledge base / wiki and capture pipeline[cite:122]
- stay manual for the near term while wiring the operating model[cite:122]

## What Remains To Be Completed

### Immediate next work

The most clearly implied next steps after the export are:
- build the first-pass wiki from the conversation export[cite:122]
- wire the manual capture pipeline for new information[cite:122]
- define the update cadence for pushing conversation deltas into the wiki[cite:122]
- continue using the wiki as the canonical source while new calls, POV, and competitor updates arrive[cite:122]

### Knowledge work not yet complete

The following areas were identified but not yet fully operationalized:
- structured POV interview loop in Slack[cite:122]
- systematic competitor / industry-intelligence capture into the KB[cite:122]
- ongoing weekly synthesis memos that turn raw updates into narrative / GTM direction[cite:122]
- stable canonical page structure for all major wiki domains[cite:122]
- explicit change-log discipline around updates to canonical pages[cite:122]

### Automation work not yet complete

The following execution-layer items were explicitly deferred or left incomplete:
- full Slack integration for draft routing and review[cite:122]
- more robust social-content agentization beyond CLI/manual flow[cite:122]
- HubSpot and Apollo integration work[cite:122]
- broader GTM execution agents consuming the strengthened KB[cite:122]

## Current Recommended Operating Model

### Manual now, agentized later

The current best-fit operating model is manual-first: use the thread export and future deltas as raw material, maintain a wiki of canonical pages, and update it incrementally every few hours or at meaningful checkpoints rather than rebuilding it from scratch each time.[cite:122] This was judged feasible specifically because the conversation itself already contains enough high-quality material to seed the initial wiki, and because periodic incremental updates are simpler and more robust than full recomputation on each pass.[cite:122]

### Update loop

The recommended loop is:
1. capture new conversation / call / POV / competitor inputs[cite:122]
2. treat them as raw sources, not the wiki itself[cite:122]
3. revise canonical wiki pages[cite:122]
4. log what changed[cite:122]
5. periodically synthesize implications for future agents and GTM work[cite:122]

## Great by Friday

By the end of the week, the internal product was expected to be able to answer questions like: what forcing functions matter by ICP, which pains are most severe, what language prospects actually use, what Kevin really believes about brokers and internal sales, what competitors are claiming, where narrative whitespace exists, and what Kevin should talk about next.[cite:122] This was framed as the true unlock because once that layer works, social, outbound, web copy, and demo prep can become downstream consumers of a much smarter system.[cite:122]

## Recommended Next Wiki Pages

If this first-pass document is split into a proper wiki, the next most useful pages would be:
- `strategy/agent-product-architecture.md`
- `strategy/wiki-first-kb.md`
- `operations/manual-capture-pipeline.md`
- `operations/openclaw-debugging.md`
- `icp/icp-summary.md`
- `themes/pain-themes.md`
- `agents/remy-setup.md`
- `log/changes.md`

These would turn this first-pass overview into a more navigable, multi-page wiki structure.[cite:122]
