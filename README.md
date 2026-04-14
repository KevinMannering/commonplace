# Commonplace

Let the Wiki Win.

Commonplace helps you keep the thinking from your best LLM conversations instead of losing it when the chat ends.

Commonplace is a CLI-first tool for turning meaningful LLM conversations into durable wiki pages.

Phase 1 only does one job:

- Take a conversation transcript as input
- Extract the important thinking with a schema matched to the session type
- Write a clean markdown page into `wiki/`

## Supported session types

- `strategy`: decisions, assumptions, challenges, open questions
- `research`: claims, evidence, sources, gaps, conclusions

Both session types also capture:

- pivots
- named concepts or frameworks

## Usage

Run from the `commonplace/` directory:

```bash
python3 -m commonplace_app.cli extract --type strategy --input ./examples/strategy-transcript.md
```

Or hand it a shared chat URL directly:

```bash
python3 -m commonplace_app.cli extract --type strategy --input "https://chatgpt.com/share/..."
```

Or pipe a transcript in:

```bash
cat transcript.txt | python3 -m commonplace_app.cli extract --type research --title "Consumer health landscape"
```

`--input` now accepts:

- a local transcript file
- a ChatGPT shared chat URL
- a Claude shared chat URL
- stdin when omitted or set to `-`

## Environment

Set an OpenAI API key before running:

```bash
export OPENAI_API_KEY=your_key_here
```

Optional:

```bash
export COMMONPLACE_MODEL=gpt-5.4
```

## Output

Generated pages are written to:

```text
./wiki/
```

Each page includes:

- frontmatter
- a concise summary
- structured sections based on session type
- wiki-style concept links like `[[Decision Journal]]`

## Development

Run tests:

```bash
python3 -m unittest discover -s tests
```
