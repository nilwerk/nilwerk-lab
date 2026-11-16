# Offline sample ring buffer (task 4.F3, FR-D04). Pure C: also built by test/host without ESP-IDF.
idf_component_register(
    SRCS "src/nw_sample_ring.c"
    INCLUDE_DIRS "include"
)
