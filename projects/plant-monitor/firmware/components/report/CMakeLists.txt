# Hourly report payload (task 4.F3, FR-D02). Pure C: also built by test/host without ESP-IDF.
# The HTTPS upload is NOT here (out of scope for 4.F3 slice 1).
idf_component_register(
    SRCS "src/nw_report.c"
    INCLUDE_DIRS "include"
    REQUIRES storage
)
