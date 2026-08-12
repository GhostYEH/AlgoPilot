import { createSectionProgress } from '@/modules/shared/sectionProgress'

export const LINKED_LIST_SECTION_STORAGE_KEY = 'alp-linked-list-section-done-v1'
export const linkedListProgress = createSectionProgress(LINKED_LIST_SECTION_STORAGE_KEY)

/** @deprecated 请使用 linkedListProgress.loadSectionDone */
export const loadSectionDone = linkedListProgress.loadSectionDone

/** @deprecated 请使用 linkedListProgress.toggleSectionDone */
export const toggleSectionDone = linkedListProgress.toggleSectionDone
