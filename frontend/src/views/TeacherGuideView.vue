<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowRight,
  DataAnalysis,
  DataLine,
  Cpu,
  MagicStick,
  QuestionFilled,
  User,
} from '@element-plus/icons-vue'

const router = useRouter()
const activeTab = ref('guide')

interface GuideStep {
  icon: typeof DataLine
  title: string
  desc: string
  route?: string
  routeLabel?: string
}

const guideSteps: GuideStep[] = [
  {
    icon: DataLine,
    title: '查看教学看板',
    desc: '汇总班级画像、学习进度、OJ 提交与资源记录，一屏掌握教学落地关键指标，自动生成补讲建议与巩固包。',
    route: '/teacher-dashboard',
    routeLabel: '前往教学看板',
  },
  {
    icon: User,
    title: '管理学情数据',
    desc: '逐人查看学生掌握度、学习进度、OJ 提交与薄弱模块，支持搜索与薄弱筛选，点击学生可查看详细学情画像与最近学习记录。',
    route: '/student-roster',
    routeLabel: '前往学情管理',
  },
  {
    icon: Cpu,
    title: '分析 OJ 学情',
    desc: '按模块和题目维度分析全班 OJ 通过率与常见错误，快速定位需要集中讲解的题目与知识点。',
    route: '/oj-analytics',
    routeLabel: '前往 OJ 学情',
  },
  {
    icon: MagicStick,
    title: '生成教学资源',
    desc: '选择知识模块并填写教学聚焦点，一键调用多智能体生成概念讲解、思维导图、分层题单等教学素材。',
    route: '/teacher-workbench',
    routeLabel: '前往资源工作台',
  },
  {
    icon: DataAnalysis,
    title: '管理 OJ 题目',
    desc: '新增题目、编辑测试用例、将题目挂载到章节课后习题，形成教学闭环。',
    route: '/oj-admin',
    routeLabel: '前往 OJ 管理',
  },
]

const faqItems = [
  {
    q: '教学看板的数据从哪里来？',
    a: '教学看板由后端实时聚合真实学生的学习进度、画像、Evaluation、OJ 学习记忆和资源记录生成，不依赖任何模拟数据。学生开始在平台上学习后，数据会自动更新。',
  },
  {
    q: '学情管理中的"薄弱模块"是如何判定的？',
    a: '系统根据学生的 OJ 提交失败、Trace 诊断、练习挣扎等学习记忆事件，提取对应的模块标签。当某学生在某模块累计出现失败信号时，该模块会被标记为薄弱模块。',
  },
  {
    q: '教学资源工作台和学生端的多智能体有什么区别？',
    a: '教师工作台聚焦教学场景：可以选择模块、填写教学聚焦点，生成后的资源可直接用于课堂讲解或课后布置。学生端则根据个人画像自动生成个性化学习资源。',
  },
  {
    q: 'OJ 管理中如何将题目挂载到章节？',
    a: '在 OJ 管理页面点击"挂载题目到章节"按钮，选择目标章节后确认即可。题目会被追加到该章节的课后习题列表末尾，学生可在对应章节练习中看到。',
  },
  {
    q: '如何快速定位需要重点关注的学生？',
    a: '在学情管理页面开启"仅看薄弱学生"筛选开关，系统会自动过滤出有薄弱模块标记的学生。也可以按用户名搜索查看特定学生的详细学情。',
  },
]

const expandedFaq = ref<string[]>([])

function toggleFaq(index: number) {
  const key = String(index)
  if (expandedFaq.value.includes(key)) {
    expandedFaq.value = expandedFaq.value.filter((k) => k !== key)
  } else {
    expandedFaq.value = [...expandedFaq.value, key]
  }
}

function goTo(route: string) {
  router.push(route)
}
</script>

<template>
  <main class="teacher-guide">
    <section class="dashboard-hero">
      <div class="hero-copy">
        <div class="hero-kicker">
          <el-icon><QuestionFilled /></el-icon>
          AlgoPilot 教师指南
        </div>
        <h1>教师使用指南</h1>
        <p>
          快速了解 AlgoPilot 教师端核心功能：教学看板、学情管理、OJ 学情分析、
          教学资源生成与题目管理，将学生学习数据转化为可执行的教学决策。
        </p>
      </div>
    </section>

    <div class="tab-bar">
      <button
        class="tab-btn"
        :class="{ 'is-active': activeTab === 'guide' }"
        @click="activeTab = 'guide'"
      >
        功能指引
      </button>
      <button
        class="tab-btn"
        :class="{ 'is-active': activeTab === 'faq' }"
        @click="activeTab = 'faq'"
      >
        常见问题
      </button>
    </div>

    <!-- 功能指引 -->
    <section v-if="activeTab === 'guide'" class="dashboard-section">
      <div class="section-heading">
        <div>
          <span class="section-eyebrow">QUICK START</span>
          <h2>五步上手教师端</h2>
        </div>
      </div>

      <div class="step-list">
        <article
          v-for="(step, index) in guideSteps"
          :key="index"
          class="step-card"
        >
          <div class="step-number">{{ String(index + 1).padStart(2, '0') }}</div>
          <div class="step-icon">
            <el-icon><component :is="step.icon" /></el-icon>
          </div>
          <div class="step-content">
            <h3>{{ step.title }}</h3>
            <p>{{ step.desc }}</p>
            <button
              v-if="step.route"
              class="step-link"
              @click="goTo(step.route)"
            >
              {{ step.routeLabel }}
              <el-icon><ArrowRight /></el-icon>
            </button>
          </div>
        </article>
      </div>
    </section>

    <!-- 常见问题 -->
    <section v-if="activeTab === 'faq'" class="dashboard-section">
      <div class="section-heading">
        <div>
          <span class="section-eyebrow">FAQ</span>
          <h2>常见问题</h2>
        </div>
      </div>

      <div class="faq-list">
        <article
          v-for="(item, index) in faqItems"
          :key="index"
          class="faq-card"
          :class="{ 'is-open': expandedFaq.includes(String(index)) }"
          @click="toggleFaq(index)"
        >
          <div class="faq-header">
            <h3>{{ item.q }}</h3>
            <el-icon class="faq-arrow"><ArrowRight /></el-icon>
          </div>
          <div v-if="expandedFaq.includes(String(index))" class="faq-answer">
            <p>{{ item.a }}</p>
          </div>
        </article>
      </div>
    </section>

    <section class="dashboard-section contact-card">
      <div class="contact-content">
        <el-icon class="contact-icon"><QuestionFilled /></el-icon>
        <div>
          <h3>还有其他问题？</h3>
          <p>如果以上内容未能解决您的疑问，请检查后端服务是否正常运行，或联系平台管理员获取支持。</p>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.teacher-guide {
  width: min(1080px, 100%);
  margin: 0 auto;
  color: var(--alp-color-text);
}

.dashboard-hero {
  position: relative;
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 28px 30px;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--alp-color-primary) 32%, var(--alp-color-border));
  border-radius: 18px;
  background:
    rgba(58, 138, 158, 0.2),
    rgba(14, 116, 144, 0.22),
    var(--alp-bg-surface);
  box-shadow: var(--alp-shadow-card);
}

.dashboard-hero::after {
  position: absolute;
  right: 8%;
  bottom: -90px;
  width: 260px;
  height: 260px;
  content: '';
  border: 1px solid rgba(34, 211, 238, 0.16);
  border-radius: 50%;
  box-shadow: 0 0 0 34px rgba(34, 211, 238, 0.04), 0 0 0 70px rgba(129, 140, 248, 0.03);
  pointer-events: none;
}

.hero-copy {
  position: relative;
  z-index: 1;
}

.hero-copy h1 {
  margin: 8px 0 10px;
  font-size: clamp(28px, 4vw, 42px);
  line-height: 1.15;
}

.hero-copy p {
  max-width: 760px;
  margin: 0;
  color: var(--alp-color-muted);
  font-size: 15px;
  line-height: 1.8;
}

.hero-kicker,
.section-eyebrow {
  color: var(--alp-color-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.hero-kicker {
  display: flex;
  align-items: center;
  gap: 7px;
}

.tab-bar {
  display: flex;
  gap: 8px;
  margin-top: 24px;
}

.tab-btn {
  padding: 8px 18px;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-pill);
  background: var(--alp-bg-surface);
  color: var(--alp-color-muted);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--alp-transition-fast);
}

.tab-btn:hover {
  border-color: var(--alp-color-primary);
  color: var(--alp-color-primary);
}

.tab-btn.is-active {
  border-color: var(--alp-color-primary);
  background: color-mix(in srgb, var(--alp-color-primary) 14%, transparent);
  color: var(--alp-color-primary);
  box-shadow: var(--alp-shadow-btn);
}

.dashboard-section {
  margin-top: 24px;
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.section-heading h2 {
  margin: 4px 0 0;
  font-size: 20px;
}

.step-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.step-card {
  display: grid;
  grid-template-columns: 44px 48px 1fr;
  align-items: start;
  gap: 16px;
  padding: 20px;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-surface);
  transition: transform var(--alp-transition-fast), border-color var(--alp-transition-fast), filter var(--alp-transition-fast);
}

.step-card:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--alp-color-primary) 40%, var(--alp-color-border));
  box-shadow: var(--alp-shadow-card-hover);
  filter: brightness(1.04);
}

.step-number {
  color: color-mix(in srgb, var(--alp-color-primary) 70%, var(--alp-color-muted));
  font-size: 22px;
  font-weight: 800;
  line-height: 1;
}

.step-icon {
  display: grid;
  width: 48px;
  height: 48px;
  place-items: center;
  border-radius: 12px;
  background: color-mix(in srgb, var(--alp-color-primary) 12%, transparent);
  color: var(--alp-color-primary);
  font-size: 22px;
}

.step-content h3 {
  margin: 0 0 6px;
  font-size: 16px;
}

.step-content p {
  margin: 0;
  color: var(--alp-color-muted);
  font-size: 13px;
  line-height: 1.7;
}

.step-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 12px;
  padding: 6px 14px;
  border: 1px solid var(--alp-color-primary);
  border-radius: var(--alp-radius-pill);
  background: transparent;
  color: var(--alp-color-primary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--alp-transition-fast);
}

.step-link:hover {
  background: color-mix(in srgb, var(--alp-color-primary) 14%, transparent);
  transform: translateY(-1px);
  box-shadow: var(--alp-shadow-btn);
}

.step-link .el-icon {
  font-size: 11px;
  transition: transform var(--alp-transition-fast);
}

.step-link:hover .el-icon {
  transform: translateX(2px);
}

.faq-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.faq-card {
  padding: 16px 20px;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  background: var(--alp-bg-surface);
  cursor: pointer;
  transition: border-color var(--alp-transition-fast), filter var(--alp-transition-fast);
}

.faq-card:hover {
  border-color: color-mix(in srgb, var(--alp-color-primary) 30%, var(--alp-color-border));
  filter: brightness(1.03);
}

.faq-card.is-open {
  border-color: color-mix(in srgb, var(--alp-color-primary) 40%, var(--alp-color-border));
}

.faq-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.faq-header h3 {
  margin: 0;
  font-size: 15px;
}

.faq-arrow {
  color: var(--alp-color-muted);
  font-size: 14px;
  transition: transform var(--alp-transition-fast);
}

.faq-card.is-open .faq-arrow {
  transform: rotate(90deg);
  color: var(--alp-color-primary);
}

.faq-answer {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--alp-color-border);
}

.faq-answer p {
  margin: 0;
  color: var(--alp-color-muted);
  font-size: 13px;
  line-height: 1.8;
}

.contact-card {
  padding: 24px;
  border: 1px solid var(--alp-color-border);
  border-radius: var(--alp-radius-card);
  background: color-mix(in srgb, var(--alp-color-primary) 6%, var(--alp-bg-surface));
}

.contact-content {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.contact-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: color-mix(in srgb, var(--alp-color-primary) 14%, transparent);
  color: var(--alp-color-primary);
  font-size: 20px;
}

.contact-content h3 {
  margin: 0 0 4px;
  font-size: 15px;
}

.contact-content p {
  margin: 0;
  color: var(--alp-color-muted);
  font-size: 13px;
  line-height: 1.7;
}

@media (max-width: 760px) {
  .step-card {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .step-number {
    font-size: 18px;
  }

  .step-icon {
    width: 40px;
    height: 40px;
    font-size: 18px;
  }
}
</style>
