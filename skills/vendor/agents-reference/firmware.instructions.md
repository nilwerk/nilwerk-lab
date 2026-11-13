---
description: "Use when editing C source or header files (.c, .h). Covers firmware coding conventions, component structure, register naming, and layer boundaries."
applyTo: ["**/*.c", "**/*.h"]
---

# Firmware C Conventions

## Language Standard

- **C99** (`-std=c99`)
- Compile with `-Wall -Werror` — all warnings are errors
- No GNU extensions unless explicitly justified

## Component Structure

Every reusable module follows this layout:

```
components/<name>/
├── include/<name>.h       # Public API (only this is exposed to consumers)
├── src/<name>.c           # Implementation (internal)
└── tests/
    └── test_<name>.c      # CMocka unit test
```

- Headers use include guards: `#ifndef <NAME>_H` / `#define <NAME>_H`
- Public API is minimal — expose only what consumers need
- Internal helpers are `static` within the `.c` file

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Functions | `snake_case` | `acc_st_init()` |
| Types (struct/enum) | `snake_case_t` | `acc_config_t` |
| Macros/constants | `UPPER_SNAKE_CASE` | `ACC_ST_REG_ADDR` |
| File names | `snake_case` | `acc_st.c`, `acc_st.h` |
| Global variables | Prefix with module name | `acc_st_state` |

## Layer Architecture

```
application_layer/    → Entry point (main.c), system init, task orchestration
sensor_layer/         → Sensor algorithms, data processing, calibration
hardware_layer/       → HW register access, peripheral drivers
memory_map/           → Register definitions, memory layout headers
```

**Rules:**
- Upper layers may call lower layers; never the reverse
- `hardware_layer` is the only code that touches registers directly
- `sensor_layer` operates on abstracted data, not raw registers
- `application_layer` wires layers together via init/run sequences

## Register Access

- All register access goes through `hardware_layer` abstractions
- Register addresses defined in `memory_map/` headers
- Use typed access functions, not raw pointer casts:

```c
/* Good */
uint8_t value = hw_read_reg(REG_ACC_DATA);

/* Bad — direct memory access outside hardware_layer */
uint8_t value = *(volatile uint8_t *)0x1234;
```

## Unit Testing (CMocka)

```c
#include <stdarg.h>
#include <stddef.h>
#include <setjmp.h>
#include <cmocka.h>

#include "my_component.h"

static void test_init_success(void **state) {
    (void)state;
    int result = my_component_init();
    assert_int_equal(result, 0);
}

int main(void) {
    const struct CMUnitTest tests[] = {
        cmocka_unit_test(test_init_success),
    };
    return cmocka_run_group_tests(tests, NULL, NULL);
}
```

## Common Anti-patterns

- **Global mutable state** — minimise; prefer passing context structs
- **Magic numbers** — define named constants in headers
- **Long functions** — keep under ~50 lines; extract helpers
- **Missing `static`** — internal functions must be `static`
- **Casting away `const`** — never do this
- **Platform-specific code outside hardware_layer** — isolate all HW dependencies
