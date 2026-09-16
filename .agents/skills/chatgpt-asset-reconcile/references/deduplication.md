# Deduplication

Full byte equality is required before treating two payloads as identical. Pilot mode retains duplicates. Production reuses an identical vault payload and sends a verified source duplicate to the Recycle Bin only after a receipt; permanent deletion is forbidden.
