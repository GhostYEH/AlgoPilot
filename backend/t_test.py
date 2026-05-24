

    class Solution:
def twoSum(self, nums, target):
    d = {}
    for i, x in enumerate(nums):
        if target - x in d:
            return [d[target-x], i]
        d[x] = i


    import json
    import time

    _args = json.loads("[[2, 7, 11, 15], 9]")
    pass
    inst = Solution()
    t0 = time.perf_counter()
    result = inst.twoSum(*_args)
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    print(json.dumps({"ok": True, "result": result, "ms": elapsed_ms}, default=str))
