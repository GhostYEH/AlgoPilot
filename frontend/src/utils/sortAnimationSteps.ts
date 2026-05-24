/** 首页排序可视化：每帧为完整数组快照 + 高亮下标（保证与算法一致） */

export type SortAnimStep = {
  values: number[]
  active: number[]
  /** 快速排序当前枢轴下标 */
  pivot?: number
}

function pushCompare(steps: SortAnimStep[], arr: number[], i: number, j: number) {
  steps.push({ values: [...arr], active: [i, j] })
}

function pushSwap(steps: SortAnimStep[], arr: number[], i: number, j: number) {
  ;[arr[i], arr[j]] = [arr[j], arr[i]]
  steps.push({ values: [...arr], active: [i, j] })
}

/** 升序冒泡排序：相邻比较，大者后移 */
export function bubbleSortSteps(initial: number[]): SortAnimStep[] {
  const arr = [...initial]
  const steps: SortAnimStep[] = []
  const n = arr.length

  for (let end = n - 1; end > 0; end--) {
    let swapped = false
    for (let j = 0; j < end; j++) {
      pushCompare(steps, arr, j, j + 1)
      if (arr[j] > arr[j + 1]) {
        pushSwap(steps, arr, j, j + 1)
        swapped = true
      }
    }
    if (!swapped) break
  }

  steps.push({ values: [...arr], active: [] })
  return steps
}

/** 升序选择排序：每轮将最小元放到未排序段前端 */
export function selectionSortSteps(initial: number[]): SortAnimStep[] {
  const arr = [...initial]
  const steps: SortAnimStep[] = []
  const n = arr.length

  for (let i = 0; i < n - 1; i++) {
    let minIdx = i
    for (let j = i + 1; j < n; j++) {
      pushCompare(steps, arr, minIdx, j)
      if (arr[j] < arr[minIdx]) minIdx = j
    }
    if (minIdx !== i) pushSwap(steps, arr, i, minIdx)
  }

  steps.push({ values: [...arr], active: [] })
  return steps
}

/** 升序快速排序（Lomuto 分区，末元为枢轴） */
export function quickSortSteps(initial: number[]): SortAnimStep[] {
  const arr = [...initial]
  const steps: SortAnimStep[] = []

  function partition(lo: number, hi: number): number {
    const pivotIdx = hi
    const pivotVal = arr[pivotIdx]
    steps.push({ values: [...arr], active: [pivotIdx], pivot: pivotIdx })

    let i = lo
    for (let j = lo; j < hi; j++) {
      pushCompare(steps, arr, j, pivotIdx)
      if (arr[j] < pivotVal) {
        if (i !== j) pushSwap(steps, arr, i, j)
        i++
      }
    }
    if (i !== pivotIdx) pushSwap(steps, arr, i, pivotIdx)
    steps.push({ values: [...arr], active: [i], pivot: i })
    return i
  }

  function quick(lo: number, hi: number) {
    if (lo >= hi) return
    const p = partition(lo, hi)
    quick(lo, p - 1)
    quick(p + 1, hi)
  }

  if (arr.length > 0) quick(0, arr.length - 1)
  steps.push({ values: [...arr], active: [] })
  return steps
}
