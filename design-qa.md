# Product Design QA — 教师资源工作台与 OJ 管理

- Source visual truth: `C:\Users\32883\AppData\Local\Temp\codex-clipboard-f349658b-6c7b-4fec-a23f-5a1874edeeb2.png` and `C:\Users\32883\AppData\Local\Temp\codex-clipboard-ebf42ce3-9f04-47fe-b401-8b5145fdb6f4.png`
- Implementation routes: `http://127.0.0.1:5173/teacher-workbench` and `http://127.0.0.1:5173/oj-admin`
- Implementation screenshots: Chrome DevTools viewport captures attached to this task (the browser connector did not permit persisting them to the workspace)
- Viewport: 2000 × 1217 desktop, light theme, authenticated as `teacher_demo`
- State: six existing generated resources loaded; OJ list loaded with 126 problems

## Full-view comparison evidence

The supplied teacher screenshot showed the document scrolling together with the left navigation and raw Agent JSON in the resource drawer. The implementation keeps the shell at one viewport, confines scrolling to `.teacher-shell .app-main`, and renders generated content through `ResourceContentPreview`. A runtime coordinate check before and after scrolling kept the sidebar at `top: 0`, `bottom: 1089.6`, with `window.scrollY: 0`.

The supplied OJ screenshot constrained the workspace to a 1280 px centered column and a 560 px table. The implementation uses the full post-sidebar width and available viewport height, with a four-card summary row, full-width filters, translated module/difficulty labels, and a vertically scrolling table.

## Focused region comparison evidence

- Resource drawer: the reading resource now exposes three named levels, audience, material title, reason, and post-reading task instead of a JSON blob.
- Resource cards: embedded JSON is parsed to human-readable summaries; quizzes show question counts and domain resources show their narrative headline.
- OJ table: header, status tags, row actions, and long slug/title columns were inspected at desktop width. The redundant fixed action column and wide-screen horizontal scrollbar were removed.

## Required fidelity surfaces

- Fonts and typography: retained the existing AlgoPilot Chinese font stack and hierarchy; table labels, metadata, titles, and counts remain legible and consistent.
- Spacing and layout rhythm: preserved the existing 196 px teacher rail and product spacing tokens; OJ content now fills the working canvas without excessive empty margins.
- Colors and visual tokens: all new surfaces, borders, states, and highlights use existing `--alp-*` tokens and the established teal brand color.
- Image quality and assets: neither target screen contains imagery requiring generation; existing Element Plus icons are retained consistently.
- Copy and content: raw internal field names are replaced with teacher-facing labels; module and difficulty values are presented in Chinese.
- Responsiveness: summary cards collapse to two columns below 1100 px; filters and actions stack below 720 px; the teacher rail retains its existing compact/mobile modes.
- Interaction and accessibility: search, module filtering, clear-filter feedback, refresh, dialogs, preview drawer, and resource-type interactions remain functional. The overview section has an accessible region label.

## Findings

No actionable P0, P1, or P2 findings remain in the verified desktop states.

## Patches made since the previous QA pass

- Replaced raw `v-html` resource output with the existing structured resource renderer.
- Added balanced embedded-JSON extraction for legacy resources with appended verification notes.
- Isolated teacher main scrolling from the fixed navigation rail.
- Rebuilt OJ management as a full-width/full-height workspace with overview metrics and responsive filters.
- Removed the fixed action column and suppressed its redundant desktop horizontal scrollbar.

## Follow-up polish

- P3: generated placeholder wording such as “阅读目标” comes from existing backend resource content; improving prompt/template quality can make example resources more specific without changing this UI.

final result: passed
