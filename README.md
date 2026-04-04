# Brain — Consistent Memory for Claude Code

A 3-layer memory system that gives Claude Code persistent memory across sessions.

## What You Get

| Layer | What | How |
|-------|------|-----|
| **Honcho** | Cross-session memory — Claude remembers who you are, what you decided, your preferences | Plugin that runs on every message |
| **Obsidian Vault** | Structured knowledge — projects, strategy, daily notes, research | Files Claude reads and writes automatically |
| **Claude Code Auto-Memory** | Behavioral memory — how you like Claude to work | Builds automatically over time in `~/.claude/` |

## Setup (15 minutes)

### Step 1: Copy the vault

Copy the `vault-template/` folder wherever you want your vault to live. Rename it to whatever you want (e.g., `My Brain`, `Second Brain`).

Open it in Obsidian (optional but recommended).

### Step 2: Fill in your identity

Edit `Context/me.md` — replace all `{PLACEHOLDERS}` with your info. This is how Claude learns who you are.

Edit `Context/strategy.md` — add your current goals and focus.

### Step 3: Install Honcho plugin

1. Open Claude Code in your vault directory
2. Run: `/plugins` and search for "honcho"
3. Install the Honcho plugin
4. When prompted, enter your Honcho API key (ask Virgil or sign up at honcho.dev)

### Step 4: Configure Honcho

Create the config file:

```bash
mkdir -p ~/.honcho
```

Copy `honcho-config-template.json` to `~/.honcho/config.json`.

Edit it:
- Replace `/path/to/your/vault` with the actual path to your vault folder
- Replace `yourname-vault-name` with something like `igor-brain` or `vinod-brain`

### Step 5: Update Claude Code settings

Open `~/.claude/settings.json` and merge in the entries from `settings-snippet.json`:

- Add `"honcho@honcho": true` under `enabledPlugins`
- Add the `extraKnownMarketplaces` block if it doesn't exist

### Step 6: First run

Open Claude Code in your vault directory and say something. You should see:

- "Fetching memory context" in the hook output
- Honcho context block appearing in system messages

If both show up, you're live. Claude will start learning about you immediately.

## How It Works

**Honcho** fires on every message. It reads your conversation, extracts conclusions about you (preferences, decisions, traits), and injects relevant ones into future conversations. Think of it as Claude's long-term memory about WHO you are.

**The vault** is Claude's structured knowledge base. The `CLAUDE.md` file tells Claude how to route information — project work goes to `Projects/`, meeting notes to `Intelligence/`, your identity to `Context/me.md`. Claude auto-saves without asking.

**Auto-memory** (Layer 3) builds itself. As you work with Claude Code, it creates behavioral memories in `~/.claude/projects/.../memory/`. No setup needed.

## The Teaching Loop

When you correct Claude ("don't do that", "always do this"), it:
1. Applies the correction immediately
2. Saves it as a permanent rule in `CLAUDE.md`
3. Routes the insight to the right file

This means Claude gets better every session. Your corrections stick.

## Folder Structure

```
your-vault/
  CLAUDE.md              # The operating system — Claude reads this first
  Context/
    me.md                # Who you are
    strategy.md          # What you're working toward
  Daily/                 # Daily notes (short-term memory)
  Projects/              # Active project work
  Intelligence/          # Research, competitors, decisions
  Resources/             # Reusable content, frameworks
  Skills/                # Automation skills
```

## Questions?

Ask Virgil.
