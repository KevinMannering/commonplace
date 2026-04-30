# Inbox

## What it is

The inbox is a holding tray for proposed additions to the book. It is a
queue of items awaiting judgment: notes, excerpts, summaries, candidate
entries, or other materials that may deserve a place in the library but
have not yet earned it.

Nothing in `inbox/` is part of the permanent book. The book lives in
`book/`. The inbox exists so new material can be gathered without
confusing possibility with selection.

## Why it exists

A commonplace book is only useful if it stays curated. Good material
often arrives faster than it can be judged, and some of it needs
comparison, revision, or a second look before it belongs anywhere
durable.

The inbox gives that unfinished work a proper place. It lets the
assistant-librarian bring candidates forward while preserving the
distinction between what has been proposed and what has been kept.

## How it works

Files may be written here by the `commonplace` CLI, and later by other
tools, agents, or adapters. The source does not matter; the status does.
If a file is in `inbox/`, it is under review.

After review, each item should meet one of three fates: it is accepted
into `book/`, revised and returned for further consideration, or
discarded.

## The contract

Tools and agents may add files to `inbox/`. They may interpret source
material, draft proposals, and surface possible additions.

Only a human should move something out of `inbox/` and into `book/`.
Admission to the book is an editorial act, not an automatic one.
