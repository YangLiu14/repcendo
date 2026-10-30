# Repcendo

When generating a training plan or adjusting one from exported feedback, read `docs/codex-plans.md` first. Deliver a JSON file that passes the `plan-check` command documented there.

Keep planned targets separate from actual training records. Plan updates must preserve completed sessions and the in-progress session's original snapshot.

`third_party/exercises-dataset` is a pinned upstream submodule. Transform its text data with `Scripts/prepare_resources.py`; keep media out of the App bundle until separately licensed. After adding App source files, update the checked-in Xcode project with `Scripts/generate_project.py`.

Before modeling or revising exercise equipment, inspect a real product photo online and follow `docs/equipment-references/README.md`. Preserve the observed support layout and mechanism, and compare rendered key poses with that reference before approving the animation.
