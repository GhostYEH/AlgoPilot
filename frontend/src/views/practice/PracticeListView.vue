<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { fetchProblems, type ProblemListItem } from '@/api/oj'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const list = ref<ProblemListItem[]>([])
const q = ref((route.query.q as string) || '')

async function load() {
  loading.value = true
  try {
    list.value = await fetchProblems(q.value.trim() || undefined)
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

function onSearch() {
  router.replace({ query: q.value.trim() ? { q: q.value.trim() } : {} })
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
        @keyup.enter="onSearch"
      >
        <template #append>
          <el-button :icon="Search" @click="onSearch">搜索</el-button>
        </template>
      </el-input>
    </div>

    <el-table v-loading="loading" :data="list" stripe class="problem-table">
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
}
.search-input {
  max-width: 420px;
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
