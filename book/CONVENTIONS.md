# Conventions

The rules that keep Commonplace readable as a book and queryable as a
knowledge base. Short, because the discipline matters more than the
ceremony.

## When to create a new entry vs. append to an existing one

**Create a new entry when:**
- It's a new thinker I'm studying.
- It's a new project I've built or am building.
- It's a new field or domain I'm tracking continuously.
- It's a new idea of mine I want to pressure-test and develop.

**Append to an existing entry when:**
- I've found new material (article, tutorial, conversation, realization)
  on a topic an existing entry already covers.
- A project or thinker entry needs an update reflecting new developments.
- A field-study entry needs the latest news, tools, or practices.

Every appended section gets a date header under a standing `## Additions`
section at the bottom of the entry. Appendage is visible accumulation,
not a silent edit.

## When to write a synthesis entry

When a topic in `_topics.md` reaches three to five source entries, write
a synthesis entry. It's not a meta-doc — it's a Kevin-voice piece
distilling what I actually believe about that topic now, citing the
source entries.

Synthesis entries are dated in the title (e.g.,
`Synthesis — Context Engineering (2026).md`) because beliefs evolve.
Older syntheses stay in the book as a record of how my thinking changed.

## Front-matter (required on every entry)

```yaml
***
title: <human-readable title>
kind: thinker | project-study | field-study | idea-study | synthesis
status: living | settled | archived
started: YYYY-MM-DD
updated: YYYY-MM-DD
why-kept: <one or two sentences answering why this earned a place>
topics: [topic-slug, topic-slug]
related-entries:
  - <exact title of related entry>
***
```

The `why-kept` field is the most important. If I can't write it
honestly, the entry doesn't belong.

## Cross-referencing between entries

When one entry's argument leans on another, link inline at the point of
the connection — not in a "see also" list at the bottom. Use the entry's
title as the link anchor:

```markdown
The decision to context-stuff Remy's full KB rather than RAG was
directly shaped by [[Karpathy — Thinking Wiki]] on context engineering.
```

This makes the book a network when read by an agent and an essay when
read by a human.

## Topics

Topics live in `_topics.md` as a controlled vocabulary. Add a new topic
only when at least two entries would carry it. One-off themes don't
deserve a topic; they live inside the entry that needed them.

When a topic has earned synthesis (see above), the synthesis entry is
the canonical front-line answer for that topic; source entries become
depth.

## Demotion, not deletion

If an entry stops feeling worth keeping, move it to `_attic/`. The
record of having once cared is part of the library's value. Delete only
true mistakes (duplicates, accidents).

## Editorial artifacts

`_index.md` and `_topics.md` are hand-curated. Agents may propose
updates; I approve them. The taste in these files is what makes
Commonplace mine and not a generic file dump.