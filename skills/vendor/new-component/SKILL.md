---
name: new-component
description: 'Scaffold a new firmware component following the standard structure. Use when creating a new reusable module under common/components/ or a variant-specific component. Creates include/<name>.h, src/<name>.c, tests/test_<name>.c, and wires CMakeLists.txt.'
---

# Skill: New Firmware Component

## When to use
Use when adding a new reusable firmware module to `cronus/common/components/` or `cronus/rom/common/components/`.

## Preconditions
- Component name follows `snake_case` naming convention.
- Target component directory is confirmed (MCU-wide vs ROM-specific).

## Steps

1. **Confirm placement** — decide between:
   - `cronus/common/components/<name>/` — MCU-wide (shared by ROM and RAM)
   - `cronus/rom/common/components/<name>/` — ROM-only

2. **Create directory structure:**
   ```
   <name>/
   ├── include/<name>.h
   ├── src/<name>.c
   └── tests/
       └── test_<name>.c
   ```

3. **Header (`include/<name>.h`):**
   - Add include guard: `#ifndef <NAME>_H` / `#define <NAME>_H`
   - Declare only the public API functions
   - Use `snake_case_t` for types, `UPPER_SNAKE_CASE` for constants

4. **Implementation (`src/<name>.c`):**
   - Include the public header first
   - Mark internal helpers as `static`
   - No raw register access — use `hardware_layer` abstractions

5. **Unit test (`tests/test_<name>.c`):**
   - Use CMocka boilerplate (`stdarg.h`, `stddef.h`, `setjmp.h`, `cmocka.h`)
   - Write at least one positive and one negative test case
   - `main()` must call `cmocka_run_group_tests()`

6. **Wire CMakeLists.txt:**
   - Add the component as a library target
   - Register the test with `add_bst_cmocka_test()`

7. **Build and test:**
   - `bst-cli --configuration cronus/rom/bmi234_rom --build`
   - `bst-cli --configuration cronus/rom/bmi234_rom --test unit`

## Done criteria
- Directory structure matches the component layout convention.
- Unit test compiles and passes.
- No include-guard collisions with existing components.
