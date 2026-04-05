# Honcho Memory Fix — Apply This Now

The Honcho plugin's hooks dump every raw message (tool logs, short commands, emails) into Honcho. Honcho's backend auto-generates "conclusions" from those messages. After 3 weeks you end up with 60k+ garbage conclusions polluting your memory.

## Fix

Open `~/.honcho/config.json` and add `saveMessages: false` to your hosts block:

```json
{
  "hosts": {
    "claude_code": {
      "workspace": "your-workspace-name",
      "aiPeer": "claude-code",
      "enabled": true,
      "saveMessages": false,
      "contextRefresh": {
        "messageThreshold": 10
      }
    }
  }
}
```

## What still works

- Honcho context block still injected every message (your profile, traits, preferences)
- `create_conclusion()` still works if you explicitly save something
- Search still works
- Chat still works

## What stops

- Hooks no longer upload raw tool logs, assistant responses, or short commands
- No more auto-generated garbage conclusions from those messages

## What it doesn't fix

- Existing garbage stays (don't mass-delete, your real history is mixed in)
- If you had a stale preference baked into your Honcho profile, save a corrective conclusion to override it

That's it. One config change, no code changes, nothing breaks.
