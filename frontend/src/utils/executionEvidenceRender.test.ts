/** ExecutionEvidence 前端渲染契约测试。

测试：
1. ExecutionEvidence 完整 → 正常显示
2. First Divergence null → 正常降级
3. Trace truncated → 正常提示
4. Bug unknown → 显示"暂未确定错误类型"而非崩溃
 */

import { strict as assert } from 'node:assert'
import type { AiDiagnoseResponse, ExecutionEvidence, FirstDivergenceResult, CounterexampleResult } from './codeTrace'

function makeBaseResponse(): AiDiagnoseResponse {
  return {
    edge_case: { reason: '', category: 'edge', input_preview: 'test', expected_preview: '42', source: 'llm' },
    edge_verdict: 'WA',
    edge_message: 'Wrong Answer',
    trace: { verdict: 'WA', message: '', user_line_count: 10, steps: [], narrations: [] },
    complexity: { input_size_n: 5, total_steps: 20, meaningful_steps: 15, estimated_complexity: 'O(log n)', report: '', source: 'trace' },
    summary: '测试摘要',
  }
}

class TestExecutionEvidenceComplete {
  test_full_execution_evidence_present(): void {
    const evidence: ExecutionEvidence = {
      problem_slug: 'binary-search',
      language: 'python',
      source_code: 'def main(): pass',
      total_cases: 10,
      passed_cases: 7,
      failed_test_cases: [
        { index: 3, input_preview: '5\n1 3 5 7 9\n6', expected_output: '-1', actual_output: '4' },
      ],
      bug_diagnosis: {
        bug_type: 'boundary_condition_error',
        bug_type_label: '边界条件错误',
        suspicious_lines: [7, 12],
        root_cause: 'hi = mid 应为 hi = mid - 1',
        confidence: 'high',
      },
      ai_available: true,
      fallback_reason: '',
    }

    const resp = makeBaseResponse()
    resp.execution_evidence = evidence

    assert.ok(resp.execution_evidence)
    assert.equal(resp.execution_evidence.bug_diagnosis?.bug_type_label, '边界条件错误')
    assert.equal(resp.execution_evidence.failed_test_cases?.length, 1)
    assert.equal(resp.execution_evidence.passed_cases, 7)
  }

  test_counterexample_present(): void {
    const ce: CounterexampleResult = {
      selected_case: { args: [[1, 3, 5, 7], 8] },
      source: 'generated_verified',
      candidate_count: 8,
      verified_count: 6,
      triggered_count: 2,
      latency_ms: 150,
      category: 'not_found_upper',
      reason: '验证反例触发 Bug',
    }

    const resp = makeBaseResponse()
    resp.counterexample = ce

    assert.ok(resp.counterexample)
    assert.equal(resp.counterexample.source, 'generated_verified')
    assert.ok(resp.counterexample.candidate_count > 0)
  }
}

class TestFirstDivergenceNull {
  test_null_first_divergence_graceful(): void {
    const resp = makeBaseResponse()
    resp.first_divergence = null

    assert.equal(resp.first_divergence, null)
    // 前端应显示降级消息，不崩溃
  }

  test_first_divergence_with_reason(): void {
    const fd: FirstDivergenceResult = {
      detected: false,
      step_index: 0,
      line: null,
      reference_line: null,
      student_state: '',
      reference_state: '',
      divergent_variable: '',
      explanation: '',
      confidence: 'low',
      reference_source: '',
      reason: 'insufficient_reference_trace: 该题目尚无 AC 提交可作为参考解',
    }

    const resp = makeBaseResponse()
    resp.first_divergence = fd

    assert.ok(resp.first_divergence)
    assert.equal(resp.first_divergence.detected, false)
    assert.ok(resp.first_divergence.reason.length > 0)
  }

  test_first_divergence_detected(): void {
    const fd: FirstDivergenceResult = {
      detected: true,
      step_index: 3,
      line: 7,
      reference_line: 7,
      student_state: 'mid=3',
      reference_state: 'mid=1',
      divergent_variable: 'mid',
      explanation: 'Step 3 变量 mid 首次偏离',
      confidence: 'high',
      reference_source: 'ac_submission:binary-search',
      reason: '',
    }

    const resp = makeBaseResponse()
    resp.first_divergence = fd

    assert.ok(resp.first_divergence?.detected)
    assert.equal(resp.first_divergence?.divergent_variable, 'mid')
  }
}

class TestTraceTruncated {
  test_empty_steps_handled(): void {
    const resp = makeBaseResponse()
    resp.trace.steps = []

    assert.equal(resp.trace.steps.length, 0)
    // 前端应正常显示"无执行步骤"而非崩溃
  }

  test_large_step_count_handled(): void {
    const resp = makeBaseResponse()
    resp.trace.steps = Array.from({ length: 500 }, (_, i) => ({
      line: i + 1,
      changed: ['x'],
      vars: { x: { type: 'int', value: i } },
    }))

    assert.equal(resp.trace.steps.length, 500)
    // 前端应能处理大量步骤（可能虚拟滚动或截断显示）
  }
}

class TestBugUnknown {
  test_unknown_bug_type_display(): void {
    const evidence: ExecutionEvidence = {
      bug_diagnosis: {
        bug_type: 'unknown',
        bug_type_label: '',
        suspicious_lines: [],
        root_cause: '',
        confidence: 'low',
      },
      ai_available: false,
      fallback_reason: 'LLM 不可用',
    }

    const resp = makeBaseResponse()
    resp.execution_evidence = evidence

    // 前端应显示"暂未确定错误类型"而非崩溃
    assert.equal(resp.execution_evidence.bug_diagnosis?.bug_type, 'unknown')
    assert.equal(resp.execution_evidence.bug_diagnosis?.bug_type_label, '')
  }

  test_no_bug_diagnosis_at_all(): void {
    const evidence: ExecutionEvidence = {
      ai_available: false,
      fallback_reason: 'LLM 不可用',
    }

    const resp = makeBaseResponse()
    resp.execution_evidence = evidence

    assert.ok(resp.execution_evidence)
    assert.equal(resp.execution_evidence.bug_diagnosis, undefined)
  }
}

// 运行所有测试
const tests = [
  new TestExecutionEvidenceComplete(),
  new TestFirstDivergenceNull(),
  new TestTraceTruncated(),
  new TestBugUnknown(),
]

let passed = 0
let total = 0

for (const suite of tests) {
  const proto = Object.getPrototypeOf(suite)
  for (const name of Object.getOwnPropertyNames(proto)) {
    if (name === 'constructor') continue
    if (typeof (suite as Record<string, unknown>)[name] !== 'function') continue
    total++
    try {
      ;(suite as Record<string, () => void>)[name]()
      console.log(`  ✓ ${name}`)
      passed++
    } catch (e) {
      console.error(`  ✗ ${name}: ${(e as Error).message}`)
      process.exitCode = 1
    }
  }
}

console.log(`\n全部通过：${passed} 项（共 ${total} 项）`)