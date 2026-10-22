# Contexto de lecciones — ALMA ReviewBench
<!-- artifact: alma-lessons-context/1.0 | compiler: alma-lessons-compiler/1.0 -->
<!-- corpus: run298 claims=166 decisions-sha256: feebdc6e0aecf073dd81b7e1dabde670449932fbdef2d9e073a15174ea74651c -->
<!-- block-sha256: 2cdb32ced88785164491bda5f9cda72121b2be048ec18c7b3f236fa17a5bae6b | block-chars: 9052 -->

Artefacto generado por programa (`agent/lessons_compiler.py`) desde el corpus adjudicado de la corrida nº 298 — no editar a mano: la auditoría de procedencia lo re-deriva del corpus y cualquier edición rompe el hash declarado. El bloque entre marcadores es lo que el revisor v2.5 inyecta, verbatim, en sus prompts de producción.

<!-- LESSONS-BLOCK-BEGIN -->
LESSONS FROM THIS REVIEWER'S OWN ADJUDICATED HISTORY
(Run nº 298: 166 claims, each adjudicated against the public gold set. Dispositions recomputed deterministically through birth shaping -> claim contract -> gate 1.5.0. Every count and example below is traceable to a real adjudicated claim of that run.)

## How the claims died — counts
- Died at origin, asserted tokens absent from their own citation (`tokens_afirmados_ausentes_en_la_evidencia`): 32 of 166 (15 gold-tp, 3 gold-fpg, 4 gold-grey, 10 gold-novel)
- Died at origin, no concrete pattern declarable from the citation (`sin_patron_concreto_en_el_reclamo`): 54 of 166 (29 gold-tp, 1 gold-fpg, 5 gold-grey, 19 gold-novel)
- Rejected firmly by the gate (affirmative contradiction): 1 of 166 (1 gold-tp)
- Emitted: 79 of 166 (62 born declaring their pattern, 17 with the pattern declared at birth from the claim's own prose)
Of the 89 gold-true claims, 45 were never emitted — 44 died at origin and 1 was rejected. What decided emission was verifiability at birth, not truth.

## Dead on arrival — verbatim examples
### Example D1
<!-- src: run298 pr=AY2526S2-CS2103T-W14-3_tp_152-e0a9ce03 e=7 gold=TP disp=muerto_en_origen_tokens -->
Claim (verbatim): The user-facing contract still says notes are not persisted and only confirmed, but `NoteCommand.execute` now calls `model.setNote`, and the address book serializer writes notes to disk. Users are therefore given an obsolete persistence contract.
Citation: docs/UserGuide.md:335-335 — adjudicated verdict: TRUE POSITIVE (gold entry G29)
Cited lines (verbatim):
Records a date-bound note that will be persisted in future milestones. Currently, it validates syntax via CLI and confirms receipt.
Why it died: every token the claim asserted was absent from its own citation (absent: `NoteCommand.execute`, `model.setNote`). It was never emitted — the defect was in the claim, before any gate.

### Example D2
<!-- src: run298 pr=DisciplinedSoftware_Codebase-Conversion_1-4b46d68c e=0 gold=TP disp=muerto_en_origen_tokens -->
Claim (verbatim): The Rust benchmark never calls the converted function; it only black-boxes an input array. The resulting `rust_time_ms` and speedup therefore measure loop/black-box overhead rather than the Rust implementation.
Citation: fortran_to_rust/benchmarker.py:183-186 — adjudicated verdict: TRUE POSITIVE (gold entry G45)
Cited lines (verbatim):
    let start = Instant::now();
    for _ in 0..REPS {{
        // {fn_lower}({call_args});  // uncomment once the Rust signature is known
        std::hint::black_box(&{first_array});
Why it died: every token the claim asserted was absent from its own citation (absent: `rust_time_ms`). It was never emitted — the defect was in the claim, before any gate.

### Example D3
<!-- src: run298 pr=DisciplinedSoftware_Codebase-Conversion_1-4b46d68c e=3 gold=TP disp=muerto_en_origen_sin_patron -->
Claim (verbatim): For FUNCTION routines with array arguments, the Rust output order differs from the Fortran driver. Rust prints the return value before arrays, while the Fortran generator appends the return value after its existing array print loops, so equal-length streams are compared at the wrong positions.
Citation: fortran_to_rust/test_harness.py:553-560 — adjudicated verdict: TRUE POSITIVE (gold entry G43)
Cited lines (verbatim):
    // Safety: the generated function may be declared unsafe if the LLM used raw pointers.
    let _result = unsafe {{ {fn_lower}({call_args}) }};

    // Print return value
    println!("{{:.15e}}", _result as f64);

    // Print any array outputs
{rust_prints}
Why it died: the claim named no checkable pattern that stands in its cited lines, so nothing in it could be verified against its own evidence. It was never emitted.

### Example D4
<!-- src: run298 pr=DisciplinedSoftware_Codebase-Conversion_1-4b46d68c e=6 gold=TP disp=muerto_en_origen_sin_patron -->
Claim (verbatim): The function-call heuristic also scans the routine declaration itself, where the routine name is followed by `(`. Consequently every parsed routine is recorded as calling itself, producing spurious self-edges in the call graph and making topological ordering treat otherwise acyclic routines as cycles.
Citation: fortran_to_rust/parser.py:94-99 — adjudicated verdict: TRUE POSITIVE (gold entry G47)
Cited lines (verbatim):
        # Function calls (heuristic: any word followed by '(')
        for m2 in _FUNC_CALL.finditer(line):
            name = m2.group(1).upper()
            # Filter out Fortran keywords / intrinsics
            if name not in _FORTRAN_KEYWORDS:
                calls.add(name)
Why it died: the claim named no checkable pattern that stands in its cited lines, so nothing in it could be verified against its own evidence. It was never emitted.

### Example D5
<!-- src: run298 pr=scottlz0310_Mcp-Docker_29-e7705d26 e=1 gold=TP disp=rechazado_puerta -->
Claim (verbatim): GitHub returns OAuth denials such as `error=access_denied&state=...` without a `code`. This branch treats that valid upstream error callback as a malformed request and leaves the MCP client without an OAuth error response at its saved redirect URI, so cancellation/denial flows cannot complete correctly.
Citation: services/copilot-review-mcp/internal/auth/handler.go:130-133 — adjudicated verdict: TRUE POSITIVE (gold entry G33)
Cited lines (verbatim):
	if code == "" || state == "" {
		http.Error(w, "missing code or state", http.StatusBadRequest)
		return
	}
Why it died: the gate rejected it firmly — affirmative contradiction: the claim declares 'code' absent but the cited evidence contains it. The claim declared absent what its own citation contains — and the claim was TRUE.

## Born citable, emitted and true — verbatim examples
### Example L1
<!-- src: run298 pr=AA-Factory_aafactory-prototype_17-a1978cb7 e=0 gold=TP disp=emitido -->
Claim (verbatim): The test replaces `send_request_to_open_ai`, ostensibly the behavior under test, with a side effect that manufactures both the expected return value and `CHAT_HISTORY` mutation. Therefore none of the production implementation executes, and the assertions still pass if that implementation is completely broken.
Citation: aafactory/src/tests/test_chat/test_mock_chat.py:14-22 — adjudicated verdict: TRUE POSITIVE (gold entry G1)
Cited lines (verbatim):
    def llm_side_effect(*args, **kwargs):
        CHAT_HISTORY.append(["Hello", "Hi there!"])
        return ("", [["Hello", "Hi there!"]], "video_path.mp4")

    mocker.patch(
        "aafactory.chat.interface.send_request_to_open_ai",
        new_callable=mocker.AsyncMock,
        side_effect=llm_side_effect
    )
Why it lived: its pattern (`send_request_to_open_ai`, `CHAT_HISTORY`) was declared in backticks at birth and stands verbatim in the cited lines. It was emitted — and it was a true positive.

### Example L2
<!-- src: run298 pr=AA-Factory_aafactory-prototype_17-a1978cb7 e=1 gold=TP disp=emitido -->
Claim (verbatim): The loader mock is ineffective: the test patches the attribute on `aafactory.chat.interface` but then calls the directly imported `_load_avatar_infos_for_chat` reference, which was bound before the patch. This invokes the real loader instead of the configured mock, making the test dependent on real configuration or files and potentially causing it to fail before reaching its assertions.
Citation: aafactory/src/tests/test_chat/test_mock_chat.py:25-33 — adjudicated verdict: TRUE POSITIVE (gold entry G2)
Cited lines (verbatim):
    mocker.patch(
        "aafactory.chat.interface._load_avatar_infos_for_chat",
        return_value=(
            "Bot", "Friendly", "Knows stuff", "avatar_video.mp4",
            "elevenlabs", "voiceid", "path/to/rec", "transcript", "en", "avatar.png"
        )
    )

    avatar_info = _load_avatar_infos_for_chat()
Why it lived: its pattern (`aafactory.chat.interface`, `_load_avatar_infos_for_chat`) was declared in backticks at birth and stands verbatim in the cited lines. It was emitted — and it was a true positive.

## Rules distilled from the counts above
1. Before you assert a token in backticks, find it in the lines you cite; if it is not there, do not assert it. 32 of 166 claims died at origin because everything they asserted stood outside their citation (40 asserted tokens with no backing).
2. Copy your pattern out of your citation: a claim that names no token present in its cited lines is born unverifiable. 54 of 166 claims died that way.
3. This kills true claims, not just noise: 44 of the 89 gold-true claims were never emitted because they were born without a verifiable citation.
4. Never declare absent what your citation contains: the corpus's only firm rejection was a true claim killed by contradicting its own evidence.
5. What survived: 79 of 166 claims were emitted, and every one of them was born with its pattern standing in its citation. Cite first; assert only what the citation shows.
6. If the pattern is in your prose and in your citation, declare it in backticks at birth: 17 claims were rescued exactly that way and emitted.
<!-- LESSONS-BLOCK-END -->
