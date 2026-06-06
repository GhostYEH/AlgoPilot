import re

def _strip_kb_annotations(raw):
    cleaned = re.sub(r'---\*\*依据知识库\*\*[\s\S]*', '', raw)
    cleaned = re.sub(r'\n\*\*依据知识库\*\*[\s\S]*', '', cleaned)
    cleaned = re.sub(r'---{2,}\s*依据知识库[\s\S]*', '', cleaned)
    cleaned = re.sub(r'\n---+\s*\n\*\*依据知识库\*\*[\s\S]*', '', cleaned)
    cleaned = re.sub(r'\n---{3,}[\s\S]*', '', cleaned)
    cleaned = re.sub(r'\ncourse:[\w\-:]+\n', '\n', cleaned)
    cleaned = re.sub(r'\n内容校验[\s\S]*', '', cleaned)
    cleaned = re.sub(r'\n安全审查[\s\S]*', '', cleaned)
    return cleaned.strip()

def _sanitize_mermaid(text):
    text = _strip_kb_annotations(text)
    lines = text.splitlines()
    if not lines:
        return text
    header = lines[0].strip()
    is_flowchart = header.startswith('flowchart') or header.startswith('graph')
    is_mindmap = header.startswith('mindmap')
    cleaned = [lines[0]]
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('---') or stripped.startswith('==='):
            continue
        if stripped.startswith('%%'):
            if is_mindmap:
                continue
            cleaned.append(line)
            continue
        if re.match(r'^\*\*', stripped):
            continue
        if 'course:' in stripped:
            continue
        if '依据知识库' in stripped:
            continue
        if re.search(r'内容校验|安全审查|校验详情|条知识库依据', stripped):
            continue
        s = re.sub(r'\*\*([^*]+)\*\*', r'\1', stripped)
        s = re.sub(r'\*([^*]+)\*', r'\1', s)
        s = re.sub(r'---+\s*依据知识库.*', '', s)
        s = re.sub(r'---+\s*\*\*依据知识库.*', '', s)
        if is_flowchart:
            s = s.replace('---', '-->')
        if not s.strip():
            continue
        if not re.match(r'^[\w\u4e00-\u9fff()（）、，\[\]{}:：\s]', s) and not s.startswith('}') and not s.startswith(']'):
            continue
        if is_mindmap:
            indent = len(line) - len(line.lstrip())
            cleaned.append(' ' * indent + s)
        else:
            cleaned.append(s)
    result = '\n'.join(cleaned)
    if is_flowchart and not any('-->' in ln for ln in cleaned[1:]):
        return text
    return result

def _clean_mindmap_label(text):
    s = text.strip()
    s = re.sub(r'^\d+[\.\)\u3001]\s*', '', s)
    s = re.sub(r'^ch\d+[-]?\s*', '', s)
    parts = re.split(r'[:：]', s, maxsplit=1)
    if len(parts) == 2:
        after = parts[1].strip()
        before = parts[0].strip()
        has_chinese_after = bool(re.search(r'[\u4e00-\u9fff]', after))
        if has_chinese_after and len(after) <= 12:
            s = after
        else:
            s = before
    s = re.sub(r'^[a-z]+[-]?', '', s)
    s = re.sub(r'[。，、；！？\.\!\?\;\,\u300a\u300b\uff08\uff09()（）\s]+$', '', s)
    s = s.strip()
    if len(s) > 10:
        s = s[:10]
    return s

def _fix_mindmap_syntax(text, fallback_topic='学习主题'):
    lines = text.splitlines()
    if not lines or not lines[0].strip().startswith('mindmap'):
        return 'mindmap\n  root(({0}))\n    核心概念\n    关键算法\n    应用场景'.format(fallback_topic)
    has_root = False
    fixed_lines = ['mindmap']
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('root'):
            label = re.sub(r'^root\s*[\(\[\{]+', '', stripped)
            label = re.sub(r'[\)\]\}]+$', '', label)
            label = label.strip()
            if not label:
                label = fallback_topic
            fixed_lines.append('  root(({0}))'.format(label))
            has_root = True
            continue
        indent = len(line) - len(line.lstrip())
        cleaned = _clean_mindmap_label(stripped)
        if not cleaned:
            continue
        fixed_lines.append(' ' * indent + cleaned)
    if not has_root:
        fixed_lines.insert(1, '  root(({0}))'.format(fallback_topic))
    if len(fixed_lines) < 3:
        return 'mindmap\n  root(({0}))\n    核心概念\n    关键算法\n    应用场景'.format(fallback_topic)
    return '\n'.join(fixed_lines)

# User's ACTUAL broken output
raw = """mindmap
  root((主题))
    课程定位: 高校计算机类专业核心课，讲授抽象数据类型、经典算法范式、复杂度分析与课内编程实践。
    实践环节: 实验、项目
    与平台模块映射: course_manifest.yaml的module_keys字段关联平台学习模块（如array、dp、graph）
    章节一览:
     1. ch01-introduction-complexity: 绪论与复杂度
     2. ch02-linear-list: 线性表
     3. ch03-stack-queue: 栈与队列
     4. ch04-string: 字符串与双指针
     5. ch05-tree-binary-tree: 树与二叉树
     6. ch06-graph: 图与BFS/DFS
     7. ch07-search: 查找
     8. ch08-sorting: 排序
     9. ch09-recursion-divide-conquer: 递归与分治
     10. ch10-greedy: 贪心
     11. ch11-dynamic-programming: 动态规划
     12. ch12-backtracking: 回溯
     13. ch13-heap-union-find: 堆与并查集
     14. ch14-comprehensive-project: 综合项目

---
**依据知识库**：course:data_structures_algorithms:syllabus:课程定位"""

print("=== User's actual broken output ===")
result = _fix_mindmap_syntax(_sanitize_mermaid(raw), '数据结构与算法')
print(result)
print()

# Verify
for line in result.splitlines()[1:]:
    s = line.strip()
    if not s:
        continue
    assert ':' not in s, 'Colon found in: ' + s
    assert '：' not in s, 'Chinese colon found in: ' + s
    assert '依据知识库' not in s, 'KB annotation found in: ' + s
    assert '---' not in s, 'Separator found in: ' + s
    if not s.startswith('root'):
        assert len(s) <= 10, 'Label too long: ' + s + ' (len=' + str(len(s)) + ')'

# Check Chinese labels are preserved
assert '绪论与复杂度' in result, 'Missing Chinese label'
assert '线性表' in result, 'Missing 线性表'
assert '栈与队列' in result, 'Missing 栈与队列'
assert '树与二叉树' in result, 'Missing 树与二叉树'
assert '课程定位' in result, 'Missing 课程定位'

print('ALL CHECKS PASSED')
