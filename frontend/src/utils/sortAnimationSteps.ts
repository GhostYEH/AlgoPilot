/** 首页排序可视化：每帧为完整数组快照 + 高亮下标（保证与算法一致） */

export type SortAnimStep = {
  values: number[]
  active: number[]
  /** 快速排序当前枢轴下标 */
  pivot?: number
  /** 归并排序当前合并区间 [lo, hi] */
  range?: [number, number]
  /** 堆排序当前有效堆长度 */
  heapSize?: number
  /** 已排序后缀起始下标（堆排序/冒泡排序等，index >= sortedFrom 已就位） */
  sortedFrom?: number
  /** 已排序前缀结束下标（选择排序/插入排序等，index <= sortedUntil 已就位） */
  sortedUntil?: number
  /** 每个元素的附加标签（用于区分相同值，如稳定性演示） */
  tags?: string[]
  /** 步骤说明文字 */
  hint?: string
}

function pushCompare(
  steps: SortAnimStep[],
  arr: number[],
  i: number,
  j: number,
  extra?: Partial<SortAnimStep>,
) {
  steps.push({ values: [...arr], active: [i, j], ...extra })
}

function pushSwap(
  steps: SortAnimStep[],
  arr: number[],
  i: number,
  j: number,
  extra?: Partial<SortAnimStep>,
) {
  ;[arr[i], arr[j]] = [arr[j], arr[i]]
  steps.push({ values: [...arr], active: [i, j], ...extra })
}

/** 升序冒泡排序：相邻比较，大者后移 */
export function bubbleSortSteps(initial: number[]): SortAnimStep[] {
  const arr = [...initial]
  const steps: SortAnimStep[] = []
  const n = arr.length
  // sortedFrom: 已排序后缀起始下标，初始 n 表示无已就位元素
  let sortedFrom = n

  for (let end = n - 1; end > 0; end--) {
    let swapped = false
    const doneMark = sortedFrom < n ? { sortedFrom } : {}
    for (let j = 0; j < end; j++) {
      pushCompare(steps, arr, j, j + 1, doneMark)
      if (arr[j] > arr[j + 1]) {
        pushSwap(steps, arr, j, j + 1, doneMark)
        swapped = true
      }
    }
    sortedFrom = end
    if (!swapped) {
      steps.push({
        values: [...arr],
        active: [],
        sortedFrom: 0,
        hint: '本轮无交换，已有序，提前结束',
      })
      break
    }
  }

  steps.push({ values: [...arr], active: [], sortedFrom: 0, hint: '排序完成' })
  return steps
}

/** 升序选择排序：每轮将最小元放到未排序段前端 */
export function selectionSortSteps(initial: number[]): SortAnimStep[] {
  const arr = [...initial]
  const steps: SortAnimStep[] = []
  const n = arr.length

  for (let i = 0; i < n - 1; i++) {
    let minIdx = i
    // sortedUntil: 上一轮结束时前缀 [0, i-1] 已就位
    const doneMark = i - 1 >= 0 ? { sortedUntil: i - 1 } : {}
    for (let j = i + 1; j < n; j++) {
      pushCompare(steps, arr, minIdx, j, doneMark)
      if (arr[j] < arr[minIdx]) minIdx = j
    }
    if (minIdx !== i) pushSwap(steps, arr, i, minIdx, doneMark)
    // 标记本轮最小元归位
    steps.push({
      values: [...arr],
      active: [i],
      sortedUntil: i,
      hint: `最小元 a[${i}] 已就位`,
    })
  }

  steps.push({ values: [...arr], active: [], sortedUntil: n - 1, hint: '排序完成' })
  return steps
}

/** 升序快速排序（Lomuto 分区，末元为枢轴） */
export function quickSortSteps(initial: number[]): SortAnimStep[] {
  const arr = [...initial]
  const steps: SortAnimStep[] = []

  function partition(lo: number, hi: number): number {
    const pivotIdx = hi
    const pivotVal = arr[pivotIdx]
    steps.push({
      values: [...arr],
      active: [pivotIdx],
      pivot: pivotIdx,
      hint: `选 a[${pivotIdx}]=${pivotVal} 为枢轴`,
    })

    let i = lo
    for (let j = lo; j < hi; j++) {
      // 比较步骤：保留 pivot 标记，让学生看到哪个是枢轴
      steps.push({
        values: [...arr],
        active: [j],
        pivot: pivotIdx,
        hint: `比较 a[${j}]=${arr[j]} 与 pivot=${pivotVal}`,
      })
      if (arr[j] < pivotVal) {
        const smallVal = arr[j]
        if (i !== j) {
          ;[arr[i], arr[j]] = [arr[j], arr[i]]
          steps.push({
            values: [...arr],
            active: [i, j],
            pivot: pivotIdx,
            hint: `${smallVal} < pivot，交换 a[${i}] ↔ a[${j}]`,
          })
        } else {
          steps.push({
            values: [...arr],
            active: [i],
            pivot: pivotIdx,
            hint: `${smallVal} < pivot，已在左区无需交换`,
          })
        }
        i++
      }
    }
    // 枢轴归位
    if (i !== pivotIdx) {
      ;[arr[i], arr[pivotIdx]] = [arr[pivotIdx], arr[i]]
      steps.push({
        values: [...arr],
        active: [i],
        pivot: i,
        hint: `枢轴归位到 a[${i}]，左侧均 < pivot，右侧均 ≥ pivot`,
      })
    } else {
      steps.push({
        values: [...arr],
        active: [i],
        pivot: i,
        hint: `枢轴已在最终位置 a[${i}]`,
      })
    }
    return i
  }

  function quick(lo: number, hi: number) {
    if (lo >= hi) return
    const p = partition(lo, hi)
    quick(lo, p - 1)
    quick(p + 1, hi)
  }

  if (arr.length > 0) quick(0, arr.length - 1)
  steps.push({ values: [...arr], active: [], hint: '排序完成' })
  return steps
}

/** 升序插入排序：维护有序前缀，逐个将待插入元素前移 */
export function insertionSortSteps(initial: number[]): SortAnimStep[] {
  const arr = [...initial]
  const steps: SortAnimStep[] = []
  const n = arr.length

  for (let i = 1; i < n; i++) {
    const key = arr[i]
    // sortedUntil: 前缀 [0, i-1] 已有序
    const done = i - 1
    steps.push({
      values: [...arr],
      active: [i],
      sortedUntil: done,
      hint: `待插入 a[${i}] = ${key}，前缀 [0, ${done}] 已有序`,
    })
    let j = i - 1
    while (j >= 0 && arr[j] > key) {
      const movingVal = arr[j]
      steps.push({
        values: [...arr],
        active: [j, j + 1],
        sortedUntil: done,
        hint: `a[${j}]=${movingVal} > key=${key}，将 a[${j}] 右移到 a[${j + 1}]`,
      })
      arr[j + 1] = arr[j]
      steps.push({
        values: [...arr],
        active: [j + 1],
        sortedUntil: done,
        hint: `a[${j + 1}] ← ${movingVal}；原位置 a[${j}] 为副本，待 key 放入后覆盖`,
      })
      j--
    }
    arr[j + 1] = key
    steps.push({
      values: [...arr],
      active: [j + 1],
      sortedUntil: i,
      hint: `key=${key} 放入 a[${j + 1}]，前缀 [0, ${i}] 已有序`,
    })
  }

  steps.push({ values: [...arr], active: [], sortedUntil: n - 1, hint: '排序完成' })
  return steps
}

/** 升序归并排序：递归分半后双指针合并，同时统计逆序对 */
export function mergeSortSteps(initial: number[]): SortAnimStep[] {
  const arr = [...initial]
  const steps: SortAnimStep[] = []
  const n = arr.length

  function merge(lo: number, mid: number, hi: number) {
    steps.push({
      values: [...arr],
      active: [],
      range: [lo, hi],
      hint: `合并 [${lo}, ${hi}]，切点 ${mid}`,
    })
    const left = arr.slice(lo, mid + 1)
    const right = arr.slice(mid + 1, hi + 1)
    let i = 0
    let j = 0
    let k = lo
    while (i < left.length && j < right.length) {
      // 注意：left[i] 对应原下标 lo+i，但当 j>0 时该位置可能已被覆盖，
      // 因此比较步骤只高亮写入位置 k，靠 hint 文字说明比较的两个值
      steps.push({
        values: [...arr],
        active: [k],
        range: [lo, hi],
        hint: `比较 left[${i}]=${left[i]} 与 right[${j}]=${right[j]}`,
      })
      if (left[i] <= right[j]) {
        arr[k] = left[i]
        i++
      } else {
        arr[k] = right[j]
        j++
      }
      steps.push({
        values: [...arr],
        active: [k],
        range: [lo, hi],
        hint: `写入 a[${k}] = ${arr[k]}`,
      })
      k++
    }
    while (i < left.length) {
      arr[k] = left[i]
      steps.push({
        values: [...arr],
        active: [k],
        range: [lo, hi],
        hint: `左半剩余 ${left[i]} 拷贝到 a[${k}]`,
      })
      i++
      k++
    }
    while (j < right.length) {
      arr[k] = right[j]
      steps.push({
        values: [...arr],
        active: [k],
        range: [lo, hi],
        hint: `右半剩余 ${right[j]} 拷贝到 a[${k}]`,
      })
      j++
      k++
    }
  }

  function mergeSort(lo: number, hi: number) {
    if (lo >= hi) return
    const mid = Math.floor((lo + hi) / 2)
    mergeSort(lo, mid)
    mergeSort(mid + 1, hi)
    merge(lo, mid, hi)
  }

  if (n > 0) mergeSort(0, n - 1)
  steps.push({ values: [...arr], active: [], hint: '排序完成' })
  return steps
}

/** 升序堆排序：自底向上建最大堆，逐轮交换堆顶到末尾并下沉 */
export function heapSortSteps(initial: number[]): SortAnimStep[] {
  const arr = [...initial]
  const steps: SortAnimStep[] = []
  const n = arr.length
  let heapSize = n

  function siftDown(start: number, size: number, sortedFrom?: number) {
    let parent = start
    while (true) {
      const left = 2 * parent + 1
      const right = 2 * parent + 2
      let largest = parent
      if (left < size && arr[left] > arr[largest]) largest = left
      if (right < size && arr[right] > arr[largest]) largest = right

      // 构造比较说明，明确指出有哪些孩子参与比较
      const children: string[] = []
      if (left < size) children.push(`左 a[${left}]=${arr[left]}`)
      if (right < size) children.push(`右 a[${right}]=${arr[right]}`)
      const childDesc = children.length > 0 ? children.join('，') : '无孩子（叶子）'

      // 去重 active：当 largest === parent 时只保留一个
      const activeIdxs = largest === parent ? [parent] : [parent, largest]
      steps.push({
        values: [...arr],
        active: activeIdxs,
        heapSize: size,
        sortedFrom,
        hint: `a[${parent}]=${arr[parent]}，${childDesc}，最大在 a[${largest}]`,
      })
      if (largest === parent) break
      ;[arr[parent], arr[largest]] = [arr[largest], arr[parent]]
      steps.push({
        values: [...arr],
        active: [parent, largest],
        heapSize: size,
        sortedFrom,
        hint: `下沉：交换 a[${parent}] ↔ a[${largest}]`,
      })
      parent = largest
    }
  }

  // 自底向上建堆
  for (let i = Math.floor(n / 2) - 1; i >= 0; i--) {
    steps.push({
      values: [...arr],
      active: [i],
      heapSize,
      hint: `从下标 ${i} 开始下沉建堆`,
    })
    siftDown(i, heapSize)
  }
  steps.push({
    values: [...arr],
    active: [],
    heapSize,
    hint: '最大堆建好，堆顶为最大值',
  })

  // 逐轮提取最大值
  for (let end = n - 1; end > 0; end--) {
    ;[arr[0], arr[end]] = [arr[end], arr[0]]
    heapSize--
    steps.push({
      values: [...arr],
      active: [0, end],
      heapSize,
      sortedFrom: end,
      hint: `堆顶交换到 a[${end}]，堆缩小到 ${heapSize}`,
    })
    siftDown(0, heapSize, end)
  }

  steps.push({ values: [...arr], active: [], heapSize: 0, sortedFrom: 0, hint: '排序完成' })
  return steps
}
