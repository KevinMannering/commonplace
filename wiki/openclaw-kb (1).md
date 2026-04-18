# OpenClaw & AI Agentic Systems — Knowledge Base

> **Purpose:** LLM-optimized reference wiki for setting up, running, and extending OpenClaw and related AI agentic systems.
> **Last updated:** 2026-04-16
> **Primary sources:** github.com/openclaw (all repos), neurometric.ai/claw, X.com bookmarks (@kevinRmannering)
> **Schema:** Karpathy wiki pattern — raw → compiled wiki → Q&A → write-back → lint

---

## Table of Contents

1. [What Is OpenClaw](#1-what-is-openclaw)
2. [GitHub Org — Repo Map](#2-github-org--repo-map)
3. [Architecture](#3-architecture)
4. [Install & Onboarding](#4-install--onboarding)
5. [Supported LLM Providers & Model Config](#5-supported-llm-providers--model-config)
6. [Supported Channels (Messaging Platforms)](#6-supported-channels-messaging-platforms)
7. [Agent Identity Files: SOUL.md, USER.md, MEMORY.md](#7-agent-identity-files-soulmd-usermd-memorymd)
8. [Skills — What They Are & How They Work](#8-skills--what-they-are--how-they-work)
9. [Plugins — Extending OpenClaw](#9-plugins--extending-openclaw)
10. [MCP Support via mcporter](#10-mcp-support-via-mcporter)
11. [Automation: Cron, Webhooks, Gmail Pub/Sub](#11-automation-cron-webhooks-gmail-pubsub)
12. [Gateway — The Control Plane](#12-gateway--the-control-plane)
13. [Security Model & DM Pairing](#13-security-model--dm-pairing)
14. [Companion Apps (macOS, iOS, Android, Windows)](#14-companion-apps-macos-ios-android-windows)
15. [Development Channels & Updating](#15-development-channels--updating)
15b. [Recent Release Notes](#15b-recent-release-notes)
16. [ClawHub — The Skill & Plugin Registry](#16-clawhub--the-skill--plugin-registry)
17. [Advanced Tools: Lobster, acpx, Ansible](#17-advanced-tools-lobster-acpx-ansible)
18. [Neurometric & ClawPack — Domain-Routing Model Layer](#18-neurometric--clawpack--domain-routing-model-layer)
19. [Core Concepts: Chat vs Agents](#19-core-concepts-chat-vs-agents)
20. [The AI Operating System (AIOS) Model](#20-the-ai-operating-system-aios-model)
21. [Context Engineering: .md File Architecture](#21-context-engineering-md-file-architecture)
22. [LLM Knowledge Base Pattern (Karpathy)](#22-llm-knowledge-base-pattern-karpathy)
23. [Autonomous Repo Agents: Code Factory Pattern](#23-autonomous-repo-agents-code-factory-pattern)
24. [Claude Token Cost Optimization](#24-claude-token-cost-optimization)
25. [Claude Cowork — Power User System](#25-claude-cowork--power-user-system)
26. [Real-World Agent Deployments](#26-real-world-agent-deployments)
27. [Critical Mistakes to Avoid (Setup)](#27-critical-mistakes-to-avoid-setup)
28. [Appendix: Key Source References](#28-appendix-key-source-references)

---

## 1. What Is OpenClaw

**OpenClaw** is an open-source, model-agnostic personal AI assistant that runs on your own devices, connects to the messaging platforms you already use, and takes autonomous action on your behalf 24/7.

> "OpenClaw is not a language model. It is an infrastructure layer — an agent wrapper that connects to any LLM the user chooses: Claude, GPT, DeepSeek, Gemini, or local models via Ollama." — Neurohive

### Core properties (from official README)
- **Model-agnostic** — any LLM via provider/model format (`anthropic/claude-opus-4-6`, `openai/gpt-5.4`, `ollama/qwen3.5`, etc.)
- **Local-first** — runs on Mac, Windows (WSL2), or Linux; your data stays on your machine
- **Any chat app** — WhatsApp, Telegram, Discord, Slack, Signal, iMessage, Teams, Matrix, and 20+ more
- **Persistent memory** — remembers you and becomes uniquely yours across sessions
- **Browser control** — full web automation via dedicated Chrome/Chromium instance
- **Full system access** — read/write files, run shell commands, execute scripts (sandboxed or elevated — your choice)
- **Skills & plugins** — extend with community skills or let the agent build its own
- **Cron + webhooks** — autonomous background tasks without human involvement
- **MIT license** — fully open source, self-hostable

### Naming history
Warelay → Clawdbot → Moltbot → **OpenClaw**
(Renamed after legal pressure from Anthropic whose product is called Claude. The rename was to Moltbot first, then OpenClaw.)

### Creator & sponsors
- Built by **Peter Steinberger (@steipete)**, Austria. Steinberger subsequently joined OpenAI; the project continues as open source.
- **Sponsors:** OpenAI, GitHub, NVIDIA, Vercel, Blacksmith, Convex

### Official links
| Resource | URL |
|----------|-----|
| Website | https://openclaw.ai |
| Docs | https://docs.openclaw.ai |
| GitHub org | https://github.com/openclaw |
| Main repo | https://github.com/openclaw/openclaw |
| Discord | https://discord.gg/clawd |
| DeepWiki | https://deepwiki.com/openclaw/openclaw |
| ClawHub (skill registry) | https://clawhub.ai |
| onlycrabs.ai (SOUL.md registry) | https://onlycrabs.ai |
| Trust & threat model | https://trust.openclaw.ai |
| Security contact | security@openclaw.ai |

### Current version
`2026.4.14` — stable release (2026-04-14)
`2026.4.15-beta.1` — beta in testing (2026-04-15); not yet stable
(versioned as `vYYYY.M.D`)

---

## 2. GitHub Org — Repo Map

> Source: github.com/openclaw — all public repos as of 2026-04-16

| Repo | Stars | Description |
|------|-------|-------------|
| [openclaw/openclaw](https://github.com/openclaw/openclaw) | 358,580 | Main runtime — TypeScript gateway + CLI + all channels |
| [openclaw/clawhub](https://github.com/openclaw/clawhub) | 8,026 | Skill & plugin registry (clawhub.ai) |
| [openclaw/skills](https://github.com/openclaw/skills) | 4,140 | Archive of all ClawHub skills (Python, for analysis) |
| [openclaw/acpx](https://github.com/openclaw/acpx) | 2,152 | Headless ACP client — agent-to-agent protocol CLI |
| [openclaw/lobster](https://github.com/openclaw/lobster) | 1,129 | Workflow shell — typed pipelines, approval gates, macros |
| [openclaw/nix-openclaw](https://github.com/openclaw/nix-openclaw) | 647 | Nix packaging for OpenClaw |
| [openclaw/openclaw-ansible](https://github.com/openclaw/openclaw-ansible) | 559 | Hardened Debian/Ubuntu auto-installer (UFW, Tailscale, Docker) |
| [openclaw/openclaw-windows-node](https://github.com/openclaw/openclaw-windows-node) | 445 | Windows companion: system tray app, shared lib, PowerToys extension |
| [openclaw/openclaw.ai](https://github.com/openclaw/openclaw.ai) | 262 | Marketing website (Astro) |
| [openclaw/clawdinators](https://github.com/openclaw/clawdinators) | 155 | Declarative NixOS infra modules for CLAWTINATOR hosts |
| [openclaw/docs](https://github.com/openclaw/docs) | 51 | Docs mirror + i18n (zh-CN, uk, pl, id, tr, it, ar, fr, de); source of truth is openclaw/openclaw |
| [openclaw/community](https://github.com/openclaw/community) | 99 | Discord server policies |
| [openclaw/trust](https://github.com/openclaw/trust) | 37 | Threat model (MITRE ATLAS framework) |
| [openclaw/casa](https://github.com/openclaw/casa) | 36 | Swift — exposing home base to OpenClaw |
| [openclaw/clawgo](https://github.com/openclaw/clawgo) | 76 | Go implementation of OpenClaw node |
| [openclaw/hermit](https://github.com/openclaw/hermit) | 32 | TypeScript (purpose unlisted) |
| [openclaw/caclawphony](https://github.com/openclaw/caclawphony) | 35 | Elixir — isolated autonomous implementation runs for teams |
| [openclaw/multipass](https://github.com/openclaw/multipass) | 22 | CLI for testing message channels against OpenClaw (Vercel Chat SDK) |
| [openclaw/flawd-bot](https://github.com/openclaw/flawd-bot) | 38 | "Clawd's evil twin, Flawd" |
| [openclaw/homebrew-tap](https://github.com/openclaw/homebrew-tap) | 38 | Homebrew tap for OpenClaw |

### Source structure of main repo
```
src/          — CLI wiring, commands, channels, routing, infra, media pipeline
skills/       — bundled skills shipped with core
extensions/   — bundled workspace plugin tree (channels, providers as plugins)
packages/     — internal packages
apps/         — macOS, iOS, Android companion apps
ui/           — Control UI (web frontend served from Gateway)
docs/         — documentation source (synced to openclaw/docs)
test/         — tests (colocated *.test.ts alongside source)
```

---

## 3. Architecture

> Source: openclaw/openclaw README, AGENTS.md, VISION.md

### High-level diagram
```
WhatsApp / Telegram / Slack / Discord / Google Chat / Signal /
iMessage / BlueBubbles / IRC / Teams / Matrix / LINE / Nostr / ...
                    │
                    ▼
    ┌───────────────────────────────┐
    │            Gateway            │
    │   (WebSocket control plane)   │
    │     ws://127.0.0.1:18789      │
    └──────────────┬────────────────┘
                   │
        ┌──────────┼──────────────┐
        │          │              │
    Pi agent    CLI (openclaw…)  WebChat UI
    (RPC mode)  macOS app        iOS / Android nodes
```

### Four core layers
| Layer | What it does |
|-------|-------------|
| **Channel adapter** | Connects to messaging platforms (WhatsApp via Baileys, Telegram via grammY, Slack via Bolt, Discord via discord.js, etc.) |
| **Agent runtime (Pi)** | Runs in RPC mode with tool streaming and block streaming. Assembles workspace files into system prompt, sends to LLM, handles tool calls. |
| **Skills system** | Bundled, managed, and workspace skills. Text-based markdown folders. |
| **Memory** | Special plugin slot (one active at a time). Persists preferences and context across sessions. |

### Key subsystems
- **Gateway WebSocket network** — single WS control plane for clients, tools, events, ops. Serves Control UI and WebChat.
- **Browser control** — OpenClaw-managed Chrome/Chromium with CDP control. Full web automation.
- **Canvas + A2UI** — agent-driven visual workspace with push/reset, eval, snapshot.
- **Voice Wake + Talk Mode** — wake words on macOS/iOS; continuous voice on Android (ElevenLabs + system TTS fallback).
- **Nodes** — canvas, camera snap/clip, screen record, `location.get`, notifications, `system.run`/`system.notify`.
- **Tailscale exposure** — Serve (tailnet-only) or Funnel (public) for remote Gateway access.
- **Session model** — `main` session for direct chats; group isolation; activation modes; queue modes; reply-back.

### How "autonomous behavior" actually works
> "Autonomous behaviour is a cron job that assembles the prompt and dispatches it." — Neurohive (quoting OpenClaw architecture docs)

The agent runtime reads workspace files, packs them into a system prompt, sends to the LLM API, and processes tool calls. There is no magic — it's a loop running on a schedule.

---

## 4. Install & Onboarding

> Source: openclaw/openclaw README

### Runtime requirement
**Node 24 (recommended) or Node 22.16+**

### Recommended install (all platforms)
```bash
npm install -g openclaw@latest
# or:
pnpm add -g openclaw@latest

openclaw onboard --install-daemon
```

`openclaw onboard` guides you step-by-step through: gateway setup, workspace, channels, and skills. It installs a launchd (macOS) or systemd (Linux) user service so the gateway stays running.

Works on **macOS, Linux, and Windows via WSL2** (WSL2 strongly recommended over bare Windows).

### Quick start commands
```bash
# Run onboarding with daemon install
openclaw onboard --install-daemon

# Start gateway manually (verbose mode)
openclaw gateway --port 18789 --verbose

# Send a message
openclaw message send --to +1234567890 --message "Hello from OpenClaw"

# Run agent directly
openclaw agent --message "Ship checklist" --thinking high

# Health check
openclaw doctor
```

### Build from source (development)
```bash
git clone https://github.com/openclaw/openclaw.git
cd openclaw
pnpm install
pnpm ui:build        # auto-installs UI deps on first run
pnpm build

pnpm openclaw onboard --install-daemon

# Dev loop with auto-reload
pnpm gateway:watch
```

### Ansible installer (Linux/Debian/Ubuntu — hardened)
```bash
curl -fsSL https://raw.githubusercontent.com/openclaw/openclaw-ansible/main/install.sh | bash
```
Installs: Tailscale VPN, UFW firewall, Fail2ban, Docker CE, Node 22.x, pnpm, OpenClaw as systemd service.
> Note: macOS bare-metal support deprecated in this installer as of 2026-02-06. Use Docker or native install on macOS.

### Nix install
```bash
# See https://github.com/openclaw/nix-openclaw
```

### Homebrew tap
```bash
# See https://github.com/openclaw/homebrew-tap
```

### Docker
See https://docs.openclaw.ai/install/docker

### After install: key CLI commands
```bash
openclaw onboard              # interactive setup wizard
openclaw doctor               # diagnose config, surface risky DM policies
openclaw update --channel stable|beta|dev   # switch release channels
openclaw channels status --probe            # check channel connectivity
openclaw pairing approve <channel> <code>   # approve a new DM sender
openclaw config set ...       # set config values
openclaw providers login      # authenticate LLM provider
```

---

## 5. Supported LLM Providers & Model Config

> Source: openclaw/openclaw README, VISION.md; lumadock.com; skywork.ai

OpenClaw is **fully model-agnostic**. It has no built-in model weights. Uses a `provider/model` format:
- `anthropic/claude-opus-4-6`
- `openai/gpt-5.4`
- `ollama/qwen3.5`
- `lmstudio/minimax-m2.1-gs32`

### Supported cloud providers
| Provider | Example models | Auth method | Notes |
|----------|---------------|-------------|-------|
| **Anthropic** (Claude) | claude-opus-4-6, claude-sonnet | OAuth token (from `claude setup-token`) or API key | Use membership token, NOT pay-per-use console API |
| **OpenAI** | gpt-5.4, gpt-4o, codex | Codex OAuth (ChatGPT Plus) or API key | Codex OAuth gives generous limits from Plus subscription |
| **Google** | gemini-2-flash, gemini-pro | API key | Multimodal, long context |
| **xAI** | grok | API key | Real-time knowledge |
| **MiniMax** | m2.5 | API key | Community favorite for background/heartbeat tasks |
| **Moonshot AI** | kimi-k2.5 | API key | Efficient for routine tasks |
| **Mistral** | mistral-large, mixtral | API key | EU-based models |
| **OpenRouter** | 100+ models via one key | API key | Supports `:free` suffix for free-tier models |

### Local / free providers (zero API cost)
| Provider | Setup | Notes |
|----------|-------|-------|
| **Ollama** | `ollama run qwen3.5` | Auto-detected at `http://127.0.0.1:11434/v1`. Community recommends Qwen 3.5. Free forever. |
| **LM Studio** | Run LM Studio, point to `http://localhost:1234/v1` | Any model LM Studio supports |
| **vLLM / LiteLLM / llama.cpp** | Any OpenAI-compatible runtime | Configure via `models.providers` with custom `baseUrl` |

### Model config format
```json
{
  "agents": {
    "defaults": {
      "model": { "primary": "anthropic/claude-opus-4-6" },
      "models": {
        "anthropic/claude-opus-4-6": { "alias": "Claude" },
        "ollama/qwen3.5": { "alias": "LocalFast" }
      }
    }
  },
  "models": {
    "providers": {
      "lmstudio": {
        "baseUrl": "http://localhost:1234/v1",
        "apiKey": "LMSTUDIO_KEY",
        "api": "openai-completions",
        "models": [
          {
            "id": "minimax-m2.1-gs32",
            "name": "MiniMax M2.1",
            "contextWindow": 200000,
            "maxTokens": 8192,
            "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 }
          }
        ]
      }
    }
  }
}
```

### CLI model management
```bash
openclaw onboard              # initial auth and provider setup
openclaw models list          # see all available providers/models
openclaw models set provider/model    # switch model without editing config
```

### Multi-model routing (cost optimization)
Assign expensive models to complex reasoning; cheap/local models to heartbeats and background tasks. Reduces costs up to 95%.

### Model failover
See https://docs.openclaw.ai/concepts/model-failover — auth profile rotation (OAuth vs API keys) + automatic fallbacks.

---

## 6. Supported Channels (Messaging Platforms)

> Source: openclaw/openclaw README

OpenClaw connects to these messaging platforms out of the box:

| Channel | Library/Method | Notes |
|---------|---------------|-------|
| **WhatsApp** | Baileys | |
| **Telegram** | grammY | |
| **Slack** | Bolt | |
| **Discord** | discord.js | |
| **Google Chat** | Chat API | |
| **Signal** | signal-cli | |
| **BlueBubbles** | iMessage (recommended method) | |
| **iMessage** | legacy imsg | |
| **IRC** | | |
| **Microsoft Teams** | | |
| **Matrix** | | |
| **Feishu** | | |
| **LINE** | | |
| **Mattermost** | | |
| **Nextcloud Talk** | | |
| **Nostr** | | |
| **Synology Chat** | | |
| **Tlon** | | |
| **Twitch** | | |
| **Zalo** | | |
| **Zalo Personal** | | |
| **WeChat** | `@tencent-weixin/openclaw-weixin` | |
| **QQ** | | |
| **WebChat** | Served from Gateway | Built-in browser-based chat |
| **macOS** | Menu bar app | |
| **iOS/Android** | Node apps | |

Also: voice on macOS/iOS (wake words), continuous voice on Android.

---

## 7. Agent Identity Files: SOUL.md, USER.md, MEMORY.md

> Source: jordy (@jordymaui); OpenClaw VISION.md

These three files define who your agent is and who it works for.

### SOUL.md
The agent's personality, communication style, what it cares about, its name.
Published and shared via **onlycrabs.ai** (the SOUL.md registry, built on ClawHub infrastructure).

### USER.md
Information about the user: name, job, preferences, habits, tools used daily, goals.

### MEMORY.md
Long-term memory — the agent updates this file over time so it never forgets important facts between sessions. Acts as persistent state across the stateless session model.

### How to populate them efficiently
Let the agent interview you rather than writing manually:

```
"You just came online for the first time. Ask me questions to get to know me —
my name, what I do, my goals, how I want you to talk to me, what tools I use
daily, what I need help with. Ask them one at a time. Then use my answers to
fill out SOUL.md and USER.md."
```

Send answers as voice notes for faster, more natural responses.

> **This is the difference between a chatbot and something that actually feels like yours.**

### Important: install QMD before populating
Install the QMD skill first, before loading the agent with conversations. Installing it mid-session causes the agent to reset and lose chat logs.

---

## 8. Skills — What They Are & How They Work

> Source: openclaw/openclaw VISION.md, README; openclaw/clawhub README; openclaw/skills README

### What is a skill?
A skill is a **folder of plain text files** — primarily a `SKILL.md` markdown file plus optional supporting scripts and reference documents.

- Fully readable, editable, yours
- No binaries, no compiled code
- The agent can install and update skills by itself, just by talking to it

### Skill types
| Type | Description |
|------|-------------|
| **Bundled** | Shipped with OpenClaw core for baseline UX (rare additions; new skills go to ClawHub first) |
| **Managed** | Installed from ClawHub — versioned, curated, searchable |
| **Workspace** | Your own local skills in your workspace folder |

### Installing skills via conversation
```
"Install the QMD skill"
"Set up Brave Search — here's my API key: [KEY]"
"Install the skill at [ClawHub URL]"
```

The agent handles the install itself.

### Skill file structure
```markdown
# Skill Name

## Purpose
What this skill does.

## Inputs
What information is needed.

## Process
Step-by-step instructions.

## Output
What the finished deliverable looks like.

## Constraints
Rules and guardrails.
```

### Skills compound over time
Real example (from Oliver Henry's agent Larry):
- TikTok skill started at ~50 lines
- Grew to 500+ lines as rules were added from real failures
- Each new rule = one mistake + one explicit fix
- Result: consistent, improving performance over weeks and months

### SOUL.md registry (onlycrabs.ai)
onlycrabs.ai is the companion registry for SOUL.md files — publish and share agent personalities the same way you publish skills. Built on ClawHub infrastructure.

### Skills the team will NOT add to core (from VISION.md)
- Skills that can live on ClawHub
- Full-doc translation sets
- Commercial service integrations outside the model-provider category
- Wrapper channels around already-supported ones

---

## 9. Plugins — Extending OpenClaw

> Source: openclaw/openclaw VISION.md, AGENTS.md; docs.openclaw.ai/plugins

### Plugin vs skill
| | Skill | Plugin |
|--|-------|--------|
| Format | `SKILL.md` markdown folder | npm package |
| Runtime | Text instructions to the LLM | Executes code |
| Distribution | ClawHub | npm + ClawHub packages catalog |
| Use case | Workflows, SOPs, agent behavior | New channel types, model providers, tools |

### Plugin API
OpenClaw has an extensive plugin API. Core stays lean; optional capability ships as plugins.

Plugin categories from the SDK:
- **Channel plugins** — add new messaging channels
- **Provider plugins** — add new LLM providers
- **Memory plugins** — only one active at a time; controls how memory is stored

### Building plugins
- Use `openclaw/plugin-sdk/*` as the only public cross-package contract
- npm package distribution is the preferred path for third-party plugins
- Host and maintain in your own repository
- Community listing: https://docs.openclaw.ai/plugins/community

### Bundled plugin naming convention
Canonical plugin id must be consistent across:
- `openclaw.plugin.json:id`
- Default workspace folder name
- Package name (`@openclaw/<id>` or approved suffix forms)

### Memory plugin
One memory plugin active at a time. Multiple options ship today; project plans to converge on one recommended default path.

---

## 10. MCP Support via mcporter

> Source: openclaw/openclaw VISION.md

OpenClaw supports MCP (Model Context Protocol) through **mcporter**:
- GitHub: https://github.com/steipete/mcporter

### Design rationale
MCP is kept **decoupled from core runtime** via the bridge model:
- Add or change MCP servers without restarting the gateway
- Keeps core tool/context surface lean
- Reduces MCP churn impact on core stability and security

### What this means for you
- First-class MCP runtime will NOT be merged into core (by policy)
- If an MCP server or feature mcporter doesn't support, open an issue at mcporter repo
- For now: configure MCP through mcporter, not through OpenClaw core config

---

## 11. Automation: Cron, Webhooks, Gmail Pub/Sub

> Source: openclaw/openclaw README; docs.openclaw.ai

### Cron jobs
Built-in cron scheduler. Define recurring tasks that run even while you're away.

Docs: https://docs.openclaw.ai/automation/cron-jobs

### Webhooks
OpenClaw can receive webhooks and trigger agent actions.

Docs: https://docs.openclaw.ai/automation/webhook

### Gmail Pub/Sub
Built-in Gmail Pub/Sub integration — trigger agent actions when emails arrive.

Docs: https://docs.openclaw.ai/automation/gmail-pubsub

### Remote access for always-on automation
The gateway runs fine on a small Linux instance (VPS, Raspberry Pi, etc.) accessed via:
- **Tailscale Serve** (tailnet-only HTTPS)
- **Tailscale Funnel** (public HTTPS — requires password auth)
- **SSH tunnels**

Device-local actions (camera, screen recording, notifications) still work via device nodes connected to the remote gateway.

---

## 12. Gateway — The Control Plane

> Source: openclaw/openclaw README, AGENTS.md

### What the Gateway does
The Gateway is the single WebSocket control plane that manages:
- Sessions and presence
- Channel connections
- Tool routing
- Cron and webhooks
- Control UI (served directly from Gateway)
- WebChat UI (served directly from Gateway)

Default bind: `ws://127.0.0.1:18789`

### Tailscale access modes
Configure `gateway.tailscale.mode`:
| Mode | Behavior |
|------|---------|
| `off` | No Tailscale automation (default) |
| `serve` | Tailnet-only HTTPS via `tailscale serve` |
| `funnel` | Public HTTPS via `tailscale funnel` (requires `gateway.auth.mode: "password"`) |

Rules:
- `gateway.bind` must stay `loopback` when Serve/Funnel is enabled
- Funnel refuses to start without password auth set
- `gateway.tailscale.resetOnExit` — optionally undo Serve/Funnel on shutdown

### Running Gateway on remote Linux host
```bash
pkill -9 -f openclaw-gateway || true
nohup openclaw gateway run --bind loopback --port 18789 --force > /tmp/openclaw-gateway.log 2>&1 &

# Verify
openclaw channels status --probe
ss -ltnp | rg 18789
tail -n 120 /tmp/openclaw-gateway.log
```

### Session model
- `main` session — direct chats
- Group isolation — separate sessions per group
- Activation modes — control when the agent responds in groups
- Queue modes — how messages are queued and processed
- Per-session configurable: `thinkingLevel`, `verboseLevel`, `model`, `sendPolicy`, `groupActivation`

---

## 13. Security Model & DM Pairing

> Source: openclaw/openclaw README, SECURITY.md

### DM pairing (default security model)
Unknown senders receive a pairing code. The bot does not process their message until approved.

```bash
# Approve a new sender
openclaw pairing approve <channel> <code>
```

After approval, sender is added to a local allowlist.

To allow open public DMs (explicit opt-in only):
```
dmPolicy="open"   # in config
# AND add "*" to allowFrom/channels.discord.allowFrom
```

Run `openclaw doctor` to surface risky or misconfigured DM policies.

### Operator trust model
OpenClaw does **not** model one gateway as a multi-tenant adversarial boundary.
- Authenticated Gateway callers = trusted operators for that gateway instance
- localhost/loopback sessions authenticated with the shared gateway secret = trusted operator
- Per-user multi-tenant auth is explicitly out of scope

### Elevated bash
Use `/elevated on|off` to toggle per-session elevated access when enabled and allowlisted.

### Security contact
- Report vulnerabilities to: security@openclaw.ai
- Full threat model: https://trust.openclaw.ai
- Security officer: Jamieson O'Reilly (@theonejvo), founder of Dvuln

### Prompt injection
Prompt injection (without a boundary bypass) is explicitly out of scope. Do not point OpenClaw at untrusted web content without understanding this risk.

---

## 14. Companion Apps (macOS, iOS, Android, Windows)

> Source: openclaw/openclaw README; openclaw/openclaw-windows-node README

### macOS app
- Menu bar control plane
- Voice Wake + PTT (push-to-talk)
- Talk Mode overlay (continuous voice)
- WebChat embedded
- Debug tools
- Remote gateway control
- Canvas (A2UI visual workspace)
- Node mode — exposes `system.run`, `system.notify`, camera, screen recording to gateway

### iOS node
- Canvas, Voice Wake, Talk Mode
- Camera and screen recording
- Bonjour + device pairing
- Connects to gateway over local network or Tailscale

### Android node
- Connect tab (setup code / manual)
- Chat sessions, voice tab, Canvas
- Camera / screen recording
- Android device commands: notifications, location, SMS, photos, contacts, calendar, motion, app updates

### Windows companion (openclaw-windows-node)
Four components (C#, .NET 10):
- **OpenClaw.Tray.WinUI** — system tray app (WinUI 3) — "Molty"
  - Real-time sessions, channels, usage display
  - Quick Send via global hotkey (Ctrl+Alt+Shift+C)
  - Auto-updates from GitHub Releases
  - Embedded WebChat (WebView2)
  - Toast notifications with smart categorization
  - Channel control (start/stop Telegram, WhatsApp)
  - Cron jobs quick access
  - Auto-start with Windows
- **OpenClaw.Shared** — shared gateway client library
- **OpenClaw.Cli** — WebSocket validator CLI
- **OpenClaw.CommandPalette** — PowerToys Command Palette extension

---

## 15. Development Channels & Updating

> Source: openclaw/openclaw README

| Channel | Tag format | npm dist-tag | Notes |
|---------|-----------|-------------|-------|
| **stable** | `vYYYY.M.D` or `vYYYY.M.D-<patch>` | `latest` | Recommended |
| **beta** | `vYYYY.M.D-beta.N` | `beta` | macOS app may be missing |
| **dev** | moving `main` head | `dev` | When published |

```bash
# Switch channels
openclaw update --channel stable
openclaw update --channel beta
openclaw update --channel dev

# Health check after update
openclaw doctor
```

---

## 15b. Recent Release Notes

> Source: github.com/openclaw/openclaw releases — updated 2026-04-16

### v2026.4.14 — stable (released 2026-04-14)

**Changes:**
- OpenAI Codex/models: forward-compat support for `gpt-5.4-pro` added (pricing, limits, list/status visibility)
- Telegram/forum topics: human topic names surfaced in agent context and plugin hooks; persisted to session sidecar after restart

**Notable fixes:**
- Agents/Ollama: configured embedded-run timeout now forwarded into global stream timeout (slow local models no longer cut off early)
- Models/Codex: `apiKey` now included in codex provider catalog so custom models are no longer silently dropped from `models.json`
- Tools/image+pdf: Ollama vision model refs now normalized correctly before media-tool registry lookup
- Slack/interactions: `allowFrom` owner allowlist now applies to block-action and modal interactive events; unknown senders properly rejected
- Memory/Ollama: built-in `ollama` embedding adapter restored; endpoint-aware cache keys prevent cross-host embedding reuse
- Browser/SSRF: hostname navigation restored under default policy; loopback CDP control kept accessible
- UI/chat: replaced marked.js with markdown-it to prevent ReDoS freeze via malicious markdown
- Gateway/security: `config.patch` / `config.apply` blocked from model-facing tool when they would newly enable security-flagged flags (e.g. `dangerouslyDisableDeviceAuth`)
- Agents/context engine: compact engine-owned sessions from first tool-loop delta; long-running tool loops now stay bounded
- Ollama/OpenAI-compat: `stream_options.include_usage` now sent so local Ollama reports real usage (fixes premature compaction)
- Memory/active-memory: recalled memory moved to hidden untrusted prompt-prefix path instead of system prompt injection
- Feishu/allowlist: allowlist entries canonicalized by `user`/`chat` kind; opaque IDs no longer lowercased (prevents namespace crossing)
- Auto-reply/send policy: `sendPolicy: "deny"` no longer blocks inbound processing (observer-style setups work correctly)
- Doctor/systemd: `openclaw doctor --repair` no longer re-embeds dotenv-backed secrets into systemd units
- Google image generation: trailing `/openai` suffix stripped from Google base URLs only for native Gemini image API calls

### v2026.4.15-beta.1 — beta (released 2026-04-15, not yet stable)

**Changes:**
- Control UI/Overview: new Model Auth status card showing OAuth token health and provider rate-limit pressure at a glance (backed by `models.authStatus` gateway method, 60s cache, credential-stripped)
- Memory/LanceDB: cloud storage support added to `memory-lancedb` so durable memory indexes can run on remote object storage
- GitHub Copilot/memory search: Copilot embedding provider added for memory search
- Agents/local models: experimental `agents.defaults.experimental.localModelLean: true` flag drops heavyweight default tools (`browser`, `cron`, `message`) for weaker local-model setups
- Ollama/onboarding: setup now split into `Cloud + Local`, `Cloud only`, and `Local only`; direct `OLLAMA_API_KEY` cloud setup supported without a local daemon

**Notable fixes (beta):**
- Security/approvals: secrets redacted in exec approval prompts (credential leak in rendered prompt content closed)
- CLI/update: stale packaged `dist` chunks pruned after npm upgrades
- Memory-core/QMD `memory_get`: `memory_get` now rejects reads of arbitrary workspace markdown paths; only canonical memory files and active indexed QMD docs allowed (closes workspace-file read shim bypass)
- Gateway/MCP loopback: `/mcp` bearer comparison switched to constant-time `safeEqualSecret`; non-loopback browser-origin requests rejected before auth gate
- Agents/workspace files: `agents.files.get/set` routed through `fs-safe` helpers; symlink aliases rejected for allowlisted agent files (prevents symlink-swap path redirect)
- Gateway/auth: active gateway bearer now resolved per-request on HTTP and upgrade handlers so rotated secrets invalidate immediately without gateway restart
- Feishu/webhook: webhook transport fails closed on missing `encryptKey`; unsigned requests rejected when no key present
- OpenRouter/Qwen3: `reasoning_details` stream deltas parsed as thinking content without skipping same-chunk tool calls (fixes empty Qwen3 replies on OpenRouter)
- BlueBubbles: persistent file-backed GUID dedupe added to prevent re-replying to already-handled messages after BB Server restart
- Context Engine: graceful fallback to legacy engine when third-party context engine plugin fails at resolution (prevents full gateway outage)
- Agents/compaction: compaction reserve-token floor capped to model context window so small-context local models no longer trigger overflow or infinite compaction loops
- Agents/Anthropic: non-positive token overrides now rejected locally before reaching the provider API
- Dreaming/memory-core: ordinary transcripts that quote the dream-diary prompt no longer misclassified as internal dreaming runs

---

## 16. ClawHub — The Skill & Plugin Registry

> Source: openclaw/clawhub README; openclaw/skills README

### What ClawHub is
ClawHub (clawhub.ai) is the **public skill registry** for OpenClaw. Publish, version, and search text-based agent skills (`SKILL.md` plus supporting files). Also exposes a native OpenClaw **package catalog** for code plugins and bundle plugins.

onlycrabs.ai is the companion **SOUL.md registry**.

### CLI commands
```bash
# Auth
clawhub login
clawhub whoami

# Discover
clawhub search ...
clawhub explore
clawhub package explore
clawhub package inspect <name>

# Install / manage
clawhub install <slug>
clawhub uninstall <slug>        # removes local install only
clawhub list
clawhub update --all
clawhub inspect <slug>          # inspect without installing

# Publish
clawhub skill publish <path>
clawhub sync
clawhub package publish <source>

# Manage owned skills
clawhub skill rename <slug> <new-slug>   # keeps old slug as redirect
clawhub skill merge <source> <target>    # hides source, redirects to target
```

### Telemetry
ClawHub tracks minimal install telemetry (install counts) when logged in.
```bash
export CLAWHUB_DISABLE_TELEMETRY=1   # opt out
```

### Tech stack
- Web app: TanStack Start (React, Vite/Nitro)
- Backend: Convex (DB + file storage + HTTP actions) + Convex Auth (GitHub OAuth)
- Search: OpenAI embeddings (`text-embedding-3-small`) + Convex vector search

### Security warning (skills archive)
The `openclaw/skills` repo is a historical archive of all ClawHub skills.
> "There may be suspicious or malicious skills within this repo. We retain them for analysis. We recommend you only use the site to download skills, and treat this as a historical archive."

Always install skills via clawhub.ai or the CLI, not by cloning the archive repo.

---

## 17. Advanced Tools: Lobster, acpx, Ansible

### Lobster — Workflow Shell
> Source: openclaw/lobster README

**Lobster** is an OpenClaw-native workflow engine: typed (JSON-first) pipelines, jobs, and approval gates.

**Why it exists:** AI agents re-plan every step, burning tokens and producing non-deterministic results. Lobster encodes repeatable workflows so the agent just invokes one command instead of reasoning through the whole sequence again.

Goals:
- Typed pipelines (objects/arrays), not text pipes
- Local-first execution
- No new auth surface — Lobster does not own OAuth/tokens
- Composable macros OpenClaw invokes in one step to save tokens

```bash
node bin/lobster.js --help
node bin/lobster.js doctor
node bin/lobster.js "workflows.run --name github.pr.monitor --args-json '{"repo":"openclaw/openclaw","pr":1152}'"
node bin/lobster.js "exec --json --shell 'echo [1,2,3]' | where '0>=0' | json"
```

---

### acpx — Agent Client Protocol CLI
> Source: openclaw/acpx README

**acpx** is a headless CLI client for the **Agent Client Protocol (ACP)** — so AI agents and orchestrators can talk to coding agents over a structured protocol instead of scraping PTY sessions.

Supports: Pi, OpenClaw ACP, Codex CLI, Claude Code, and any ACP-compatible agent.

```bash
npm install -g acpx@latest
# or: npx acpx@latest

acpx codex sessions new                        # create session for this project
acpx codex 'fix the tests'                     # run prompt in session
acpx codex --no-wait 'draft migration plan'    # fire-and-forget
acpx codex cancel                              # cooperative cancel
acpx codex exec 'what does this repo do?'      # one-shot, no saved session
acpx claude 'refactor the auth module'         # use Claude Code instead
```

Key features:
- **Persistent sessions** — multi-turn conversations that survive across invocations, scoped per repo
- **Named sessions** — parallel workstreams (`-s backend`, `-s frontend`)
- **Prompt queueing** — submit while one is running; they execute in order
- **Structured output** — typed ACP messages (thinking, tool calls, diffs) instead of ANSI scraping
- **Crash reconnect** — dead agent processes detected and sessions reloaded automatically
- **Flow mode** — `flow run <file>` for TypeScript workflow modules over multiple prompts

Install acpx skill for full reference:
```bash
npx acpx@latest --skill install acpx
# Read skill: https://raw.githubusercontent.com/openclaw/acpx/main/skills/acpx/SKILL.md
```

---

### Ansible Installer (Linux — hardened)
> Source: openclaw/openclaw-ansible README

Automated, hardened installation for Debian/Ubuntu.

```bash
curl -fsSL https://raw.githubusercontent.com/openclaw/openclaw-ansible/main/install.sh | bash
```

Installs:
- Tailscale (mesh VPN)
- UFW firewall (SSH + Tailscale ports only)
- Fail2ban (SSH brute-force protection)
- Docker CE + Compose V2
- Node.js 22.x + pnpm
- OpenClaw as systemd service (auto-start)

> macOS bare-metal support deprecated 2026-02-06 due to system-level permission risks. Use Docker or native macOS install instead.

---

## 18. Neurometric & ClawPack — Domain-Routing Model Layer

> Source: https://www.neurometric.ai/claw and https://www.neurometric.ai/docs

### What is Neurometric?
Neurometric is an OpenAI-compatible API proxy that dynamically selects the right model and inference strategy per task. Core claim: 4x faster and 10x cheaper vs. one generalist model, by matching model to task type.

### What is ClawPack?
**ClawPack** (`neurometric/clawpack`) is a single model ID routing to 39 task-specific specialists across 6 domains. One API call — the SPI (Smart Prompt Intelligence) classifier auto-detects task type and routes. Responses tagged with domain handled.

> **Key insight for OpenClaw skill authors:** Reference `neurometric/clawpack` as the model in a skill definition and let the SPI route automatically. No domain-specific routing logic needed in the skill.

### Architecture
```
Your App / OpenClaw
  ↓ POST /v1/chat/completions
  ↓ model: neurometric/clawpack

Neurometric SPI
  ↓ Classifies task → Routes to specialist

[LEGAL]   [FINANCE]  [CODING]
[SALES]   [SUPPORT]  [MARKETING]

  ↓ Tagged response: e.g. [LEGAL] Contract review complete...
```

### The 6 Specialist Domains

| Domain | Key Capabilities |
|--------|------------------|
| **Legal** | Contract risk analysis, clause extraction, redline diffs, compliance (GDPR, HIPAA, SOC2), liability assessment |
| **Finance** | Invoice parsing, expense categorization, financial statement analysis, ratio calculations, anomaly detection |
| **Coding** | Code generation, code review & PR summaries, unit/integration tests, docs & docstrings, security scanning |
| **Sales** | Cold outreach & email sequences, lead scoring, objection handling, proposal drafting, meeting prep & CRM summaries |
| **Support** | Ticket triage, sentiment detection, response drafting, escalation classification, KB article retrieval |
| **Marketing** | Ad copy (Google/LinkedIn/Facebook), SEO briefs, social posts, email campaigns, headline A/B testing, brand voice |

### Integration with OpenClaw
```bash
# 1. Get free API key at neurometric.ai/claw (no credit card)
# 2. Add to OpenClaw model picker (one install command — check marketplace for current command)
# 3. Select neurometric/clawpack in OpenClaw — SPI routes automatically
```

### Code examples
```python
from openai import OpenAI
client = OpenAI(
    api_key=os.environ.get("NEUROMETRIC_API_KEY"),
    base_url="https://api.neurometric.ai/v1"
)
response = client.chat.completions.create(
    model="neurometric/clawpack",
    messages=[{"role": "user", "content": "Review this contract for liability clauses..."}]
)
# Response tagged: [LEGAL] ...
```

```bash
curl -X POST https://api.neurometric.ai/v1/chat/completions \
  -H "Authorization: Bearer $NEUROMETRIC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "neurometric/clawpack", "messages": [{"role": "user", "content": "..."}]}'
```

### Using ClawPack in a skill file
```markdown
## Model
neurometric/clawpack

## Purpose
Handle any business task — routing is automatic.
```

### Pricing
| Plan | Price | Tokens |
|------|-------|--------|
| Free | $0/mo | 100M tokens/month, all 6 domains |
| Pro | $8/mo | Unlimited, all 6 domains + priority support |

Contact: support@neurometric.ai

### Key considerations
- ClawPack does NOT replace Claude/OpenAI as the agent brain — it handles task-specific LLM calls within workflows
- Best for: business-function tasks inside skills (legal review, sales copy, support drafts, financial parsing)
- Not needed for: agent conversation, identity management, memory operations — keep those on your primary model
- Fully OpenAI-compatible — works with LangChain, CrewAI, AutoGen, raw HTTP

---

## 19. Core Concepts: Chat vs Agents

> Source: Greg Isenberg (@gregisenberg) AI Agents 101 masterclass, March 2026

| Concept | Chat Models | Agents |
|---------|-------------|--------|
| Mode | Question → Answer (back and forth) | Goal → Result (autonomous loop) |
| Stopping | After each response | When the task is actually finished |
| Loop | None | Observe → Think → Act → repeat |
| Babysitting | Required | Not required |

### The Agent Loop
```
gather context → decide next step → execute action → feed result back → repeat until done
```

### The Five-Layer Agent Stack
```
Model       = reasoning layer (Claude, GPT, Gemini, local)
Loop        = the observe/think/act cycle
Tools       = browser, code, APIs, internal software
Context     = files, instructions, memory
Harness     = environment running everything (OpenClaw, Claude Code)
```

### MCP (Model Context Protocol)
How agents access external tools. Connects browser, code runners, APIs, internal software. Once connected, the agent decides autonomously when to invoke each tool.
In OpenClaw: handled via mcporter (https://github.com/steipete/mcporter).

---

## 20. The AI Operating System (AIOS) Model

> Source: Greg Isenberg (@gregisenberg) + Remy Gaskell, AI Agents 101 masterclass, March 2026

The AIOS model combines all layers into a self-improving autonomous system:

```
Context files   = who the agent is and how it behaves (AGENTS.md / CLAUDE.md)
Memory file     = what it has learned (memory.md / MEMORY.md)
MCP tools       = what it can access (external services, APIs)
Skills          = what it knows how to do (reusable .md SOPs)
Harness         = the runtime (OpenClaw, Claude Code)
Schedule        = when it runs (cron triggers, event triggers)
```

### agents.md / CLAUDE.md — The onboarding document
The agent's operating manual. Tells the agent:
- Who it is
- How to behave
- What it knows
- What tools it can use
- What to do when uncertain

Loads **every time** before any task. Highest-leverage config file in any agentic setup.

> OpenClaw's own CLAUDE.md / AGENTS.md files in the repo are canonical examples of this pattern applied at the codebase level — read them for inspiration.

### The "100x Employee" concept
An individual who brings a pre-existing, finely-tuned AI operating system to any context. The AIOS travels with the person, not the job.

---

## 21. Context Engineering: .md File Architecture

> Source: Nav Toor (@heynavtoor), "17 Best Practices That Make Claude Cowork 100x More Powerful"; Greg Isenberg AI Agents 101

### The fundamental shift
- ChatGPT era: optimize the **prompt**
- Agentic era: optimize the **context architecture**

> "The prompt is the least important part of a session. The context, structure, skills, and folder architecture — that's where the leverage is."

### Three persistent context files (minimum viable setup)

| File | Contents |
|------|----------|
| `about-me.md` | Professional identity, role, what you're building, what success looks like |
| `brand-voice.md` | Tone, word choices, formatting preferences, sample outputs |
| `working-style.md` | Collaboration rules, output format defaults, what to do when uncertain |

Refine weekly — every time output is slightly off, update the relevant file. They compound.

### _MANIFEST.md — Context scoping for folders
Drop into any working folder to control what the agent reads:

```markdown
## Tier 1 (Canonical) — Read first, always
Brand guidelines, project brief, master stylesheet

## Tier 2 (Domain) — Load only when task touches this domain
[subfolder] → specific topics

## Tier 3 (Archival) — Ignore unless specifically asked
Old drafts, superseded versions
```

### Global Instructions pattern
Loads before everything — before files, before the prompt.

```
I'm [NAME], a [ROLE]. Before starting any task, look for _MANIFEST.md and read
Tier 1 files only. Ask clarifying questions before executing. Show a brief plan
before taking any action. Never delete files without explicit confirmation.
```

### Task prompt design
Define the **end state**, not the process:

```
# Bad
"Help me with my files."

# Good
"Organize all files in this folder into subfolders by client name. Use YYYY-MM-DD
for date references. Flag uncategorizable files in REVIEW_NEEDED.md. Don't delete
anything."
```

Every task prompt answers:
1. What does "done" look like?
2. What are the constraints?
3. What should the agent do when uncertain?

---

## 22. LLM Knowledge Base Pattern (Karpathy)

> Source: Andrej Karpathy (@karpathy), April 2026; Nick Spisak (@NickSpisak_); Corey Ganim (@coreyganim)

### Core architecture
```
raw/     → dump everything here (immutable source material — never edit)
wiki/    → AI compiles and maintains this (never manually edit)
outputs/ → AI-generated answers, reports, slides (file back into wiki)
```

### The schema file — CLAUDE.md / AGENTS.md
One file in project root telling the AI:
- What this knowledge base is
- How it's organized
- Wiki maintenance rules
- Your interests and priorities

### Workflow
```
1. Collect raw sources → drop into raw/ (don't organize — that's AI's job)
2. Tell AI: "Read the schema, read everything in raw/, compile the wiki."
3. Walk away. Return to wiki/ full of organized articles and cross-references.
4. Ask questions against your compiled wiki.
5. Save useful answers back into the wiki (write-back rule).
6. Monthly health check: AI flags contradictions, missing sources, gaps.
```

### Source collection tools
- **Obsidian Web Clipper** — converts web articles to .md
- **agent-browser** (Vercel Labs) — AI-controlled Chrome; 82% fewer tokens than Playwright MCP
- Manual PDF dumps, image saves

### Key principle
> "You rarely ever write or edit the wiki manually. It's the domain of the LLM." — Andrej Karpathy

---

## 23. Autonomous Repo Agents: Code Factory Pattern

> Source: Ryan Carson (@ryancarson), "Code Factory" X Article, Feb 16, 2026

### The loop
1. Coding agent writes code
2. Repo enforces risk-aware checks before merge
3. Code review agent validates the PR
4. Evidence (tests + browser + review) is machine-verifiable
5. Findings turn into repeatable harness cases

### Critical lessons
1. **Deterministic ordering** — preflight gate before CI fanout
2. **Current-head SHA matching** — review state valid only when it matches current PR head commit. Ignore stale comments tied to older SHAs.
3. **Single canonical rerun writer** — dedupe by marker + `sha:<head>` to prevent race conditions
4. Treat vulnerability language and weak-confidence summaries as actionable
5. Auto-resolve only bot-only threads after clean current-head evidence
6. A remediation agent can shorten the loop significantly

### Control plane pattern (code)
```typescript
const requiredChecks = computeRequiredChecks(changedFiles, riskTier);
await assertDocsDriftRules(changedFiles);
await assertRequiredChecksSuccessful(requiredChecks);
if (needsCodeReviewAgent(changedFiles, riskTier)) {
  await waitForCodeReviewCompletion({ headSha, timeoutMinutes: 20 });
  await assertNoActionableFindingsForHead(headSha);
}
```

### Reference implementation stack
| Component | Tool |
|-----------|------|
| Code review agent | Greptile |
| Remediation agent | Codex Action |
| Canonical rerun workflow | `greptile-rerun.yml` |
| Stale-thread cleanup | `greptile-auto-resolve-threads.yml` |
| Preflight policy | `risk-policy-gate.yml` |

---

## 24. Claude Token Cost Optimization

> Source: @noisyb0y1, "How I stopped burning 75% of my Claude budget" (Apr 7, 2026)

### How Claude billing works
- Counts **tokens**, not messages
- Message 30 costs **31x more than message 1** (30 messages = ~232K tokens)
- Usage runs on a **sliding 5-hour window**
- Peak hours 5:00–11:00 AM Pacific burn limits faster outside the US

### Fix 1 — Caveman prompt plugin (biggest single impact)
Reduces Claude verbosity 65–87%:
```
/plugin marketplace add JuliusBrussee
/plugin install caveman
```
GitHub: https://github.com/JuliusBrussee/caveman (1,900+ stars)

### Fix 2 — Window anchoring
Use `claude-warmup` — a GitHub Actions cron that sends a warmup message at 6:15 AM on weekdays to anchor the 5-hour window before your workday.
GitHub: https://github.com/vdesimone/claude-warmup

### Fix 3 — Behavioral changes
| Habit | Fix |
|-------|-----|
| Adding new reply messages | Edit prompts instead — each new message adds all previous to context |
| Sending three separate prompts | Batch into one message — three questions = one context load |
| Re-uploading files each session | Upload to Projects once (cached, not re-tokenized) |
| Not using Memory | Set up Settings → Memory — saves thousands of tokens/day |

---

## 25. Claude Cowork — Power User System

> Source: Nav Toor (@heynavtoor), "17 Best Practices That Make Claude Cowork 100x More Powerful" (Mar 1, 2026)

> Note: "Claude Cowork" is Anthropic's agentic desktop product. Principles transfer directly to OpenClaw and any LLM agent setup.

### The 17 practices (condensed)

**Context architecture**
1. **_MANIFEST.md** — Tier 1/2/3 context scoping in every folder
2. **Global Instructions as permanent OS** — loaded before everything
3. **Three persistent context files** — about-me.md, brand-voice.md, working-style.md
4. **Folder Instructions** — project-specific context layered on Global
5. **Scope context deliberately** — don't let the agent read everything

**Task design**
6. **Define end state, not process**
7. **Always request a plan before execution** — 30 seconds prevents 20-minute undo sessions
8. **Handle uncertainty explicitly** — tell it what to do at every edge case
9. **Batch related work into single sessions** — shared context, lower startup cost
10. **Trigger parallel subagents** — "Spin up subagents to..." for independent tasks

**Automation and scheduling**
11. **Schedule recurring tasks** — `/schedule` for daily briefings, competitor tracking, status reports
12. **Externalize everything to files** — no memory = no hallucination; files don't degrade
13. **/schedule + connectors = real automation** — Gmail, Slack, Google Drive, Notion (50+ integrations)

**Plugins and skills**
14. **Stack plugins for compound capability** — composable, use together in one session
15. **Build custom skills for your workflows** — encode months of process into one command
16. **Use Plugin Management plugin** — build plugins conversationally, no code needed

**Safety**
17. **Treat it like a powerful employee** — back up before experimenting; add "Don't delete anything" to every task; monitor first runs; be aware of prompt injection with untrusted content

---

## 26. Real-World Agent Deployments

> Source: Oliver Henry (@oliverhenry), "How a personal AI agent will change your entire life in 1 day" (Mar 7, 2026)

### Case study: Larry (Oliver Henry's OpenClaw agent)
**Hardware:** Old gaming PC running Ubuntu
**Agent name:** Larry
**Runtime:** OpenClaw
**Revenue after 4 weeks:** $7,000+/month

**Daily autonomous operations:**
- Generates TikTok slideshow content (images, hooks, text overlays, uploads drafts)
- Tracks which posts convert → drops failing hooks, turns winners into formulas
- Monitors X mentions, builds daily support reports
- Tracks app revenue, flags paywall and onboarding issues
- Writes and tests code, shows diffs, waits for approval
- Manages skill review pipeline (LarryBrain marketplace)
- Runs cron jobs overnight

**Key insight — compounding:**
> "My TikTok skill started at ~50 lines. It's over 500 now. Every single rule exists because something went wrong and I fixed it. I'm not getting lucky. I'm getting better every single day. That's the difference between a tool and an agent. Tools stay the same. I improve." — Larry (written by Oliver Henry)

### Other real-world deployments (non-developers)
- Car salesman → follow-up system writing personalized proposals from lot behavior data
- Cleaner → full business website with online booking, built from phone
- Estate agent → property listings generated from photos and bullet points
- Personal trainer → meal plan app
- Recruiter → full recruitment platform to compete with former employer

All built by non-developers. Timeline: months → days.

### Claude Code Routines (April 2026 — new)
> Source: Greg Isenberg (@gregisenberg), April 2026

Claude Code now ships **Routines** (research preview): 24/7 on Anthropic's servers, triggered by schedule, API call, or event. Laptop can be closed.

**Trigger examples:**
| Trigger | Agent action |
|---------|-------------|
| Customer usage drops 40% in a week | Alert + draft outreach |
| Deal sits in pipeline untouched 14 days | Follow-up sequence |
| Contract hits 90 days before renewal | Renewal prep workflow |
| Stripe payment fails | Recovery sequence |
| Competitor launches a feature | Competitive brief |

---

## 27. Critical Mistakes to Avoid (Setup)

> Source: jordy (@jordymaui), synthesized from 80 hours of failed setups

| Mistake | Consequence | Fix |
|---------|-------------|-----|
| Using Anthropic console pay-per-use instead of Claude membership token | Burned $800+ in tokens | Use Claude Pro/Max token from `claude setup-token` |
| Running multiple agents simultaneously | Context lost between agents, confusion | One agent + proper skills beats a squad of confused ones |
| AWS/remote server for day-one setup | Unnecessary complexity | Start with local machine; remote works fine once you know what you're doing |
| Leaving SOUL.md, USER.md empty | Agent sounds like a customer service bot | Fill out identity files; let the agent interview you |
| Installing QMD skill mid-session | Agent resets, loses chat logs | Install QMD first, before any other work |
| Ignoring voice messages / not setting up Groq | Misses the most natural usage pattern | Set up Groq from day one |
| Trailing space in Claude token | HTTPS error that looks unrelated | Strip all spaces from the token string |

---

## 28. Appendix: Key Source References

| Source | Author | Date | URL |
|--------|--------|------|-----|
| OpenClaw main repo | openclaw org | Live | https://github.com/openclaw/openclaw |
| OpenClaw website | openclaw org | Live | https://openclaw.ai |
| OpenClaw docs | openclaw org | Live | https://docs.openclaw.ai |
| ClawHub repo | openclaw org | Live | https://github.com/openclaw/clawhub |
| acpx repo | openclaw org | Live | https://github.com/openclaw/acpx |
| Lobster repo | openclaw org | Live | https://github.com/openclaw/lobster |
| openclaw-windows-node | openclaw org | Live | https://github.com/openclaw/openclaw-windows-node |
| openclaw-ansible | openclaw org | Live | https://github.com/openclaw/openclaw-ansible |
| trust / threat model | openclaw org | Live | https://github.com/openclaw/trust |
| mcporter (MCP bridge) | steipete | Live | https://github.com/steipete/mcporter |
| "I wasted 80 hours and $800 setting up OpenClaw" | @jordymaui | Feb 16, 2026 | https://x.com/jordymaui/status/2023421221744877903 |
| "How a personal AI agent will change your entire life in 1 day" | @oliverhenry | Mar 7, 2026 | https://x.com/oliverhenry/article/2030394095399588145 |
| "AI AGENTS 101 (58 minute free masterclass)" | @gregisenberg | Mar 17, 2026 | https://x.com/gregisenberg/status/2034052610664116550 |
| AI Agents 101 YouTube video (58:55) | Greg Isenberg + Remy Gaskell | Mar 17, 2026 | https://www.youtube.com/watch?v=eA9Zf2-qYYM |
| "17 Best Practices That Make Claude Cowork 100x More Powerful" | @heynavtoor | Mar 1, 2026 | https://x.com/heynavtoor/status/2028148844891152554 |
| "Code Factory" article | @ryancarson | Feb 16, 2026 | https://x.com/ryancarson/status/2023452909883609111 |
| "LLM Knowledge Bases" | @karpathy | Apr 2, 2026 | https://x.com/karpathy/status/2039805659525644595 |
| "How to Build Your Second Brain" | @NickSpisak_ | Apr 4, 2026 | https://x.com/NickSpisak_/status/2040448463540830705 |
| "How I stopped burning 75% of my Claude budget" | @noisyb0y1 | Apr 7, 2026 | https://x.com/noisyb0y1/status/2041454862425047268 |
| Claude Code Routines announcement | @gregisenberg | Apr 14, 2026 | https://x.com/gregisenberg/status/2044163870567346331 |
| ClawPack product page | Neurometric | 2026 | https://www.neurometric.ai/claw |
| Neurometric API docs | Neurometric | 2026 | https://www.neurometric.ai/docs |
