---
title: Commonplace birth conversation wiki 
session_type: strategy
generated_at: 2026-04-14T03:25:25.498144+00:00
source_transcript: https://claude.ai/share/49d79bd5-a77b-4d50-989b-d5e89a98e8b8
model: gpt-5.4-2026-03-05
---

# From research-loop productization to Commonplace wiki capture

## Summary

The session began with packaging a self-critiquing research loop as a product, moved through target-market and pricing debates, then pivoted after the user judged the research output inferior to one-shot frontier-model prompting. The conversation ultimately landed on a new product direction: Commonplace, a CLI-first tool that extracts structured wiki pages from LLM conversations so users can preserve decisions, pivots, and reasoning across sessions.

## Concept Links

[[Generation-Evaluation Loop]], [[Research Infrastructure, Not Grant Writing]], [[Research Memory]], [[Session-Type Schema]], [[Commonplace]], [[Let the Wiki Win]], [[Victorian Gentleman’s Personal Library]]

## Key Decisions

### Do not be sycophantic; keep advice direct.
**Reasoning:** The user explicitly requested bluntness, setting the tone for the session.

### For the research product, the initial packaging advice was to ship to one painful recurring research workflow rather than a generic audience.
**Reasoning:** A focused user with recurring pain and willingness to pay was seen as the fastest path to a real product.

### Research firms were deprioritized as an initial market.
**Reasoning:** They were framed as likely competitors or threatened buyers who might build internally or resist headcount-reducing tools.

### VC analysts were treated as the strongest early research-product wedge, with grant writing later identified as another strong fit.
**Reasoning:** VCs had budget and clear memo workflows; grant writing had structured formats, skeptical reviewers, recurring demand, and high stakes.

### The UI for the research tool should be minimal, centered on the output and the diff/export rather than elaborate controls.
**Reasoning:** The assistant argued the 'diff' or final deliverable was the real product, while the rest was plumbing.

### Near-term defensibility for the research tool should come from distribution, data, integrations, trust, and vertical fit rather than the loop logic itself.
**Reasoning:** The assistant judged the orchestration logic easy for frontier labs to copy over time.

### For early outreach on the research product, use a polished export artifact (eventually PDF) rather than raw markdown or unhosted HTML.
**Reasoning:** A clean deliverable better matches user expectations and feels like professional work product.

### The user chose to shelve IQL Research and work on Commonplace instead.
**Reasoning:** They found the wiki/memory product more compelling and saw the research system underperforming one-shot prompting on core answer quality.

### Commonplace Phase 1 should stay CLI-first and do one job: extract structured wiki pages from transcripts.
**Reasoning:** The user shared a README that intentionally limited scope to transcript ingestion, schema-based extraction, and markdown output to wiki/.

### Commonplace should support at least two session types from the start: strategy and research.
**Reasoning:** The user believed different session types need different schemas and extraction logic.

### Commonplace is the chosen product name.
**Reasoning:** It fit the mental model of a personal library/commonplace book and felt more resonant than other naming ideas.

## Assumptions

### The research loop architecture is technically strong even if current output quality is uneven.
**Reasoning:** Both user and assistant repeatedly treated the architecture as promising while identifying evidence acquisition, summarization loss, and rigidity as bottlenecks.

### Traceability, controllability, and deliverables are meaningful advantages over one-shot prompting.
**Reasoning:** The user explicitly said the system is better on those axes even when weaker on narrative coherence.

### Frontier models will likely absorb more loop-like behavior natively over time.
**Reasoning:** This was used to argue that tech moats are weak and product defensibility must come from workflow, memory, or distribution.

### Different user groups value different things: some want elegant answers, others value auditability and source traceability.
**Reasoning:** This distinction drove the discussion of when the loop helps versus when a single prompt already suffices.

### A persistent user-owned wiki could solve context-window and session-memory problems for non-technical LLM users.
**Reasoning:** The user saw repeated forgetting in long sessions as a concrete pain point and proposed a portable memory layer as the fix.

### The schema and capture structure are the key differentiators for Commonplace.
**Reasoning:** The user argued strategy sessions, research sessions, and other conversations need distinct extraction formats and pressure tests.

### The failure of IQL Research’s brief builder on the Commonplace concept was evidence of a product mismatch rather than merely a bug.
**Reasoning:** The user interpreted the scope-definition failure as a sign that research-brief tooling was not suited to strategy-concept work.

## Challenges

### The research product often produces outputs less coherent and direct than a single well-formed ChatGPT/Claude prompt.
**Why it matters:** If the structured loop does not outperform simpler alternatives on the core answer, packaging alone will not make it a product.

### Lossy summarization across pipeline stages degrades narrative quality.
**Why it matters:** The user identified the system as 'too lossy and too rigid,' limiting its advantage except in high-auditability tasks.

### The research pipeline treats all questions similarly instead of adapting to task complexity.
**Why it matters:** This causes unnecessary friction on simple questions where a single synthesis pass may be better.

### The current research system is weak at defining scope for open-ended product concepts like Commonplace.
**Why it matters:** This revealed a mismatch between research-brief tooling and strategy-session needs.

### Defensibility is weak if the product is only 'the loop' and not tied to workflow, memory, or accumulated user context.
**Why it matters:** General-purpose frontier tools could replicate orchestration features, eroding differentiation.

### Commonplace risks becoming broad infrastructure rather than a sharply defined product.
**Why it matters:** A generic memory layer could face the same weak consumer defensibility unless narrowed by session type, schema, or use case.

## Open Questions

### Can the research system be improved enough—by reducing summarization loss and making the pipeline adaptive—to outperform one-shot prompting on the tasks that matter?
**Why open:** The user judged current output quality inadequate, but the assistant suggested targeted fixes rather than abandoning the architecture entirely.

### Which specific session type should Commonplace optimize for first: strategy, research, or another category?
**Why open:** The product direction is set broadly, but the narrowest painful first use case was not finalized.

### What extraction schema and output structure will make a Commonplace wiki page genuinely useful for resuming a session later?
**Why open:** The README defines broad categories, but the real test—whether tomorrow’s conversation can pick up from today—has not yet been validated.

### Should Commonplace remain model-agnostic, or should it favor a particular model/provider despite early OpenAI-based implementation?
**Why open:** The assistant suggested Claude might be a more natural fit, but no decision was made.

### How much of the eventual vision for Commonplace should stay out of scope in Phase 1?
**Why open:** The product idea includes compounding memory, critics, and multi-session behavior, but the user’s current implementation is intentionally narrow.

## Pivots

### Productize the existing research loop as a vertical research tool, initially for VC analysts or grant-writing workflows.
**To position:** Consider a low-cost broad writer product for Substack/bloggers focused on traceability and evidence visibility.
**Why it changed:** The user worried frontier models could copy the loop, making a vertical moat or aggressive pricing more relevant than pure workflow tech.

### Debate between cheap consumer pricing and high-dollar vertical pricing for research briefs.
**To position:** Favor vertical-first pricing and learning from serious users.
**Why it changed:** The assistant argued vertical users would provide stronger feedback, better willingness to pay, and more durable positioning than churn-prone consumer users.

### Assume the existing research system was close to product-ready if packaged better.
**To position:** Recognize the system was not yet a product because output quality was often worse than one-shot ChatGPT/Claude.
**Why it changed:** The user explicitly stated the briefs were consistently worse in coherence/directness than single-prompt answers, despite stronger traceability and controllability.

### Treat weak output mainly as a packaging/export problem.
**To position:** Diagnose it as an architectural issue: lossy summarization handoffs and excessive rigidity.
**Why it changed:** The user gave a clear diagnosis that the system wins only when structure adds more value than it destroys; the assistant then reframed the problem as compression loss and non-adaptive workflow.

### Continue focusing on IQL Research as the main product.
**To position:** Pivot to a new product, Commonplace, for capturing and reusing LLM conversation insights as a personal wiki.
**Why it changed:** The user found the memory/context-loss problem more compelling and more personally motivating than the research-brief product.

### Think of the wiki idea as generic memory infrastructure.
**To position:** Define it around session-type-specific schemas (strategy vs research) and structured extraction.
**Why it changed:** The user observed that different conversations need different capture formats and pressure tests, making schema design the product rather than generic storage.

## Named Concepts

### Generation-Evaluation Loop
**Description:** The core architecture of separating answer generation from skeptical evaluation, then refining and re-evaluating.

### Research Infrastructure, Not Grant Writing
**Description:** Positioning for grant workflows that avoids AI-authored application concerns by focusing on evidence gathering and literature support instead of writing submissions.

### Research Memory
**Description:** A writer-specific accumulating knowledge base where each research brief compounds across sessions and informs future work.

### Session-Type Schema
**Description:** The idea that strategy, research, and other conversations require different wiki extraction structures and different post-processing lenses.

### Commonplace
**Description:** The chosen product name for the new wiki-based conversation capture tool, inspired by commonplace books and a personal library metaphor.

### Let the Wiki Win
**Description:** The tagline/philosophy for Commonplace: preserve and reuse accumulated thinking instead of losing context across LLM sessions.

### Victorian Gentleman’s Personal Library
**Description:** The mental model for Commonplace: a curated, personal, cross-referenced, compounding thinking environment.
