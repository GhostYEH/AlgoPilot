import { createRequire } from 'node:module'
import fs from 'node:fs/promises'
import path from 'node:path'

const require = createRequire(import.meta.url)
const { chromium } = require('C:/Users/32883/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright')

const base = 'http://127.0.0.1:5173'
const outDir = path.resolve('docs/submission/images')
await fs.mkdir(outDir, { recursive: true })

const browser = await chromium.launch({
  headless: true,
  executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
})
const context = await browser.newContext({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 })
const page = await context.newPage()
const consoleErrors = []
page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(`${page.url()} :: ${msg.text()}`) })
page.on('pageerror', (err) => consoleErrors.push(`${page.url()} :: ${err.message}`))

async function settle() {
  await page.waitForLoadState('domcontentloaded')
  await page.waitForTimeout(1800)
  await page.addStyleTag({ content: `
    * { animation-duration: 0s !important; transition-duration: 0s !important; }
    .user-name,.username,.user-email,.avatar-name,.account-name { filter: blur(7px) !important; }
  ` })
  await page.evaluate(() => {
    const sensitive = /demo|teacher_demo|@alp-learning\.example/i
    for (const el of document.querySelectorAll('body *')) {
      if (el.children.length === 0 && sensitive.test(el.textContent || '')) {
        el.style.filter = 'blur(7px)'
      }
    }
  })
}

async function shot(name, url, options = {}) {
  await page.goto(`${base}${url}`, { waitUntil: 'domcontentloaded' })
  await settle()
  if (options.clickText) {
    const target = page.getByText(options.clickText, { exact: false }).first()
    if (await target.count()) {
      await target.click().catch(() => {})
      await page.waitForTimeout(1500)
      await settle()
    }
  }
  await page.screenshot({ path: path.join(outDir, name), fullPage: false })
}

async function login(role) {
  await page.goto(`${base}/login`, { waitUntil: 'domcontentloaded' })
  await settle()
  if (role === 'teacher') await page.getByRole('button', { name: '教师' }).click()
  await page.getByRole('button', { name: /测试账号一键登录/ }).click()
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 20000 })
  await settle()
}

await shot('S01-login-register.png', '/register')
await login('student')
await shot('home-system.png', '/')
await shot('S02-persona-chat.png', '/learning-path?onboarding=1')
await shot('S03-persona-result.png', '/')
await shot('S04-persona-evidence.png', '/my-learning')
await shot('S05-learning-path.png', '/learning-path')
await shot('S06-agent-progress.png', '/agent-workbench')
await shot('S07-generated-resources.png', '/resources')
await shot('S08-oj-list.png', '/practice')
await shot('S09-oj-workbench.png', '/practice/reverse-linked-list')
await shot('S10-trace-visualization.png', '/practice/reverse-linked-list', { clickText: 'Trace' })
await shot('S11-ai-diagnosis.png', '/practice/reverse-linked-list', { clickText: 'AI 深度诊断' })
await shot('S12-learning-dashboard.png', '/my-learning')
await shot('S13-learning-memory.png', '/my-learning', { clickText: '学习记忆' })
await shot('S14-event-log.png', '/my-learning', { clickText: '事件' })
await shot('S15-mastery-update.png', '/my-learning', { clickText: '掌握度' })
await shot('S16-path-replan.png', '/learning-path', { clickText: '重规划' })

await context.clearCookies()
await page.goto(`${base}/login`)
await page.evaluate(() => localStorage.clear())
await login('teacher')
await shot('S17-teacher-dashboard.png', '/teacher-dashboard')
await shot('S18-student-roster.png', '/student-roster')

await fs.writeFile(path.join(outDir, 'playwright-console-errors.txt'), consoleErrors.join('\n'), 'utf8')
await browser.close()
