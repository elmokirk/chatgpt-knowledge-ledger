# Live sync

Process ChatGPT conversations only, deduplicate by `chat_id`, and enforce the 50-item overlap coverage guard. Live sync is a delta source, never the historic completeness baseline.

For each new or updated chat, apply [summarization.md](summarization.md) before rendering. Store `summary` and `moc_summary` separately; never use an unbounded message preview as either value.
