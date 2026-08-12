import request from '@/utils/request'

export interface LearningProgressDto {
  payload: Record<string, unknown>
}

export function fetchLearningProgress() {
  return request.get<unknown, LearningProgressDto>('/api/me/learning-progress')
}

export function saveLearningProgress(payload: Record<string, unknown>) {
  return request.put<unknown, LearningProgressDto>('/api/me/learning-progress', { payload })
}
