# Testing
- Every acceptance criterion maps to a test ID. Matrix status is only: not run, pass, fail, waived.
- Thresholds and test IDs go into the intake gate, not the review (Ines, Sprint 1 lesson).
- Write the matrix row and its test ID in the same PR as the feature, status "not run" from day one.
- QA tests the PR head SHA (`git show <sha>:<path>` or a clean checkout), and the report records the SHA.
- Read both line comments and conversation comments before a verdict (two separate endpoints).
- Mutation check before a test suite is accepted.
- Cross-document consistency grep after every decision.
- Bench procedures (for Peter): numbered steps, raw values, explicit PASS/FAIL thresholds, photo list.
