# Playbook: Pipeline / DevOps

Living skill file for this role — read it before every assignment (TEAM.md §8).
Rules are short and imperative, most important first, each with *why* and a source.
Updated in the Friday retro PR; max ~60 rules. Never relaxes TEAM.md §5 hard rules.

## Rules
- Use `gh api` (REST) for PRs, comments and check runs; GraphQL-based `gh pr …` commands are blocked in agent sessions. *Source:* setup 2026-11-03, TEAM.md §11.
- Every job must skip cleanly (and say so) when its workstream has no project yet. *Why:* a red pipeline from empty folders hides real failures. *Source:* CI design.
- Firmware toolchains can't be downloaded in the agent sandbox; build in GitHub Actions. *Why:* Arduino/ESP download servers were blocked in the sandbox. *Source:* learning log 08.
