const STORAGE_KEY = 'alp-oj-favorites'

function loadFavorites(): string[] {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '[]')
    return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : []
  } catch {
    return []
  }
}

export function isOjFavorite(slug: string): boolean {
  return loadFavorites().includes(slug)
}

export function toggleOjFavorite(slug: string): boolean {
  const favorites = new Set(loadFavorites())
  if (favorites.has(slug)) favorites.delete(slug)
  else favorites.add(slug)
  localStorage.setItem(STORAGE_KEY, JSON.stringify([...favorites]))
  return favorites.has(slug)
}
