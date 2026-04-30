# Write to Freedom — Test Project

Pipeline for converting *Write to Freedom* Zoom call recordings into structured per-client Markdown documents matching the format under `Example Outputs/Examples/`.

## Pipeline

Six steps, all under `pipeline/`:

1. **`transcribe`** (AssemblyAI Universal, speaker diarization on) — full transcript cached to `data/transcripts/<call-date>.json`.
2. **`cleanup`** — two pre-segmentation transformations:
   - merges 1–3 word diarization microbursts back into the surrounding speaker (AssemblyAI occasionally flips speakers for one or two words mid-monologue);
   - splits long Scott monologues (a single 5–15 min utterance can cover one client's wrap-up, the next client's introduction, *and* a read-through of their submission) into ~120-word chunks at sentence boundaries with linearly-interpolated timestamps, so the segmentation pass can place tight boundaries.
3. **`segment`** (`gpt-4.1`, Structured Outputs, strict schema) — single call resolves AssemblyAI's anonymous speaker labels (A/B/C/...) to real names *and* partitions the call into per-client review segments. The Zoom `chat.txt` attendee roster is fed in as a candidate seed set. Prompt enforces tight boundaries (no broader call preamble per Scott's instruction).
4. **`enrich`** (`gpt-4.1`, Structured Outputs, strict schema) — per-segment call producing `client_question`, `distilled_advice`, `key_principles`, and `topics`.
5. **`polish`** — regex pass over each transcript turn: strips `uh`/`um`/`ah` filler, collapses adjacent identical word and 2/3-word phrase repetitions ("I, I think it's, I think it's true" → "I think it's true"). Preserves Scott's words otherwise (no removal of `you know` / `like` since those carry meaning).
6. **`render`** — emits Markdown matching the section structure and separator style of the example MDs.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env   # fill ASSEMBLYAI_API_KEY and OPENAI_API_KEY
python run.py "examples/<call-folder>"
```

Each call writes one MD per client into `data/output/`. Re-runs are cheap: the AssemblyAI transcript is cached, so only OpenAI is paid on subsequent runs.

## Deliverables

- **40 Markdown files** in `data/output/` (one per client per call).
- **Pipeline source** under `pipeline/` and `run.py`.
- **Cached AssemblyAI transcripts** under `data/transcripts/` (8 JSON files; raw diarized utterances).
- **Per-call attendee rosters** at `data/rosters/` (parsed from `chat.txt`).

## Cost

~$5 total for all 8 calls:

- AssemblyAI Universal: 13.2 audio-hours × $0.27/hr ≈ **$3.60**
- OpenAI `gpt-4.1` (segment + enrich passes): **~$1.50**

Re-running with the same transcripts costs only the OpenAI portion.

## Assumptions made (where the spec didn't specify)

1. **Filename/`DATE` = call date** (the date in the folder name), not the date the MD was generated. Verified consistent across all five example MDs you provided.
2. **`PROGRAM` = "Write to Freedom"** and **`CONTENT_TYPE` = "Zoom Response"** are hardcoded.
3. **One MD per client per call**, even if the client asks two distinct questions — segments belonging to the same client within a call are merged into one MD with concatenated advice. (Per the spec: "one Markdown file per client (usually each client asks one question, but they may contain a couple questions)".)
4. **Topics field is AI-generated** alongside Distilled Advice and Key Principles. The spec explicitly authorized AI for the latter two; I extended to Topics since the examples clearly use them.
5. **Transcript scope** = tight to the client's question and Scott's answer, no broader call preamble (per Scott's confirmation: "each file should try to capture the client's concise question. No need for a broader lead in.").
6. **Transcripts have light filler removal** — `uh`/`um`/`ah` stripped and word/phrase stutters collapsed (per Scott's confirmation: "drop the 'uh' stutters"). Other potential fillers (`you know`, `like`, `I mean`) are preserved since they often carry meaning.

## Edge cases handled

- **Diarization microbursts** — 1–3 word utterances mis-attributed mid-monologue ("we", "how" inside a Scott block) are folded back into the surrounding speaker.
- **Long Scott monologues** — utterances exceeding ~120 words are split at sentence boundaries before segmentation so the LLM can place tight per-client boundaries instead of inheriting AssemblyAI's coarse atomic chunks.
- **Same-client multiple questions** — grouped into one MD per `(client, call)` rather than two files (which would have silently overwritten each other since they share a slug).
- **Missing or "Unknown" name parts** — the slug drops empty / placeholder components (`robin.md` rather than `_-robin.md`; `christoph.md` rather than `unknown-christoph.md`).
- **Client reviewed in absentia** (not on the call) — segment captures Scott's monologue only; no fake client utterances.
- **Client joins late** (e.g., Ann Socolofsky on 2025-04-16, who Scott had given up on before she joined) — preamble + arrival + Q&A all captured in one segment.
- **Filler words and stutters** — `uh`/`um`/`ah` stripped, adjacent word and 2/3-word phrase repetitions collapsed (`"I, I think, I think it's true"` → `"I think it's true"`).

## Edge cases observed but not auto-corrected

Flagging for transparency. Each is fixable but I chose to leave them as-is for the test deliverable — most need a decision from you.

1. **Cross-call name spelling drift.** AssemblyAI auto-transcribes names from audio, so the same person can show up under two spellings across calls. Examples in this deliverable:
   - **Tina Constant** (2025-04-02) vs. **Tina Konstant** in your manual `2026-04-08` example.
   - **Patrick Stall** (2025-03-05) vs. **Patrick Stoll** (2025-03-26).
   - **Sheryl Twitty** (2025-02-26) vs. **Cheryl Twitty** (2025-03-13).
   - **John Lindholm** (chat roster) vs. **Jonathan Lindholm** (audio).
   - **Victoria 'AntiNovelist'** (2025-04-02 — chat handle) vs. **Victoria Crowder** (2025-04-09 — real name).

   Fixable with a master client roster from you (one CSV with canonical names + aliases) — the segment pass would then snap to canonical names.
2. **Soft boundary leak at transitions.** Scott's farewell to the previous client (e.g., "Of course. All right, keep going, Gloria. Good job.") occasionally lands at the very start of the next client's segment, because both fall inside the same long-utterance chunk. Average leak is ~1 sentence — cosmetic. The first segment of each call may also include a bit of Scott's opening riffing before the named client's review begins, since the LLM can't always tell where preamble ends and the first review begins.
3. **AssemblyAI speaker conflation.** On calls with 5+ live speakers, AssemblyAI's diarizer sometimes lumps two clients into one speaker label. Visible on 2025-03-05: Christoph's lines are mis-labeled `Patrick Stall:` in the transcript because the diarizer didn't separate the two voices. The segmenter can't repair this — the error is upstream. Mitigations would be (a) Slam-1 model (slightly better diarization, +$0.10/hr) or (b) a per-speaker word-level confidence pass.

## Open questions sent to you on Upwork

All five are now confirmed:

1. ✅ AssemblyAI API key — resolved (used $50 free trial).
2. ✅ Transcript polish — confirmed: drop the `uh` stutters. Implemented in `pipeline/polish.py`.
3. ✅ Segment scope — confirmed: capture the client's concise question, no broader lead-in. Prompt tightened in `pipeline/segment.py`.
4. ✅ Topics field — confirmed AI-generated via OpenAI.
5. ✅ Repeat clients across calls — confirmed one MD per `(client, call)`.

Ready for your review.
