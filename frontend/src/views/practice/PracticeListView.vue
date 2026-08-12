<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { fetchProblems, type ProblemListItem } from '@/api/oj'
import { ALGORITHM_MODULES } from '@/constants/modules'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const list = ref<ProblemListItem[]>([])
const q = ref((route.query.q as string) || '')
const moduleFilter = ref((route.query.module as string) || '')

const filteredList = computed(() =>
  moduleFilter.value
    ? list.value.filter((item) => item.module_key === moduleFilter.value)
    : list.value,
)

async function load() {
  loading.value = true
  try {
    list.value = await fetchProblems(q.value.trim() || undefined)
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

onMounted(load)

watch(
  () => route.query.q,
  (v) => {
    q.value = (v as string) || ''
    void load()
  },
)

watch(
  () => route.query.module,
  (value) => {
    moduleFilter.value = (value as string) || ''
  },
)

function applyFilters() {
  router.replace({
    query: {
      ...(q.value.trim() ? { q: q.value.trim() } : {}),
      ...(moduleFilter.value ? { module: moduleFilter.value } : {}),
    },
  })
  void load()
}

function diffTag(d: string) {
  if (d === 'easy') return 'success'
  if (d === 'hard') return 'danger'
  return 'warning'
}
</script>

<template>
  <div class="practice-list-page">
    <header class="page-head">
      <h1>在线 OJ 题库</h1>
      <p class="sub">
        与学习路径题单同步，支持 Python 3 / C++ 在线编写与判题。共 {{ list.length }} 题（带测例题以「可判题」为准；后端离线时可浏览离线题库）。
      </p>
    </header>

    <div class="toolbar">
      <el-input
        v-model="q"
        placeholder="搜索标题或 slug…"
        clearable
        class="search-input"
        @keyup.enter="applyFilters"
      >
        <template #append>
          <el-button :icon="Search" @click="applyFilters">搜索</el-button>
        </template>
      </el-input>
      <el-select
        v-model="moduleFilter"
        clearable
        filterable
        placeholder="按课程模块筛选"
        class="module-select"
        @change="applyFilters"
      >
        <el-option
          v-for="item in ALGORITHM_MODULES"
          :key="item.key"
          :label="item.label"
          :value="item.key"
        />
      </el-select>
    </div>

    <el-table v-loading="loading" :data="filteredList" stripe class="problem-table">
      <el-table-column label="状态" width="88">
        <template #default="{ row }">
          <el-tag v-if="row.ready" type="success" size="small">可判题</el-tag>
          <el-tag v-else type="info" size="small">待完善</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="题目" min-width="220">
        <template #default="{ row }">
          <router-link :to="`/practice/${row.slug}`" class="title-link">{{ row.title }}</router-link>
        </template>
      </el-table-column>
      <el-table-column prop="slug" label="Slug" min-width="180" show-overflow-tooltip />
      <el-table-column label="模块" width="110">
        <template #default="{ row }">
          <el-tag v-if="row.module_key" type="info" size="small">{{ row.module_key }}</el-tag>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
      <el-table-column label="力扣" width="72">
        <template #default="{ row }">
          <span v-if="row.lc_id">{{ row.lc_id }}</span>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
      <el-table-column label="难度" width="88">
        <template #default="{ row }">
          <el-tag :type="diffTag(row.difficulty)" size="small">{{ row.difficulty }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <router-link :to="`/practice/${row.slug}`">
            <el-button type="primary" link size="small">去做题</el-button>
          </router-link>
        </template>
      </el-table-column>
    </el-table>

    <el-empty
      v-if="!loading && filteredList.length === 0"
      description="暂无题目。若后端离线，请确认 frontend/public/oj/bundle.json 可访问"
    >
      <el-button type="primary" plain @click="load">重新加载</el-button>
    </el-empty>
  </div>
</template>

<style scoped>
.practice-list-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 8px 16px 32px;
}
.page-head h1 {
  margin: 0 0 8px;
  font-size: 1.5rem;
}
.sub {
  margin: 0 0 20px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
.toolbar {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}
.search-input {
  max-width: 420px;
}
.module-select {
  width: 220px;
}
.title-link {
  color: var(--el-color-primary);
  text-decoration: none;
}
.title-link:hover {
  text-decoration: underline;
}
.muted {
  color: var(--el-text-color-placeholder);
}
</style>
