# Contexto de ausencias — ALMA ReviewBench
<!-- artifact: alma-absence-context/1.0 | compiler: alma-absence-compiler/1.0 -->
<!-- corpus: run298 gold-tp=352 touched=66 absent=286 decisions-sha256: feebdc6e0aecf073dd81b7e1dabde670449932fbdef2d9e073a15174ea74651c -->
<!-- block-sha256: be712a35ba052806c51622bd861e5bd8fa57b44a68b038221651c8c8b913fb2f | block-chars: 8427 -->

Artefacto generado por programa (`agent/absence_compiler.py`) desde el oro público y la adjudicación grounded de la corrida nº 298 — no editar a mano: la auditoría de procedencia lo re-deriva de las fuentes y cualquier edición rompe el hash declarado. Hermano de `CONTEXTO-LECCIONES.md`: aquel destila los reclamos que nacieron; este, los defectos verdaderos que nunca fueron reclamados.

<!-- ABSENCE-BLOCK-BEGIN -->
WHAT THIS REVIEWER NEVER CLAIMED — ABSENCE LESSONS FROM ITS OWN ADJUDICATED HISTORY
(Run nº 298, grounded adjudication against the public gold set: of 352 true defects, 66 were claimed and 286 were never claimed. Absence is adjudicated by the benchmark's own matching: a true defect counts as claimed only when a finding was adjudicated as that very defect.)

## The absences — counts
- Never claimed, in a file the reviewer never emitted on in that PR (A1): 104 of 286 absences (36.4%)
- Never claimed, in a file the reviewer did emit on (A2): 182 of 286 (63.6%); in 54 of those, one of its claims points at lines overlapping the missed defect
- Grazed but not claimed: 11 absent defects were referenced by a finding the adjudication filed as grey-zone, not as the defect itself
- PRs with the most absences: cmik_apilix_12-0c34439a (29 of 36); DisciplinedSoftware_Codebase-Conversion_1-4b46d68c (26 of 31); scotthamilton77_agents-config_1-1fc78970 (24 of 25); gagneurlab_PROTRIDER_10-b462b109 (19 of 21); scottlz0310_Mcp-Docker_29-e7705d26 (16 of 22)
- By category:
  - accessibility: 7 of 10 true defects never claimed (70.0%)
  - api-architecture: 12 of 12 true defects never claimed (100.0%)
  - correctness: 100 of 133 true defects never claimed (75.2%)
  - documentation: 18 of 21 true defects never claimed (85.7%)
  - maintainability: 44 of 44 true defects never claimed (100.0%)
  - performance: 7 of 12 true defects never claimed (58.3%)
  - reliability: 49 of 58 true defects never claimed (84.5%)
  - security: 23 of 27 true defects never claimed (85.2%)
  - testing: 26 of 35 true defects never claimed (74.3%)
- By context required:
  - broader-project-context: 14 of 17 true defects never claimed (82.4%)
  - diff-only: 94 of 115 true defects never claimed (81.7%)
  - diff-plus-related-files: 178 of 220 true defects never claimed (80.9%)
- By scope:
  - exacerbated-by-pr: 12 of 14 true defects never claimed (85.7%)
  - introduced-by-pr: 251 of 315 true defects never claimed (79.7%)
  - pre-existing: 23 of 23 true defects never claimed (100.0%)
- By difficulty:
  - easy: 148 of 174 true defects never claimed (85.1%)
  - hard: 13 of 19 true defects never claimed (68.4%)
  - medium: 125 of 159 true defects never claimed (78.6%)

## Missed true defects — verbatim examples
### Example A1-1
<!-- src: gold298 pr=AY2526S2-CS2103T-W14-3_tp_152-e0a9ce03 g=0 family=A1_archivo_nunca_visitado -->
Missed defect (verbatim, from the public gold set): DeleteNoteCommand.execute() is a stub that does not remove any note from the model. It only returns a success message ('Delete note request received for date: %1$s') without calling any model operation. The note is never actually deleted. This makes the advertised `note d-/DATE` feature entirely non-functional.
Location: src/main/java/seedu/address/logic/commands/DeleteNoteCommand.java:35-38 — category: correctness; context required: diff-only; scope: pre-existing; difficulty: easy; severity: high.
What the reviewer did on this PR instead: it emitted 12 claims, on 9 file(s) — docs/UserGuide.md, src/main/java/seedu/address/logic/commands/NoteCommand.java, src/main/java/seedu/address/model/AddressBook.java, src/main/java/seedu/address/model/location/NoteContent.java, src/main/java/seedu/address/storage/JsonSerializableAddressBook.java, src/test/java/seedu/address/logic/LogicManagerTest.java, src/test/java/seedu/address/logic/commands/NoteCommandTest.java, src/test/java/seedu/address/model/AddressBookTest.java, src/test/java/seedu/address/storage/JsonSerializableAddressBookTest.java — and never on this file.

### Example A1-2
<!-- src: gold298 pr=AY2526S2-CS2103T-W14-3_tp_152-e0a9ce03 g=4 family=A1_archivo_nunca_visitado -->
Missed defect (verbatim, from the public gold set): execute_deleteNote_success() uses an empty model and an empty expectedModel, so the test trivially passes without exercising deletion. A note added before the command would still be present in the model after execution, but this is never verified. The test provides no coverage of the core delete behavior.
Location: src/test/java/seedu/address/logic/commands/DeleteNoteCommandTest.java:24-29 — category: testing; context required: diff-only; scope: pre-existing; difficulty: easy; severity: low.
What the reviewer did on this PR instead: it emitted 12 claims, on 9 file(s) — docs/UserGuide.md, src/main/java/seedu/address/logic/commands/NoteCommand.java, src/main/java/seedu/address/model/AddressBook.java, src/main/java/seedu/address/model/location/NoteContent.java, src/main/java/seedu/address/storage/JsonSerializableAddressBook.java, src/test/java/seedu/address/logic/LogicManagerTest.java, src/test/java/seedu/address/logic/commands/NoteCommandTest.java, src/test/java/seedu/address/model/AddressBookTest.java, src/test/java/seedu/address/storage/JsonSerializableAddressBookTest.java — and never on this file.

### Example A2-1
<!-- src: gold298 pr=AA-Factory_aafactory-prototype_17-a1978cb7 g=3 family=A2_archivo_visitado_no_reclamado -->
Missed defect (verbatim, from the public gold set): `send_request_to_open_ai` is called with 10 positional arguments, but its real signature (aafactory/src/aafactory/fetcher/fetching.py) is `send_request_to_open_ai(messages: list[dict[str, str]])` — a single parameter. The arguments passed don't match the actual API, so the mock is being exercised with a completely wrong call shape; if patching ever failed, this would raise a TypeError immediately.
Location: aafactory/src/tests/test_chat/test_mock_chat.py:35-37 — category: testing; context required: diff-plus-related-files; scope: introduced-by-pr; difficulty: easy; severity: medium.
What the reviewer did on this PR instead: it emitted 4 claims, 4 of them on this very file. One of them (verbatim):
The test replaces `send_request_to_open_ai`, ostensibly the behavior under test, with a side effect that manufactures both the expected return value and `CHAT_HISTORY` mutation. Therefore none of the production implementation executes, and the assertions still pass if that implementation is completely broken.
(That claim points at aafactory/src/tests/test_chat/test_mock_chat.py:14-22; the missed defect lives at 35-37.)

### Example A2-2
<!-- src: gold298 pr=AA-Factory_aafactory-prototype_17-a1978cb7 g=4 family=A2_archivo_visitado_no_reclamado -->
Missed defect (verbatim, from the public gold set): `llm_side_effect` returns a 3-tuple `('', [['Hello', 'Hi there!']], 'video_path.mp4')`, but the real `send_request_to_open_ai` returns a plain string (the cleaned LLM text). If `send_request_to_llm` were actually called, `text_response` would be this tuple and the subsequent call `send_request_to_elevenlabs(text_response, voice_id)` would receive a tuple instead of a string, breaking the real code path the mock is supposed to stand in for.
Location: aafactory/src/tests/test_chat/test_mock_chat.py:13-21 — category: testing; context required: diff-plus-related-files; scope: introduced-by-pr; difficulty: easy; severity: medium.
What the reviewer did on this PR instead: it emitted 4 claims, 4 of them on this very file. One of them (verbatim):
The test replaces `send_request_to_open_ai`, ostensibly the behavior under test, with a side effect that manufactures both the expected return value and `CHAT_HISTORY` mutation. Therefore none of the production implementation executes, and the assertions still pass if that implementation is completely broken.
(That claim points at aafactory/src/tests/test_chat/test_mock_chat.py:14-22; the missed defect lives at 13-21.)

## Rules distilled from the counts above
1. Sweep the files you did not flag: 104 of 286 missed true defects (36.4%) sat in files you never emitted on in that PR. Silence on a file is not a verdict on it.
2. Your largest blind spot by count is correctness: 100 of 133 true correctness defects were never claimed (75.2%). When a change touches that surface, slow down.
3. Most misses needed diff-plus-related-files: 178 of 220 such defects were never claimed (80.9%). Do not judge a hunk without the context its defect class needs.
4. The scope you miss most, proportionally, is pre-existing: 23 of 23 never claimed (100.0%). A defect does not have to be born in this diff to be yours to report.
5. You can stand on the very lines and still miss it: in 54 absences, one of your claims pointed at lines overlapping the missed defect. When you flag a line, ask what else those lines break.
<!-- ABSENCE-BLOCK-END -->
