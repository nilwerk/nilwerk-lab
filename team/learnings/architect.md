# Playbook: System Architect

Living skill file for this role — read it before every assignment (TEAM.md §8).
Rules are short and imperative, most important first, each with *why* and a source.
Updated in the Friday retro PR; max ~60 rules. Never relaxes TEAM.md §5 hard rules.

## Rules
- Write the interface contracts (device report schema, OpenAPI, DB schema, MCP tools) before builders start coding against them. *Why:* parallel agents otherwise invent incompatible shapes. *Source:* team setup.
- Check reality against documents: earlier smart-home logs claimed MQTT/Node-RED/entities that weren't actually running. Verify the live state before designing on top of it. *Source:* verification/01-findings-vs-logs.
