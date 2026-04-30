# WTF Zoom Pipeline

Convert *Write to Freedom* Zoom call recordings into one Markdown document per client, matching the format under `examples/Examples/` (gitignored locally).

## Pipeline

1. **Transcribe** the call audio via AssemblyAI with speaker diarization.
2. **Resolve speakers** — map AssemblyAI's `Speaker A/B/C` to real names using Scott's on-mic introductions, the spoken self-intros, and the chat roster (`data/rosters/<date>.json`) as a candidate set. Note: the chat roster only includes people who *typed* in chat, so it is a seed, not the full attendee list.
3. **Segment** the call into per-client blocks via OpenAI Structured Outputs (strict schema: `pipeline.models.CallSegmentation`).
4. **Enrich** each segment with Distilled Advice, Key Principles, and Topics via OpenAI.
5. **Render** to Markdown via `pipeline.render.render(ClientResponseDoc)`.

## Layout

- `pipeline/` — library: `models`, `render`, `chat_parser`. (`transcribe`, `segment`, `enrich` are pending.)
- `scripts/` — runnable utilities (`parse_chats.py`, `smoke_render.py`).
- `data/rosters/<date>.json` — chat-derived attendee rosters per call.
- `data/transcripts/`, `data/output/` — gitignored runtime artifacts.
- `examples/` — Scott's recordings, hand-built example MDs, and the template (gitignored).
- `Test Project Instructions.md` — Scott's spec (gitignored).
- `upwork_msgs.txt` — running log of the Upwork conversation with Scott (gitignored).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env  # then fill ASSEMBLYAI_API_KEY and OPENAI_API_KEY
```

## Common commands

```bash
python scripts/parse_chats.py    # regenerate data/rosters/ from examples/<call>/chat.txt
python scripts/smoke_render.py   # verify the markdown renderer end-to-end
```

## Output filename pattern

`wtf_zoom-response_YYYY-MM-DD_lastname-firstname.md` — `YYYY-MM-DD` is the call date (matches the folder name and the `DATE:` metadata field).

## Project status

- **Stage 1 (offline modules):** done — schemas, renderer, chat parser.
- **Stage 2 (online modules):** pending Scott's reply with the AssemblyAI key and answers to the open questions in `upwork_msgs.txt`.
