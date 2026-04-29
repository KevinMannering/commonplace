# Commonplace — The Book

This folder is the heart of Commonplace: the book itself. Everything else
in this repo (the ingestion app, the extension, the server) exists to serve
what lives here.

## What this is

In a Victorian gentleman's library, a commonplace book was a personal
notebook for collecting and organizing things worth remembering. Not a
diary — a diary records what happened to me. A commonplace book records
what I found worth keeping.

It served several roles at once:

- **Memory aid** — preserving passages from books, lectures, newspapers,
  and correspondence.
- **Self-cultivation** — evidence of reading, taste, and intellectual
  discipline.
- **Conversation fuel** — quotes, anecdotes, and arguments retrievable for
  letters, essays, speeches, drawing-room conversation.
- **Personal index of thought** — arranged by topic so the owner could
  return to ideas by theme rather than by source.

A good way to think of it: the commonplace book was the Victorian
gentleman's personal knowledge base, built by hand.

This is mine, built in markdown.

## What's different about this one

The Victorian commonplace book optimized for retrieval by browsing — the
owner thumbed through pages and let serendipity do the connecting work.
This one needs to also retrieve well by query, both for me searching and
for agents stuffing or RAG-ing the contents.

That puts a few extra demands on the structure that a Victorian wouldn't
have needed:

1. **Topics are first-class.** A controlled vocabulary in `_topics.md`
   tells me (and any agent) which entries cover which themes.
2. **Entries grow by appending, not multiplying.** New material on an
   existing topic extends the relevant entry rather than spawning a new
   one. This keeps the book from devolving into eighty thin fragments.
3. **Cross-references are inline.** When one entry's argument depends on
   another's, they link directly so a single retrieval pulls a coherent
   network.
4. **Synthesis entries appear when a topic earns one.** Once a theme has
   accumulated three to five source entries, a synthesis entry distills
   what I currently believe — dated, because beliefs change.

The discipline that holds it all together: every entry answers *why I
kept it*. The `why-kept` field in each entry's front-matter is the
Victorian move, made explicit. If I can't write a sentence answering it,
the entry doesn't belong.

## How to use this folder

- `_index.md` — annotated table of contents, grouped by kind. Start here
  when browsing.
- `_topics.md` — controlled vocabulary of topics, with which entries
  cover each. Start here when querying.
- `CONVENTIONS.md` — the rules that keep the book coherent: when to
  append vs. create new, how to cross-reference, when to synthesize.
- `entries/` — the entries themselves, flat. One file per entry.
- `_attic/` — entries I've outgrown but don't want to delete. The fact
  that I once cared is itself information.

## A note for future me, or any agent reading this

This is a curated library, not a dump. If something here doesn't seem
worth keeping anymore, demote it to `_attic/` rather than deleting it —
its presence in the past is part of the record. If something is missing,
the question to ask before adding it is the Victorian one: *will future
me be glad this was kept?*