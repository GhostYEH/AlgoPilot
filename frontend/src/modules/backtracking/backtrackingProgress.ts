import { createSectionProgress } from '@/modules/shared/sectionProgress'

export const BACKTRACKING_SECTION_STORAGE_KEY = 'alp-backtracking-section-done-v1'
export const backtrackingProgress = createSectionProgress(BACKTRACKING_SECTION_STORAGE_KEY)
