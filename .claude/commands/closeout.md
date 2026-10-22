Session close-out. This session never commits, pushes, tags or amends.
1. Update HANDOFF.md of the module you worked in: stage and pass, last verified result with source, open items (each with how it will be settled), open decisions (K links), next step. Decisions taken this session go to docs\DECISIONS.md (append-only, K<nn>). Do not write commit state (no HEAD hash, no "committed/uncommitted").
2. Append one entry to docs\DEVLOG.md: date, task, change, labelled results.
3. Print the /report format.
4. Under "Commit'e hazır yollar" in HANDOFF.md write the explicit list of paths changed in this session (from git status --short). Do not stage anything. The commit is a separate coordinator ticket in 00_coordination, run from the pipeline root.
