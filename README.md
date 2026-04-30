# Commonplace

Commonplace is a modern commonplace book: a personal library of things worth
keeping, stored in git.

It is built to hold durable knowledge rather than passing notes. The book grows
by selection: source material is gathered, judged in context, and either kept or
left aside.

## What it is

A commonplace book is a record of what is worth keeping.

Unlike a journal, which records what happened, Commonplace is meant to preserve
ideas, frameworks, observations, and bodies of knowledge that remain useful over
time. This repository contains both the library itself and the small CLI that
helps draft new additions to it.

## Structure

```text
commonplace/
├── README.md
├── pyproject.toml
├── .gitignore
├── book/
├── inbox/
└── commonplace/
```

`book/` is the curated library itself. It holds the entries that have already
been judged worth keeping.

`inbox/` is the holding tray. It contains proposals awaiting judgment. Nothing
there is part of the permanent book yet.

`commonplace/` is the ingestion CLI package. It reads source files, compares
them against lightweight context from the existing book, and drafts a proposal
for review.

## Workflow

V1 works in four steps:

1. Ingest a markdown, text, or PDF source file.
2. Extract its text and compare it against the existing book.
3. Generate a structured proposal for a new entry, an addition to an existing
   entry, or a case that should be flagged for judgment.
4. Render that proposal into markdown and write it into `inbox/`.

From there, review stays human. A proposal is accepted into `book/`, revised, or
discarded.

## Usage

The CLI currently exposes one command:

```bash
commonplace ingest <file> [-m "why this matters"] [--model <model>]
```

The command reads the source file, builds book context from `book/_index.md`,
`book/_topics.md`, and existing entry titles, then writes a proposal markdown
file into `inbox/`.

## Purpose

The aim of Commonplace is to build a lifelong, queryable library of specialized
knowledge.

It is a way of preserving what is worth returning to, connecting related ideas
over time, and letting thought compound instead of disappearing into old chats,
saved files, or scattered notes.
