# Absorb trigger (LORE-071)

The absorb trigger is a read-only ingestion layer. It converts two machine
exports into `lore.evidence.EvidenceBlock` values and passes them to the
existing `absorb_sweep` function. `absorb_sweep` returns in-memory proposal
objects; it does not publish or modify a runbook.

## Board events

`BoardEventWatcher(board, JsonCursorStore(cursor_path))` reads a board's
`events.jsonl` by byte offset. It accepts `task_completed` records and any
other record carrying an explicit `class_id` or lesson. The cursor is written
only after the complete suffix has been parsed successfully, using an atomic
replace. A restart therefore resumes at the saved offset and does not replay
seen records. The board itself is never opened for writing.

The cursor path is owner-managed local state; it is not a board file and should
not be placed inside `.coding-hermes/` when installing a service.

## Auger export

`AugerDecisionTableAdapter(path).read()` reads Auger's deterministic Markdown
`export` output and returns the parsed evidence blocks; it performs no Auger or
DuckBrain writes. Decision, assumption, unknown, and break rows become
`duckbrain-row` evidence. Provenance is explicit, for example:

```text
source=auger:decisions:D-001
fields.table=decisions
fields.row_id=D-001
```

The adapter reads an export file only. It does not connect to or write a
DuckBrain store.

## Proposal-only integration

```python
from lore.absorb import absorb_sweep
from lore.trigger import BoardEventWatcher, JsonCursorStore

blocks = BoardEventWatcher(
    "/path/to/.coding-hermes/board/events.jsonl",
    JsonCursorStore("/var/lib/lore/board-cursor.json"),
).consume()
proposals = absorb_sweep(blocks, source="board-event")
```

The returned `proposals` are for operator review. No timer or service is
installed by this package. An owner may run the watcher from a separately
managed process after choosing a cursor location and review workflow.

Fixtures and tests use copies under `tests/fixtures/`; they never read live
boards or `~/.duckbrain`.
