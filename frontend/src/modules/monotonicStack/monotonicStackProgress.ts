import { createSectionProgress } from '@/modules/shared/sectionProgress'

export const MONOTONIC_STACK_SECTION_STORAGE_KEY = 'alp-monotonic-stack-section-done-v1'
export const monotonicStackProgress = createSectionProgress(MONOTONIC_STACK_SECTION_STORAGE_KEY)
