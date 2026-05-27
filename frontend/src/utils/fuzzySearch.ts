import Fuse, { type IFuseOptions } from 'fuse.js'

/**
 * 对列表做 Fuse.js 模糊匹配（拼写容错、子串）。
 */
export function fuzzyFilter<T>(
  items: T[],
  query: string,
  keys: (keyof T & string)[] | string[],
  options?: IFuseOptions<T>,
): T[] {
  const q = query.trim()
  if (!q) return items
  const fuse = new Fuse(items, {
    keys: keys as string[],
    threshold: 0.42,
    ignoreLocation: true,
    ...options,
  })
  return fuse.search(q).map((hit) => hit.item)
}
