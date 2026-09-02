# Stale Page Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove refactor leftovers without changing any currently reachable page, route, or backend API behavior, then refresh the frontend bundle served by FastAPI.

**Architecture:** Treat `frontend/src/main.ts` and the Vue Router records as frontend roots, and `backend/main.py` as the backend root. Delete only files that remain outside those import/runtime graphs after accounting for lazy imports, Vue auto-components, styles, tests, and helper scripts copied by path.

**Tech Stack:** Vue 3, TypeScript, Vite 8, FastAPI, Python 3.13, pytest

**Spec:** `docs/superpowers/specs/2026-09-02-stale-page-cleanup.md`

## Global Constraints

- Preserve all current routes and active FastAPI endpoints.
- Preserve generated declarations, tests, knowledge data, backups, and documentation media.
- Rebuild the ignored `frontend/dist` directory after source cleanup.
- Do not stop or modify the unrelated CampusMate process on port 8000.

---

### Task 1: Establish the clean baseline and route map

**Files:**
- Inspect: `frontend/src/router/index.ts`
- Inspect: `frontend/src/router/learnRoutes.ts`
- Inspect: `frontend/src/modules/shared/moduleRegistry.ts`
- Inspect: `backend/main.py`

**Interfaces:**
- Consumes: Vue application entry and FastAPI application entry.
- Produces: Confirmed route/module sets and baseline test evidence.

- [x] **Step 1: Compare specialized and registry-driven learning module keys**

  Expected: four specialized keys, nine registry keys, and an empty overlap set.

- [x] **Step 2: Run the frontend baseline**

  Run: `npm run typecheck && npm run build`

  Expected: exit code 0 for both commands.

- [x] **Step 3: Run the backend fast baseline**

  Run: `python scripts/ci_test_runner.py fast`

  Expected: 171 passed and 18 deselected.

### Task 2: Remove unreachable frontend refactor leftovers

**Files:**
- Delete: `frontend/src/api/search.ts`
- Delete: `frontend/src/components/home/HomeSortDemo.vue`
- Delete: `frontend/src/components/learning/AlgorithmLearningMap.vue`
- Delete: `frontend/src/components/learning/AlgorithmUniverseGraph.vue`
- Delete: `frontend/src/components/learning/LearningPathDagViz.vue`
- Delete: `frontend/src/components/learning/LearningPathRoadmap.vue`
- Delete: `frontend/src/components/learning/LearningProgressRing.vue`
- Delete: `frontend/src/components/learning/PracticeOjLinks.vue`
- Delete: `frontend/src/composables/useGsapAnimations.ts`
- Delete: `frontend/src/composables/useGuidedTour.ts`
- Delete: `frontend/src/composables/useLearningActivity.ts`
- Delete: `frontend/src/composables/useLearningImpact.ts`
- Delete: `frontend/src/composables/useModuleAiExplain.ts`
- Delete: `frontend/src/composables/useUniverseGraphEnhancements.ts`
- Delete: `frontend/src/modules/games/composables/useGameLevel.ts`
- Delete: `frontend/src/utils/universeDagLayout.ts`
- Delete: `frontend/src/assets/home-quote-landscape.png`
- Delete: `frontend/src/assets/hero.png`
- Delete: `frontend/src/assets/vite.svg`
- Delete: `frontend/src/assets/vue.svg`
- Delete: `frontend/public/icons.svg`

**Interfaces:**
- Consumes: Reachability audit rooted at `frontend/src/main.ts`.
- Produces: A frontend source tree containing only reachable application code plus declarations and tests.

- [x] **Step 1: Recheck every candidate has no inbound reference outside the candidate set**

  Run: `rg` over `frontend/src`, excluding generated declaration files.

  Expected: only references among the obsolete universe-graph cluster itself.

- [x] **Step 2: Delete the confirmed orphaned text and media files**

  Expected: `git status --short` lists only the planned deletions and audit documents.

- [x] **Step 3: Repeat the reachability and asset-name scans**

  Expected: no unexplained unreachable application code or source assets.

### Task 3: Remove unreachable backend compatibility modules

**Files:**
- Delete: `backend/schemas/agent_outputs.py`
- Delete: `backend/services/ai_chat.py`

**Interfaces:**
- Consumes: Python AST import graph rooted at `backend/main.py` plus full-repository symbol search.
- Produces: Removal of two modules with no importer and no runtime path-based loader.

- [x] **Step 1: Confirm no imports or symbol references exist**

  Run: `rg -n "agent_outputs|ai_chat|validate_quiz_payload|QuizOutput" backend evaluation`

  Expected: matches only inside files scheduled for deletion.

- [x] **Step 2: Delete both modules**

  Keep `gdb_stl_extract.py` and `trace_serialize.py`: they are copied by filename at runtime and are false positives in a pure AST import scan.

### Task 4: Refresh the served bundle and run regressions

**Files:**
- Regenerate (ignored): `frontend/dist/**`
- Verify: `backend/main.py`

**Interfaces:**
- Consumes: Cleaned frontend source and existing FastAPI SPA fallback.
- Produces: A fresh deployment bundle and verification evidence.

- [x] **Step 1: Run frontend typecheck and all utility tests**

  Run: `npm run typecheck`, followed by every `test:*` script in `frontend/package.json`.

  Expected: all commands exit 0.

- [x] **Step 2: Rebuild the frontend bundle**

  Run: `npm run build`

  Expected: exit 0 and a newly generated `frontend/dist/index.html`.

- [x] **Step 3: Run backend fast tests**

  Run: `python scripts/ci_test_runner.py fast`

  Expected: 171 passed and 18 deselected.

- [x] **Step 4: Verify FastAPI SPA behavior against the rebuilt bundle**

  Check `/`, `/learning-path`, `/learn/array`, and `/learn/linked-list` return the rebuilt SPA index; check an unknown `/api/...` path returns JSON 404.

- [x] **Step 5: Review the final diff against this plan**

  Expected: no current router, page, API registration, test, database, backup, or knowledge file changed.
