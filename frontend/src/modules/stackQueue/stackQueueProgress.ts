import { createSectionProgress } from '@/modules/shared/sectionProgress'

export const STACK_QUEUE_SECTION_STORAGE_KEY = 'alp-stack-queue-section-done-v1'
export const stackQueueProgress = createSectionProgress(STACK_QUEUE_SECTION_STORAGE_KEY)
