# Pipeline and QA skills

| Name | What | URL | Status | Used by |
|---|---|---|---|---|
| GitHub Actions docs | Workflow syntax, `needs`, `if`, artifacts | https://docs.github.com/en/actions | to verify | Kai |
| GitHub path filters | Detect-then-run pattern | https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions | to verify | Kai |
| Supabase CLI | Migrations, local Postgres tests | https://supabase.com/docs/guides/cli | to verify | Kai, Sana |
| Unity and CMock | C unit tests and mocks | https://github.com/ThrowTheSwitch/Unity , https://github.com/ThrowTheSwitch/CMock | to verify | Ines, Mira |
| Stryker mutator | Mutation testing (JS/TS) | https://stryker-mutator.io | to verify | Ines |
| mutmut | Mutation testing (Python) | https://github.com/boxed/mutmut | to verify | Ines |

Rule: CI verdict is per head SHA, checked with `gh api repos/nilwerk/nilwerk-lab/commits/<sha>/check-runs` (Kai, meeting 13 Nov).
