import request from '@/utils/request'

export interface SemanticSearchResult {
  id: string
  kind: string
  title: string
  snippet: string
  module_key: string
  concept_ids: string[]
  node_ids: string[]
  score: number
  slug: string
  difficulty: string
}

export interface SemanticSearchResponse {
  query: string
  results: SemanticSearchResult[]
  highlight_node_ids: string[]
}

export async function semanticSearch(params: {
  q: string
  scope?: string
  module_key?: string
  difficulty?: string
  top_k?: number
}): Promise<SemanticSearchResponse> {
  const { data } = await request.get<SemanticSearchResponse>('/search/semantic', { params })
  return data
}
