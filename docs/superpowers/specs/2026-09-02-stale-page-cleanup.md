# Stale Page Cleanup Specification

## Objective

Remove page, component, composable, asset, and backend compatibility files that are provably unreachable after the frontend refactor, with special attention to duplicate second-level learning pages and stale frontend bundles served by FastAPI.

## Safety rules

- Keep every Vue route that is registered by `src/router/index.ts`, `learnRoutes.ts`, or `gameRoutes.ts`.
- Keep files reached by static imports, dynamic imports, Vue component tags, CSS imports, or runtime helper-file copying.
- Do not remove active backend API routes merely because the current UI does not call them; they may be external interfaces.
- Do not remove database backups, knowledge content, test fixtures, generated type declarations, or documentation screenshots.
- Rebuild `frontend/dist` after cleanup because FastAPI serves that ignored directory whenever it exists.

## Confirmed findings

- The four specialized learning routes (`array`, `hash-table`, `string`, `two-pointers`) and nine registry-driven generic routes have no key overlap or duplicate route names.
- `LearningPathView.vue` now renders `LearningPathCommandCenter.vue`; the former universe-graph/roadmap/DAG implementation chain is unreachable from `main.ts`.
- `frontend/dist` is served by `backend/main.py` in non-frozen local runs, so it must be rebuilt to match the cleaned source tree.
- The process listening on port 8000 exposes `CampusMate AI Backend`; it is unrelated to this checkout. No process from this checkout was listening on 5173 or 9000 during the audit.

## Verification requirements

- Frontend typecheck exits successfully.
- Frontend production build exits successfully and recreates `dist` from scratch.
- All frontend utility tests listed in `package.json` pass.
- Backend fast test suite passes.
- A post-cleanup reachability scan reports no unexplained application-code or source-asset orphans.
- FastAPI test-client checks confirm SPA fallback serves the rebuilt index and deep routes, while unknown `/api` paths remain JSON 404 responses.
