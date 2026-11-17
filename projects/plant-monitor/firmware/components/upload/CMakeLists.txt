# Hourly upload logic (task 4.F3 slice 2, FR-D02, FR-D04, FR-D06, NFR-06). Pure C: also built by test/host without ESP-IDF.
# The real HTTPS client (esp_http_client, cert bundle/pinning, SNTP) is NOT here yet: it only has to fill nw_upload_io_t.
idf_component_register(
    SRCS "src/nw_upload.c"
    INCLUDE_DIRS "include"
    REQUIRES storage report power
)
