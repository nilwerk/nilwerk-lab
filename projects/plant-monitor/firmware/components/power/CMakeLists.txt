# Deep-sleep and report decision (task 4.F3, FR-D02, FR-D06, NFR-01). Pure C: also built by test/host without ESP-IDF.
idf_component_register(
    SRCS "src/nw_sleep.c"
    INCLUDE_DIRS "include"
    REQUIRES storage
)
