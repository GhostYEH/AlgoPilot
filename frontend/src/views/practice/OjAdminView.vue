<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete, RefreshRight, Search } from '@element-plus/icons-vue'
import {
  fetchProblems,
  fetchAdminCases,
  updateAdminCases,
  fetchAdminChapters,
  createProblem,
  attachProblemToChapter,
  type ProblemListItem,
  type AdminProblemCases,
  type AdminTestCase,
  type AdminChapter,
  type CreateProblemPayload,
} from '@/api/oj'
import { ALGORITHM_MODULES } from '@/constants/modules'

// ──────────────────────────── 题目列表 ────────────────────────────
const allProblems = ref<ProblemListItem[]>([])
const listLoading = ref(false)
const searchQuery = ref('')
const moduleFilter = ref('')

const filteredProblems = computed(() => {
  let items = allProblems.value
  if (moduleFilter.value) {
    items = items.filter((p) => p.module_key === moduleFilter.value)
  }
  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    items = items.filter(
      (p) => p.slug.toLowerCase().includes(q) || p.title.toLowerCase().includes(q),
    )
  }
  return items
})

const readyCount = computed(() => allProblems.value.filter((problem) => problem.ready).length)
const moduleCount = computed(() => new Set(allProblems.value.map((problem) => problem.module_key)).size)
const moduleLabelMap = new Map(ALGORITHM_MODULES.map((module) => [module.key, module.label]))

function moduleLabel(moduleKey: string): string {
  return moduleLabelMap.get(moduleKey) ?? moduleKey
}

function difficultyMeta(difficulty: string): {
  label: string
  type: 'success' | 'warning' | 'danger' | 'info'
} {
  if (difficulty === 'easy') return { label: '简单', type: 'success' }
  if (difficulty === 'hard') return { label: '困难', type: 'danger' }
  if (difficulty === 'medium') return { label: '中等', type: 'warning' }
  return { label: difficulty || '未知', type: 'info' }
}

function clearFilters() {
  searchQuery.value = ''
  moduleFilter.value = ''
}

async function loadProblems() {
  listLoading.value = true
  try {
    allProblems.value = await fetchProblems()
  } catch {
    ElMessage.error('题目列表加载失败')
  } finally {
    listLoading.value = false
  }
}

// ──────────────────────────── 测试用例编辑 ────────────────────────────
const casesDialogVisible = ref(false)
const casesLoading = ref(false)
const casesSaving = ref(false)
const currentCases = ref<AdminProblemCases | null>(null)
const editableSamples = ref<AdminTestCase[]>([])
const editableHidden = ref<AdminTestCase[]>([])

function openCasesDialog(slug: string) {
  casesDialogVisible.value = true
  casesLoading.value = true
  currentCases.value = null
  fetchAdminCases(slug)
    .then((data) => {
      currentCases.value = data
      editableSamples.value = JSON.parse(JSON.stringify(data.samples))
      editableHidden.value = JSON.parse(JSON.stringify(data.hidden))
    })
    .catch(() => {
      ElMessage.error('加载测试用例失败')
      casesDialogVisible.value = false
    })
    .finally(() => {
      casesLoading.value = false
    })
}

function addSample() {
  editableSamples.value.push({ stdin: '', stdout: '' })
}

function removeSample(idx: number) {
  editableSamples.value.splice(idx, 1)
}

function addHidden() {
  editableHidden.value.push({ stdin: '', stdout: '' })
}

function removeHidden(idx: number) {
  editableHidden.value.splice(idx, 1)
}

async function saveCases() {
  if (!currentCases.value) return
  casesSaving.value = true
  try {
    const data = await updateAdminCases(
      currentCases.value.slug,
      editableSamples.value,
      editableHidden.value,
    )
    currentCases.value = data
    editableSamples.value = JSON.parse(JSON.stringify(data.samples))
    editableHidden.value = JSON.parse(JSON.stringify(data.hidden))
    ElMessage.success('测试用例已保存')
  } catch {
    ElMessage.error('保存失败，请重试')
  } finally {
    casesSaving.value = false
  }
}

// ──────────────────────────── 新增题目 ────────────────────────────
const createDialogVisible = ref(false)
const createLoading = ref(false)
const chapters = ref<AdminChapter[]>([])

const createForm = reactive<CreateProblemPayload>({
  slug: '',
  title: '',
  module_key: '',
  difficulty: 'medium',
  lc_id: 0,
  description: '',
  judge_mode: 'stdio',
  samples: [{ stdin: '', stdout: '' }],
  hidden: [],
})

function openCreateDialog() {
  createDialogVisible.value = true
  if (!chapters.value.length) {
    fetchAdminChapters()
      .then((data) => {
        chapters.value = data
      })
      .catch(() => {
        ElMessage.warning('章节列表加载失败，仍可创建题目但无法挂载')
      })
  }
}

function resetCreateForm() {
  createForm.slug = ''
  createForm.title = ''
  createForm.module_key = ''
  createForm.difficulty = 'medium'
  createForm.lc_id = 0
  createForm.description = ''
  createForm.judge_mode = 'stdio'
  createForm.samples = [{ stdin: '', stdout: '' }]
  createForm.hidden = []
}

function addCreateSample() {
  if (!createForm.samples) createForm.samples = []
  createForm.samples.push({ stdin: '', stdout: '' })
}

function removeCreateSample(idx: number) {
  createForm.samples?.splice(idx, 1)
}

async function submitCreate() {
  if (!createForm.slug.trim() || !createForm.title.trim()) {
    ElMessage.warning('请填写题目 slug 和标题')
    return
  }
  createLoading.value = true
  try {
    await createProblem({ ...createForm })
    ElMessage.success(`题目 ${createForm.slug} 创建成功`)
    createDialogVisible.value = false
    resetCreateForm()
    await loadProblems()
  } catch {
    ElMessage.error('创建失败，slug 可能已存在')
  } finally {
    createLoading.value = false
  }
}

// ──────────────────────────── 挂载到章节 ────────────────────────────
const attachDialogVisible = ref(false)
const attachSlug = ref('')
const attachChapterId = ref('')
const attachLoading = ref(false)

function openAttachDialog(slug: string) {
  attachSlug.value = slug
  attachChapterId.value = ''
  attachDialogVisible.value = true
  if (!chapters.value.length) {
    fetchAdminChapters()
      .then((data) => {
        chapters.value = data
      })
      .catch(() => {
        ElMessage.warning('章节列表加载失败')
      })
  }
}

async function submitAttach() {
  if (!attachChapterId.value) {
    ElMessage.warning('请选择章节')
    return
  }
  attachLoading.value = true
  try {
    const result = await attachProblemToChapter(attachSlug.value, attachChapterId.value)
    ElMessage.success(`已将 ${attachSlug.value} 挂载到章节`)
    attachDialogVisible.value = false
    // 更新本地章节列表
    const ch = chapters.value.find((c) => c.id === attachChapterId.value)
    if (ch) ch.recommended_problems = result.recommended_problems
  } catch {
    ElMessage.error('挂载失败')
  } finally {
    attachLoading.value = false
  }
}

const difficultyOptions = [
  { label: '简单', value: 'easy' },
  { label: '中等', value: 'medium' },
  { label: '困难', value: 'hard' },
]

const judgeModeOptions = [
  { label: '标准输入输出 (stdio)', value: 'stdio' },
  { label: '力扣方法签名 (leetcode)', value: 'leetcode' },
]

const moduleOptions = ALGORITHM_MODULES.map((m) => ({
  label: m.label,
  value: m.key,
}))

onMounted(loadProblems)
</script>

<template>
  <main class="oj-admin">
    <section class="page-hero">
      <div>
        <div class="hero-kicker">OJ MANAGEMENT</div>
        <h1>OJ 题目管理</h1>
        <p>查看与修改测试用例、新增题目、挂载题目到章节课后习题。</p>
      </div>
      <div class="hero-actions">
        <el-button :loading="listLoading" :icon="RefreshRight" @click="loadProblems">刷新</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreateDialog">新增题目</el-button>
      </div>
    </section>

    <section class="summary-grid" aria-label="题库概览">
      <article class="summary-card">
        <span>题目总数</span>
        <strong>{{ allProblems.length }}</strong>
        <small>当前题库收录</small>
      </article>
      <article class="summary-card">
        <span>可判题</span>
        <strong>{{ readyCount }}</strong>
        <small>{{ allProblems.length ? Math.round((readyCount / allProblems.length) * 100) : 0 }}% 已配置测例</small>
      </article>
      <article class="summary-card">
        <span>覆盖模块</span>
        <strong>{{ moduleCount }}</strong>
        <small>知识模块</small>
      </article>
      <article class="summary-card summary-card--result">
        <span>当前结果</span>
        <strong>{{ filteredProblems.length }}</strong>
        <small>{{ searchQuery || moduleFilter ? '筛选后的题目' : '显示全部题目' }}</small>
      </article>
    </section>

    <section class="problem-workspace">
      <div class="filter-bar">
        <div class="filter-fields">
          <el-input
            v-model="searchQuery"
            placeholder="搜索 Slug 或题目名称"
            clearable
            :prefix-icon="Search"
            class="search-input"
          />
          <el-select
            v-model="moduleFilter"
            placeholder="全部知识模块"
            clearable
            class="module-select"
          >
            <el-option
              v-for="m in moduleOptions"
              :key="m.value"
              :label="m.label"
              :value="m.value"
            />
          </el-select>
          <el-button v-if="searchQuery || moduleFilter" text @click="clearFilters">清除筛选</el-button>
        </div>
        <span class="result-count">共 {{ filteredProblems.length }} 道题</span>
      </div>

      <div class="table-frame">
        <el-table
          v-loading="listLoading"
          :data="filteredProblems"
          row-key="slug"
          stripe
          height="100%"
          class="problem-table"
          empty-text="没有符合条件的题目"
        >
          <el-table-column prop="slug" label="Slug" min-width="210" show-overflow-tooltip />
          <el-table-column prop="title" label="题目" min-width="220" show-overflow-tooltip />
          <el-table-column label="知识模块" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">{{ moduleLabel(row.module_key) }}</template>
          </el-table-column>
          <el-table-column label="难度" width="104" align="center">
            <template #default="{ row }">
              <el-tag :type="difficultyMeta(row.difficulty).type" size="small" effect="plain">
                {{ difficultyMeta(row.difficulty).label }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="判题状态" width="112" align="center">
            <template #default="{ row }">
              <el-tag :type="row.ready ? 'success' : 'info'" size="small">
                {{ row.ready ? '可判题' : '待完善' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="300" align="right">
            <template #default="{ row }">
              <el-button size="small" @click="openCasesDialog(row.slug)">测试用例</el-button>
              <el-button size="small" type="primary" plain @click="openAttachDialog(row.slug)">
                挂载章节
              </el-button>
              <router-link :to="`/practice/${row.slug}`" class="view-link">
                <el-button size="small" text>预览</el-button>
              </router-link>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </section>

    <!-- 测试用例编辑弹窗 -->
    <el-dialog
      v-model="casesDialogVisible"
      title="测试用例编辑"
      width="920px"
      :close-on-click-modal="false"
      class="cases-dialog"
    >
      <div v-loading="casesLoading" class="cases-body">
        <template v-if="currentCases">
          <div class="cases-header">
            <div class="cases-title">
              <h3>{{ currentCases.title }}</h3>
              <div class="cases-meta">
                <el-tag size="small" type="info">slug: {{ currentCases.slug }}</el-tag>
                <el-tag size="small">{{ currentCases.judge_mode }}</el-tag>
              </div>
            </div>
          </div>

          <el-tabs class="cases-tabs">
            <el-tab-pane :label="`样例测例 (${editableSamples.length})`">
              <div v-if="editableSamples.length" class="cases-list">
                <div
                  v-for="(tc, idx) in editableSamples"
                  :key="idx"
                  class="case-item case-item--sample"
                >
                  <div class="case-head">
                    <div class="case-head-left">
                      <span class="case-badge case-badge--sample">{{ idx + 1 }}</span>
                      <span class="case-type-label">样例测例</span>
                    </div>
                    <el-button
                      size="small"
                      type="danger"
                      text
                      :icon="Delete"
                      @click="removeSample(idx)"
                    >删除</el-button>
                  </div>
                  <div class="case-fields">
                    <div class="case-field">
                      <label class="case-field-label">
                        <span class="dot dot--in"></span>stdin
                      </label>
                      <el-input
                        v-model="tc.stdin"
                        type="textarea"
                        :rows="3"
                        placeholder="标准输入内容"
                        class="case-textarea"
                      />
                    </div>
                    <div class="case-field">
                      <label class="case-field-label">
                        <span class="dot dot--out"></span>stdout
                      </label>
                      <el-input
                        v-model="tc.stdout"
                        type="textarea"
                        :rows="3"
                        placeholder="期望标准输出"
                        class="case-textarea"
                      />
                    </div>
                    <div class="case-field case-field--full">
                      <label class="case-field-label">
                        expected
                        <span class="case-field-hint">(leetcode 模式填期望返回值，stdio 模式可留空)</span>
                      </label>
                      <el-input
                        v-model="tc.expected as string"
                        placeholder="如 [2, 7, 11, 15] 或 true"
                      />
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="cases-empty">
                暂无样例测例，点击下方按钮添加
              </div>
              <el-button class="add-btn" :icon="Plus" @click="addSample">添加样例测例</el-button>
            </el-tab-pane>

            <el-tab-pane :label="`隐藏测例 (${editableHidden.length})`">
              <div v-if="editableHidden.length" class="cases-list">
                <div
                  v-for="(tc, idx) in editableHidden"
                  :key="idx"
                  class="case-item case-item--hidden"
                >
                  <div class="case-head">
                    <div class="case-head-left">
                      <span class="case-badge case-badge--hidden">{{ idx + 1 }}</span>
                      <span class="case-type-label">隐藏测例</span>
                    </div>
                    <el-button
                      size="small"
                      type="danger"
                      text
                      :icon="Delete"
                      @click="removeHidden(idx)"
                    >删除</el-button>
                  </div>
                  <div class="case-fields">
                    <div class="case-field">
                      <label class="case-field-label">
                        <span class="dot dot--in"></span>stdin
                      </label>
                      <el-input
                        v-model="tc.stdin"
                        type="textarea"
                        :rows="3"
                        placeholder="标准输入内容"
                        class="case-textarea"
                      />
                    </div>
                    <div class="case-field">
                      <label class="case-field-label">
                        <span class="dot dot--out"></span>stdout
                      </label>
                      <el-input
                        v-model="tc.stdout"
                        type="textarea"
                        :rows="3"
                        placeholder="期望标准输出"
                        class="case-textarea"
                      />
                    </div>
                    <div class="case-field case-field--full">
                      <label class="case-field-label">
                        expected
                        <span class="case-field-hint">(leetcode 模式填期望返回值，stdio 模式可留空)</span>
                      </label>
                      <el-input
                        v-model="tc.expected as string"
                        placeholder="如 [2, 7, 11, 15] 或 true"
                      />
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="cases-empty">
                暂无隐藏测例，点击下方按钮添加
              </div>
              <el-button class="add-btn" :icon="Plus" @click="addHidden">添加隐藏测例</el-button>
            </el-tab-pane>
          </el-tabs>
        </template>
      </div>

      <template #footer>
        <el-button @click="casesDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="casesSaving" @click="saveCases">
          保存测例
        </el-button>
      </template>
    </el-dialog>

    <!-- 新增题目弹窗 -->
    <el-dialog
      v-model="createDialogVisible"
      title="新增题目"
      width="720px"
      :close-on-click-modal="false"
    >
      <el-form :model="createForm" label-width="120px" label-position="right">
        <el-form-item label="题目 Slug" required>
          <el-input
            v-model="createForm.slug"
            placeholder="如 my-new-problem（英文、数字、连字符）"
          />
        </el-form-item>
        <el-form-item label="题目标题" required>
          <el-input v-model="createForm.title" placeholder="如：我的新题目" />
        </el-form-item>
        <el-form-item label="所属模块">
          <el-select v-model="createForm.module_key" placeholder="选择模块" clearable>
            <el-option
              v-for="m in moduleOptions"
              :key="m.value"
              :label="m.label"
              :value="m.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="难度">
          <el-select v-model="createForm.difficulty">
            <el-option
              v-for="d in difficultyOptions"
              :key="d.value"
              :label="d.label"
              :value="d.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="力扣题号">
          <el-input-number v-model="createForm.lc_id" :min="0" controls-position="right" />
        </el-form-item>
        <el-form-item label="判题模式">
          <el-select v-model="createForm.judge_mode">
            <el-option
              v-for="j in judgeModeOptions"
              :key="j.value"
              :label="j.label"
              :value="j.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="题目描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="4"
            placeholder="Markdown 格式的题目描述"
          />
        </el-form-item>
        <el-form-item label="样例测例">
          <div class="create-cases">
            <div
              v-for="(tc, idx) in createForm.samples"
              :key="idx"
              class="case-item case-item--sample"
            >
              <div class="case-head">
                <div class="case-head-left">
                  <span class="case-badge case-badge--sample">{{ idx + 1 }}</span>
                  <span class="case-type-label">样例</span>
                </div>
                <el-button
                  v-if="createForm.samples && createForm.samples.length > 1"
                  size="small"
                  type="danger"
                  text
                  :icon="Delete"
                  @click="removeCreateSample(idx)"
                >删除</el-button>
              </div>
              <div class="case-fields">
                <div class="case-field">
                  <label class="case-field-label">
                    <span class="dot dot--in"></span>stdin
                  </label>
                  <el-input v-model="tc.stdin" type="textarea" :rows="3" placeholder="标准输入" class="case-textarea" />
                </div>
                <div class="case-field">
                  <label class="case-field-label">
                    <span class="dot dot--out"></span>stdout
                  </label>
                  <el-input v-model="tc.stdout" type="textarea" :rows="3" placeholder="期望输出" class="case-textarea" />
                </div>
              </div>
            </div>
            <el-button class="add-btn" :icon="Plus" @click="addCreateSample">添加样例</el-button>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="submitCreate">
          创建题目
        </el-button>
      </template>
    </el-dialog>

    <!-- 挂载到章节弹窗 -->
    <el-dialog
      v-model="attachDialogVisible"
      title="挂载题目到章节"
      width="520px"
      :close-on-click-modal="false"
    >
      <div class="attach-content">
        <p class="attach-slug">题目：<strong>{{ attachSlug }}</strong></p>
        <p class="attach-hint">选择要挂载到的章节，题目将追加到该章节的「课后习题」列表末尾。</p>
        <el-select
          v-model="attachChapterId"
          placeholder="选择章节"
          class="attach-select"
          filterable
        >
          <el-option
            v-for="ch in chapters"
            :key="ch.id"
            :label="`${ch.id} — ${ch.title}`"
            :value="ch.id"
          />
        </el-select>
        <div v-if="attachChapterId" class="attach-current">
          <span>当前章节已有题目：</span>
          <div class="attach-tags">
            <el-tag
              v-for="slug in chapters.find(c => c.id === attachChapterId)?.recommended_problems ?? []"
              :key="slug"
              size="small"
              :type="slug === attachSlug ? 'success' : 'info'"
            >
              {{ slug }}
            </el-tag>
            <span v-if="!chapters.find(c => c.id === attachChapterId)?.recommended_problems.length" class="empty-hint">
              暂无题目
            </span>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="attachDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="attachLoading" @click="submitAttach">
          确认挂载
        </el-button>
      </template>
    </el-dialog>
  </main>
</template>

<style scoped>
.oj-admin {
  display: flex;
  width: 100%;
  height: calc(100dvh - var(--alp-header-height, 60px) - 46px);
  min-height: 680px;
  flex-direction: column;
  gap: 16px;
}

.page-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 20px 24px;
  border: 1px solid var(--alp-color-border);
  border-radius: 16px;
  background:
    rgba(58, 138, 158, 0.08),
    var(--alp-bg-surface);
}

.hero-kicker {
  color: var(--alp-color-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.page-hero h1 {
  margin: 6px 0 8px;
  font-size: 26px;
}

.page-hero p {
  margin: 0;
  color: var(--alp-color-muted);
  font-size: 14px;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.summary-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: 2px 12px;
  min-height: 76px;
  padding: 14px 16px;
  border: 1px solid var(--alp-color-border);
  border-radius: 12px;
  background: var(--alp-bg-surface);
}

.summary-card span,
.summary-card small {
  color: var(--alp-color-muted);
  font-size: 12px;
}

.summary-card strong {
  grid-row: 1 / 3;
  grid-column: 2;
  color: var(--alp-color-text);
  font-size: 26px;
  line-height: 1;
}

.summary-card--result {
  border-color: color-mix(in srgb, var(--alp-color-primary) 40%, var(--alp-color-border));
  background: color-mix(in srgb, var(--alp-color-primary) 7%, var(--alp-bg-surface));
}

.problem-workspace {
  display: flex;
  min-height: 0;
  flex: 1;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--alp-color-border);
  border-radius: 14px;
  background: var(--alp-bg-surface);
}

.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--alp-color-border);
}

.filter-fields {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10px;
}

.search-input {
  width: min(360px, 32vw);
}

.module-select {
  width: min(240px, 24vw);
}

.result-count {
  flex-shrink: 0;
  color: var(--alp-color-muted);
  font-size: 12px;
}

.table-frame {
  min-height: 0;
  flex: 1;
}

.problem-table {
  width: 100%;
}

.problem-table :deep(.el-table__header th) {
  height: 46px;
  background: var(--alp-bg-soft-block);
  color: var(--alp-color-text-secondary);
  font-size: 12px;
}

.problem-table :deep(.el-table__row td) {
  height: 48px;
}

@media (min-width: 1101px) {
  .problem-table :deep(.el-scrollbar__wrap) {
    overflow-x: hidden;
  }

  .problem-table :deep(.el-scrollbar__bar.is-horizontal) {
    display: none;
  }
}

.view-link {
  margin-left: 4px;
}

@media (max-width: 1100px) {
  .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .oj-admin { height: auto; min-height: calc(100dvh - var(--alp-header-height, 60px) - 46px); }
  .table-frame { height: 620px; flex: none; }
}

@media (max-width: 720px) {
  .page-hero,
  .filter-bar,
  .filter-fields { align-items: stretch; flex-direction: column; }
  .hero-actions { width: 100%; }
  .hero-actions :deep(.el-button) { flex: 1; }
  .summary-grid { grid-template-columns: 1fr 1fr; }
  .search-input,
  .module-select { width: 100%; }
  .result-count { align-self: flex-end; }
}

.cases-header {
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--alp-color-border);
}

.cases-title h3 {
  margin: 0 0 8px;
  font-size: 17px;
}

.cases-meta {
  display: flex;
  gap: 8px;
}

.cases-tabs {
  min-height: 200px;
}

.cases-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.case-item {
  position: relative;
  padding: 14px 16px 14px 20px;
  border: 1px solid var(--alp-color-border);
  border-radius: 10px;
  background: var(--alp-bg-surface);
  overflow: hidden;
  transition: box-shadow 0.2s ease, border-color 0.2s ease, transform 0.2s ease, filter var(--alp-transition-fast);
}

.case-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--alp-color-primary);
}

.case-item--sample::before {
  background: #52c41a;
}

.case-item--hidden::before {
  background: #fa8c16;
}

.case-item:hover {
  border-color: var(--alp-color-primary);
  transform: translateY(-2px);
  box-shadow: var(--alp-shadow-card-hover);
  filter: brightness(1.06);
}

.case-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.case-head-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.case-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
}

.case-badge--sample {
  background: #52c41a;
}

.case-badge--hidden {
  background: #fa8c16;
}

.case-type-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--alp-color-muted);
}

.case-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.case-field {
  min-width: 0;
}

.case-field--full {
  grid-column: 1 / -1;
}

.case-field-label {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 5px;
  font-size: 12px;
  font-weight: 600;
  color: var(--alp-color-muted);
}

.case-field-hint {
  font-weight: 400;
  font-size: 11px;
  opacity: 0.8;
}

.dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.dot--in {
  background: #1890ff;
}

.dot--out {
  background: #52c41a;
}

.case-textarea :deep(.el-textarea__inner) {
  font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', Consolas, monospace;
  font-size: 12.5px;
  line-height: 1.5;
}

.cases-empty {
  padding: 32px 16px;
  text-align: center;
  color: var(--alp-color-muted);
  font-size: 13px;
  border: 1px dashed var(--alp-color-border);
  border-radius: 10px;
}

.add-btn {
  margin-top: 14px;
  width: 100%;
  height: 40px;
  border-style: dashed;
}

.add-btn:hover {
  border-style: solid;
}

.create-cases {
  width: 100%;
}

.attach-content {
  padding: 4px 0;
}

.attach-slug {
  margin: 0 0 8px;
  font-size: 14px;
}

.attach-hint {
  margin: 0 0 16px;
  color: var(--alp-color-muted);
  font-size: 13px;
}

.attach-select {
  width: 100%;
}

.attach-current {
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px dashed var(--alp-color-border);
  font-size: 13px;
}

.attach-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.empty-hint {
  color: var(--alp-color-muted);
  font-size: 12px;
}
</style>
