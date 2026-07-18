"""QA 综合测试脚本：通过 HTTP API 验证各功能模块稳定性与输出质量。"""
import json
import sys
import time
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"

# 测试用户（若已存在则直接登录）
TEST_USER = {
    "username": "qa_tester",
    "password": "Qa@Test1234",
    "email": "qa_tester@example.com",
}


def _req(method: str, path: str, *, token: str = "", body=None, timeout: float = 60):
    url = f"{BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except Exception as e:
        return -1, f"{type(e).__name__}: {e}"


def _sse_req(method: str, path: str, *, token: str = "", body=None, timeout: float = 120):
    """SSE 流式请求，返回所有事件列表。"""
    url = f"{BASE}{path}"
    headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    events = []
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            buf = ""
            while True:
                chunk = r.read(1024)
                if not chunk:
                    break
                buf += chunk.decode("utf-8", errors="replace")
                while "\n\n" in buf:
                    block, buf = buf.split("\n\n", 1)
                    for line in block.split("\n"):
                        if line.startswith("data: "):
                            try:
                                events.append(json.loads(line[6:]))
                            except json.JSONDecodeError:
                                events.append({"_raw": line[6:]})
    except urllib.error.HTTPError as e:
        events.append({"_error": f"HTTP {e.code}", "_body": e.read().decode("utf-8", errors="replace")[:300]})
    except Exception as e:
        events.append({"_error": f"{type(e).__name__}: {e}"})
    return events


def step(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def ok(msg: str):
    print(f"  [OK] {msg}")


def fail(msg: str):
    print(f"  [FAIL] {msg}")


def info(msg: str):
    print(f"  [INFO] {msg}")


def show(label: str, text: str, limit: int = 300):
    snippet = text[:limit].replace("\n", " ")
    print(f"  {label}: {snippet}{'...' if len(text) > limit else ''}")


# ============ 测试步骤 ============

def test_auth():
    """1. 认证：注册或登录获取 token。"""
    step("[模块1] 认证：注册/登录")
    # 尝试注册
    s, b = _req("POST", "/api/auth/register", body=TEST_USER)
    token = None
    if s == 200 or s == 201:
        data = json.loads(b)
        token = data.get("access_token") or data.get("token")
        ok(f"注册成功，token 长度={len(token) if token else 0}")
    elif s == 400 or s == 409:
        info("用户已存在，尝试登录")
        s2, b2 = _req("POST", "/api/auth/login", body={"username": TEST_USER["username"], "password": TEST_USER["password"]})
        if s2 == 200:
            data = json.loads(b2)
            token = data.get("access_token") or data.get("token")
            ok(f"登录成功，token 长度={len(token) if token else 0}")
        else:
            fail(f"登录失败 {s2}: {b2[:200]}")
    else:
        fail(f"注册失败 {s}: {b[:200]}")
    if not token:
        return None
    # 验证 token
    s, b = _req("GET", "/api/auth/me", token=token)
    if s == 200:
        ok(f"token 有效，用户信息: {b[:200]}")
    else:
        fail(f"token 无效 {s}: {b[:200]}")
    return token


def test_resource_generation(token: str):
    """2. 资源生成：单资源流式生成（document 类型）。"""
    step("[模块2] 资源生成：document 类型（流式）")
    body = {
        "resource_type": "document",
        "topic": "链表基础",
        "module_key": "linked-list",
        "focus_hint": "重点讲解指针操作与边界",
    }
    info(f"请求: POST /api/orchestrator/resources/generate body={body}")
    events = _sse_req("POST", "/api/orchestrator/resources/generate", token=token, body=body, timeout=180)
    info(f"收到事件数: {len(events)}")
    # 统计事件类型
    types = {}
    final_resource = None
    deltas_count = 0
    total_delta_text = ""
    for ev in events:
        t = ev.get("type", "_unknown")
        types[t] = types.get(t, 0) + 1
        if t == "resource":
            final_resource = ev
        elif t == "content_delta":
            deltas_count += 1
            total_delta_text += ev.get("delta", "")
        elif t == "error":
            fail(f"收到 error 事件: {ev}")
    info(f"事件类型分布: {types}")
    if deltas_count > 0:
        ok(f"流式 delta 正常，共 {deltas_count} 个 chunk，拼接长度 {len(total_delta_text)}")
        show("流式内容预览", total_delta_text, 200)
    if final_resource:
        r = final_resource.get("resource", final_resource)
        title = r.get("title", "")
        content = r.get("content", "")
        ok(f"资源已生成: title={title[:50]}, content 长度={len(content)}")
        show("资源内容预览", content, 300)
        # 质量检查
        if len(content) < 100:
            fail(f"资源内容过短（{len(content)} < 100）")
        else:
            ok(f"资源内容长度达标（{len(content)} >= 100）")
        if "链表" in content or "指针" in content:
            ok("资源内容与主题相关（含'链表'或'指针'）")
        else:
            fail("资源内容可能与主题无关（未含'链表'或'指针'）")
    else:
        fail("未收到最终 resource 事件")


def test_oj_problems(token: str):
    """3. OJ 题目列表与详情。"""
    step("[模块3] OJ 题目列表与详情")
    s, b = _req("GET", "/api/oj/problems", token=token)
    if s != 200:
        fail(f"题目列表失败 {s}: {b[:200]}")
        return None
    data = json.loads(b)
    problems = data if isinstance(data, list) else data.get("problems", data.get("items", []))
    ok(f"题目列表获取成功，共 {len(problems)} 题")
    if not problems:
        fail("题目列表为空")
        return None
    first = problems[0] if isinstance(problems[0], dict) else {"slug": problems[0]}
    slug = first.get("slug", first.get("id", ""))
    info(f"第一题: {first.get('title', slug)} (slug={slug})")
    # 题目详情
    s2, b2 = _req("GET", f"/api/oj/problems/{slug}", token=token)
    if s2 == 200:
        ok(f"题目详情获取成功")
        show("详情预览", b2, 200)
    else:
        fail(f"题目详情失败 {s2}: {b2[:200]}")
    return slug


def test_oj_judge(token: str, slug: str):
    """4. OJ 判题：提交一段示例代码。"""
    step("[模块4] OJ 判题")
    if not slug:
        info("跳过：无 slug")
        return
    # 先获取题目详情找到示例代码
    s, b = _req("GET", f"/api/oj/problems/{slug}", token=token)
    if s != 200:
        fail(f"获取题目详情失败 {s}")
        return
    problem = json.loads(b)
    judge_mode = problem.get("judge_mode", "stdio")
    lang = problem.get("languages", ["python"])[0] if problem.get("languages") else "python"
    info(f"题目 judge_mode={judge_mode}, lang={lang}")
    # 构造一段简单代码
    if judge_mode == "function":
        code = "class Solution:\n    def solve(self, *args):\n        return args[0] if args else None"
    else:
        code = "import sys\nfor line in sys.stdin:\n    print(line.strip())"
    body = {"code": code, "language": lang}
    s2, b2 = _req("POST", f"/api/oj/problems/{slug}/submit", token=token, body=body, timeout=60)
    info(f"提交响应: {s2}")
    show("判题结果", b2, 400)
    if s2 == 200:
        ok("判题端点正常响应")
    else:
        fail(f"判题失败 {s2}")


def test_oj_trace(token: str, slug: str):
    """5. OJ trace 执行。"""
    step("[模块5] OJ trace 执行")
    if not slug:
        info("跳过：无 slug")
        return
    code = "import sys\nfor line in sys.stdin:\n    print(line.strip())"
    body = {"code": code, "language": "python", "stdin": "hello\nworld\n"}
    s, b = _req("POST", f"/api/oj/problems/{slug}/trace", token=token, body=body, timeout=60)
    info(f"trace 响应: {s}")
    show("trace 结果", b, 400)
    if s == 200:
        data = json.loads(b)
        steps = data.get("steps", [])
        ok(f"trace 正常，共 {len(steps)} 步")
    else:
        fail(f"trace 失败 {s}: {b[:200]}")


def test_ai_tutor(token: str):
    """6. AI 导师聊天（非流式）。"""
    step("[模块6] AI 导师聊天（非流式）")
    body = {
        "message": "请用一句话解释什么是时间复杂度",
        "history": [],
        "module_key": "array",
    }
    s, b = _req("POST", "/api/orchestrator/tutor/chat", token=token, body=body, timeout=90)
    info(f"响应: {s}")
    if s == 200:
        data = json.loads(b)
        reply = data.get("reply", data.get("content", ""))
        ok(f"AI 导师回复成功，长度={len(reply)}")
        show("回复内容", reply, 300)
        if "复杂度" in reply or "时间" in reply:
            ok("回复与问题相关")
        else:
            fail("回复可能与问题无关")
    else:
        fail(f"AI 导师失败 {s}: {b[:200]}")


def test_learning_path(token: str):
    """7. 学习路径。"""
    step("[模块7] 学习路径")
    s, b = _req("GET", "/api/orchestrator/learning-path", token=token)
    info(f"响应: {s}")
    if s == 200:
        ok("学习路径获取成功")
        show("路径预览", b, 300)
    else:
        info(f"学习路径未生成（{s}），尝试 replan")
        body = {
            "overall_percent": 10,
            "modules": [
                {"module_key": "array", "progress": 30},
                {"module_key": "linked-list", "progress": 0},
            ],
        }
        s2, b2 = _req("POST", "/api/orchestrator/learning-path/replan", token=token, body=body, timeout=90)
        if s2 == 200:
            ok("replan 成功")
            show("replan 结果", b2, 300)
        else:
            fail(f"replan 失败 {s2}: {b2[:200]}")


def main():
    print("=" * 70)
    print("  AlgoPilot 全模块稳定性与输出质量验证")
    print("=" * 70)
    token = test_auth()
    if not token:
        fail("认证失败，无法继续后续测试")
        return 1
    test_resource_generation(token)
    slug = test_oj_problems(token)
    test_oj_judge(token, slug)
    test_oj_trace(token, slug)
    test_ai_tutor(token)
    test_learning_path(token)
    step("验证完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
