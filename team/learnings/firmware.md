# Playbook: Firmware + Edge AI

Living skill file for this role — read it before every assignment (TEAM.md §8).
Rules are short and imperative, most important first, each with *why* and a source.
Updated in the Friday retro PR; max ~60 rules. Never relaxes TEAM.md §5 hard rules.

## Rules
- Before chasing a "flash write failed"/OpenOCD/CMSIS-DAP error as a code bug, check board profile, port, cable and bootloader mode. *Why:* nRF52 and CMSIS-DAP errors were tool/board selection issues, not code. *Source:* learning logs 06, 08; checklist E6.
- Power the sensor only during a measurement, give it ≥ 1.5 s warm-up, take several spaced samples and smooth (EMA). *Why:* capacitive probe readings were noisy right after power-on. *Source:* learning log 06.
- Use deep sleep, not delay loops, between samples. *Why:* delay() idles the MCU at full power. *Source:* learning log 01.
- Verify library API names against the library source before using them. *Why:* e.g. enableCharging vs enableCharge on the Nicla. *Source:* learning log 08.
