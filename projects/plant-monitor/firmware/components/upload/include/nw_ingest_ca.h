/* Pinned trust anchor for the ingest endpoint (ADR-004: "TLS with pinned CA bundle on the device"; NFR-06; security checklist 5.9, F-01).
 * nw_upload_idf.c trusts ONLY this PEM for the POST to /ingest, never the ESP-IDF certificate bundle.
 * A public CA certificate may be committed; a secret never is.
 * PLACEHOLDER: empty. While empty, the upload refuses to send (fail closed, logged as an error). The owner supplies the PEM of the CA
 * that issues the ingest host certificate, once the host is deployed. Do not paste a leaf certificate, and do not restore the bundle. */
#ifndef NW_INGEST_CA_H
#define NW_INGEST_CA_H

#define NW_INGEST_CA_PEM ""

#endif
