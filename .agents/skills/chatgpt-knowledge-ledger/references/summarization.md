# Summarization

Summarize only new or updated chats. Use the model and reasoning effort from the private `scheduler.config.json`; defaults are `gpt-6-luna` and `low`.

Return plain text supported by the retrieved messages:

- `summary`: durable chat context, at most 10 short sentences and `chat_max_chars`.
- `moc_summary`: what changed in this run, at most 3 short sentences and `moc_max_chars`.

Keep generated summaries outside RAW evidence and pass their JSON file to `run_manual_scheduler.py` with `--summaries`. Use a `records` object keyed by `chat_id`, with `chat_summary` and `moc_summary` values.

Prefer goal, action, result, decision, and current state. Omit greetings, links, code, file inventories, source lists, and process narration. Do not copy a message verbatim when a shorter factual statement preserves its meaning.

On updates, use the existing summary plus the new message delta. Never reread or resummarize an unchanged chat. The renderer applies a deterministic final bound; 3000 characters is the non-configurable safety ceiling for any summary.
