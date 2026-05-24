import { ARRAY_SECTIONS } from '@/modules/array/arrayCurriculum'
import { loadSectionDone as loadArrayDone } from '@/modules/array/arrayProgress'
import { STRING_SECTIONS } from '@/modules/string/stringCurriculum'
import { loadSectionDone as loadStringDone } from '@/modules/string/stringProgress'
import { TWO_POINTERS_SECTIONS } from '@/modules/twoPointers/twoPointersCurriculum'
import { loadSectionDone as loadTwoPointersDone } from '@/modules/twoPointers/twoPointersProgress'
import { HASH_SECTION_IDS } from '@/modules/hashTable/hashTableCurriculum'
import { hashTableProgress } from '@/modules/hashTable/hashTableProgress'
import { MODULE_LEARN_CONFIGS } from '@/modules/shared/moduleRegistry'

export type ModuleProgressSource = {
  sectionIds: string[]
  loadDone: () => Record<string, boolean>
}

/** 各模块学习进度数据源（本地小节完成度） */
export const MODULE_PROGRESS_SOURCES: Record<string, ModuleProgressSource> = {
  array: {
    sectionIds: ARRAY_SECTIONS.map((s) => s.id),
    loadDone: loadArrayDone,
  },
  string: {
    sectionIds: STRING_SECTIONS.map((s) => s.id),
    loadDone: loadStringDone,
  },
  'two-pointers': {
    sectionIds: TWO_POINTERS_SECTIONS.map((s) => s.id),
    loadDone: loadTwoPointersDone,
  },
  'hash-table': {
    sectionIds: HASH_SECTION_IDS,
    loadDone: hashTableProgress.loadSectionDone,
  },
  ...Object.fromEntries(
    Object.values(MODULE_LEARN_CONFIGS).map((cfg) => [
      cfg.key,
      {
        sectionIds: cfg.sections.map((s) => s.id),
        loadDone: cfg.loadSectionDone,
      },
    ]),
  ),
}
