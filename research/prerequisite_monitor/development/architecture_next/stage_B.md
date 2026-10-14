# Stage B status

- **Conclusion:** Current primary-paper and official-code review supports relation verification as prior art and separates visual relation from strict necessity. ARS already implements event verification/crops; CoINS directly models obstacle-removal necessity with extra 3D/skill input. ProcVLM and PRIMO R1 are strong progress competitors but lack existing dedicated local weights.
- **Original evidence:** `literature_update.md`, `paper_learning_notes/`, `code_trace_update.md`, `source_to_design_matrix.md`; primary URLs and fixed local code commits are recorded there. ARS repository check on 2026-10-05 returned repository not found; original ARS **unrun**.
- **Strongest counterexample:** ARS short benchmark verification ablations nearly match full; a more elaborate verifier is not automatically useful here. CoINS already handles route necessity in another embodiment.
- **Gate:** passed for bounded learning and design choice, not for an originality or superiority claim. No paper found in two targeted rounds that was verified to use this exact fixed tabletop/same-goal/only-preparation-video six-condition construct; this is a search limit, not an absence proof.
- **Next single entry:** `method_hypothesis.md`, selecting one change whose benefit must survive same-backbone same-budget D2 and scene admission.
