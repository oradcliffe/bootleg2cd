# Claude Code Instructions

## Tool usage policy

The user has whitelisted specific Bash commands in `.claude/settings.json`. **Never use Bash commands that aren't on that whitelist.** Use the dedicated tools (Read, Write, Edit, Glob, Grep) for file operations instead of shelling out to python3, cat, grep, jq, etc. The goal is zero user approval prompts during normal operation.
