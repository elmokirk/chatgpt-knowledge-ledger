# ChatGPT Knowledge Ledger

This repository is the neutral, public starter kit. Never add real exports, chats, user identifiers, local absolute paths, generated private vaults, or private change proposals.

Use stable source IDs for identity. Existing immutable evidence may only be accepted when its bytes are identical; different bytes at the same target are a conflict. Generated views may be rebuilt from canonical records. Unknown entities enter the candidate queue.

All generated chats require controlled `contexts` and `content_types`. Code blocks over 300 lines or 32 KiB become deterministic Level-4 artifacts. Skills and hooks remain under `.agents/`.

Before a commit run:

```powershell
python -m unittest discover -s tests -v
python scripts/public_preflight.py
```
