# Pipeline and QA skills

| Name | What | URL | Status | Used by |
|---|---|---|---|---|
| GitHub Actions docs | Workflow syntax reference: `paths` and `paths-ignore` filters verified; job-level `if` is in the part of the page the fetch did not reach (check it) | https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions | verified 13 Nov (Lead fetch) (partly) | Kai |
| GitHub path filters | Detect-then-run pattern (section on `on.<event>.paths`) | https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions | verified 13 Nov (Lead fetch) | Kai |
| Supabase CLI | Migrations, local Postgres tests | https://supabase.com/docs/guides/cli | to verify | Kai, Sana |
| Unity and CMock | C unit tests and mocks | https://github.com/ThrowTheSwitch/Unity , https://github.com/ThrowTheSwitch/CMock | to verify | Ines, Mira |
| Stryker mutator | Mutation testing (JS/TS) | https://stryker-mutator.io | to verify | Ines |
| mutmut | Mutation testing (Python) | https://github.com/boxed/mutmut | to verify | Ines |

Rule: CI verdict is per head SHA, checked with `gh api repos/nilwerk/nilwerk-lab/commits/<sha>/check-runs` (Kai, meeting 13 Nov).
