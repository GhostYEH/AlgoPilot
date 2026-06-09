export interface OjJudgeDemoScenario {
  slug: string
  title: string
  language: 'python'
  code: string
}

const REVERSE_LINKED_LIST_WRONG_ORDER = `import sys


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def main():
    data = list(map(int, sys.stdin.read().split()))
    n = data[0]
    values = data[1:1 + n]

    dummy = ListNode()
    tail = dummy
    for value in values:
        tail.next = ListNode(value)
        tail = tail.next

    prev = None
    curr = dummy.next
    while curr:
        curr.next = prev
        nxt = curr.next
        prev = curr
        curr = nxt

    answer = []
    curr = prev
    while curr:
        answer.append(curr.val)
        curr = curr.next
    print(*answer)


if __name__ == '__main__':
    main()
`

const SCENARIOS: Record<string, OjJudgeDemoScenario> = {
  'reverse-linked-list': {
    slug: 'reverse-linked-list',
    title: '反转链表 · 后继指针保存顺序错误',
    language: 'python',
    code: REVERSE_LINKED_LIST_WRONG_ORDER,
  },
}

export function getOjJudgeDemoScenario(slug: string): OjJudgeDemoScenario | null {
  return SCENARIOS[slug] ?? null
}
