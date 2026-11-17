set(req sensors provisioning)
if(CONFIG_PLANT_UPLOAD)
    list(APPEND req upload)    # hourly upload adapter (4.F3 slice 3), off by default
endif()
idf_component_register(SRCS "main.c" INCLUDE_DIRS "." REQUIRES ${req} PRIV_REQUIRES driver esp_system)
