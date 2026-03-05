<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  downloadAnalyticsExport,
  getAnalyticsQuestions,
  getAnalyticsSummary,
} from '../utils/analyticsApi.js'

const route = useRoute()
const router = useRouter()
const surveyId = computed(() => route.params.id)
const goBack = () => router.back()

// ─── 加载状态 ──────────────────────────────────
const loading = ref(true)
const error = ref('')

// ─── 数据 ─────────────────────────────────────
const overview = ref(null)
const questions = ref([])

// ─── 初始加载 ─────────────────────────────────
onMounted(async () => {
  try {
    const [summaryData, questionsData] = await Promise.all([
      getAnalyticsSummary(surveyId.value),
      getAnalyticsQuestions(surveyId.value, 1, 50),
    ])
    overview.value = summaryData
    questions.value = questionsData.items || []
  } catch (e) {
    error.value = e.message || '数据加载失败'
  } finally {
    loading.value = false
  }
})

// ─── 题型中文标签 ──────────────────────────────
const TYPE_LABEL = {
  single:       '单选题',
  multi:        '多选题',
  text:         '填空题',
  'multi-text': '多项填空',
  scale:        '量表题',
}
function typeLabel(type) { return TYPE_LABEL[type] || type }

// ─── 文本题分页（客户端，每次加载 50 条本地分页） ──
const textPage = ref({})
const TEXT_PAGE_SIZE = 4

function getTextPage(qid) { return textPage.value[qid] || 1 }
function setTextPage(qid, p) { textPage.value = { ...textPage.value, [qid]: p } }
function pagedTexts(q) {
  const p = getTextPage(q.question_id)
  const start = (p - 1) * TEXT_PAGE_SIZE
  return (q.texts || []).slice(start, start + TEXT_PAGE_SIZE)
}
function textPages(q) {
  return Math.max(1, Math.ceil((q.texts_total || 0) / TEXT_PAGE_SIZE))
}

// ─── 格式化工具 ────────────────────────────────
function fmtDate(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}
function fmtDuration(secs) {
  if (!secs && secs !== 0) return '-'
  const m = Math.floor(secs / 60)
  const s = secs % 60
  return m > 0 ? `${m} 分 ${s} 秒` : `${s} 秒`
}
function pct(ratio) {
  if (ratio == null) return '-'
  return `${(ratio * 100).toFixed(1)}%`
}

// ─── 导出 ─────────────────────────────────────
const exporting = ref({ csv: false, xlsx: false })

function buildFilename(ext) {
  const titleSlug = (overview.value?.title || surveyId.value || 'survey')
    .replace(/[\\/:*?"<>|\s]+/g, '_')
    .slice(0, 40)
  const ts = new Date().toISOString().slice(0, 16).replace('T', '_').replace(':', '')
  return `${titleSlug}_${ts}.${ext}`
}

async function handleExport(format) {
  exporting.value[format] = true
  try {
    await downloadAnalyticsExport(surveyId.value, format, buildFilename(format))
  } catch (e) {
    alert(e.message || '导出失败')
  } finally {
    exporting.value[format] = false
  }
}
</script>

<template>
  <div class="analytics">

    <!-- ── 页头 ── -->
    <header class="page-header">
      <button class="back-btn" type="button" @click="goBack">← 返回</button>
      <div>
        <h1>数据分析</h1>
        <p class="subtitle">{{ overview ? overview.title : '加载中...' }}</p>
      </div>
    </header>

    <!-- ── 加载中 ── -->
    <div v-if="loading" class="state-block">
      <div class="spinner"></div>
      <p>数据加载中，请稍候…</p>
    </div>

    <!-- ── 错误 ── -->
    <div v-else-if="error" class="state-block error-block">
      <p>⚠️ {{ error }}</p>
      <button class="ghost-btn" type="button" @click="() => router.go(0)">重新加载</button>
    </div>

    <template v-else>
      <!-- ══════════════════════════════════════
           区域一：总览 Overview
      ══════════════════════════════════════ -->
      <section class="section">
        <div class="overview-header">
          <h2 class="section-title">📋 总览</h2>
          <div class="export-btns">
            <button
              class="primary-btn"
              type="button"
              :disabled="exporting.csv"
              @click="handleExport('csv')"
            >{{ exporting.csv ? '导出中…' : '导出 CSV' }}</button>
            <button
              class="ghost-btn"
              type="button"
              :disabled="exporting.xlsx"
              @click="handleExport('xlsx')"
            >{{ exporting.xlsx ? '导出中…' : '导出 Excel' }}</button>
          </div>
        </div>
        <p class="survey-title-display">{{ overview.title }}</p>

        <div class="overview-grid">
          <article class="ov-card">
            <span class="ov-label">发布时间</span>
            <span class="ov-value">{{ fmtDate(overview.published_at) }}</span>
          </article>
          <article class="ov-card">
            <span class="ov-label">填写人数</span>
            <span class="ov-value accent">{{ overview.responses_count }}</span>
            <span class="ov-sub">总开始填写 {{ overview.total_started_count ?? 0 }} 份</span>
          </article>
          <article class="ov-card">
            <span class="ov-label">目标份数</span>
            <span class="ov-value accent">{{ overview.target ?? '-' }}</span>
            <span class="ov-sub">设定的目标填写数量</span>
          </article>
          <article class="ov-card">
            <span class="ov-label">完成率</span>
            <span class="ov-value accent">{{ overview.completion_rate != null ? pct(overview.completion_rate) : '-' }}</span>
            <div v-if="overview.completion_rate != null" class="progress-track">
              <div class="progress-fill" :style="{ width: pct(overview.completion_rate) }"></div>
            </div>
          </article>
          <article class="ov-card">
            <span class="ov-label">平均用时</span>
            <span class="ov-value">{{ fmtDuration(overview.average_duration_seconds) }}</span>
          </article>
        </div>
      </section>

      <!-- ══════════════════════════════════════
           区域二：单题分析
      ══════════════════════════════════════ -->
      <section class="section">
        <h2 class="section-title">📊 单题分析</h2>

        <div v-if="questions.length === 0" class="no-data">暂无题目数据</div>

        <div v-for="q in questions" :key="q.question_id" class="q-block">
          <div class="q-header">
            <span class="q-no">Q{{ q.order_no }}</span>
            <span class="q-type-badge" :class="'type-' + q.type">{{ typeLabel(q.type) }}</span>
            <span class="q-title">{{ q.title }}</span>
          </div>

          <!-- 单选题：水平柱状图 -->
          <div v-if="q.type === 'single'" class="chart-area">
            <div v-if="!q.options || q.options.length === 0" class="no-data">暂无选项数据</div>
            <template v-else>
              <div v-for="opt in q.options" :key="opt.label" class="bar-row">
                <span class="bar-label">{{ opt.label }}</span>
                <div class="bar-track">
                  <div class="bar-fill bar-single"
                    :style="{ width: opt.ratio > 0 ? pct(opt.ratio) : '0%', minWidth: opt.ratio > 0 ? '4px' : '0' }"
                  ></div>
                </div>
                <span class="bar-stat" :class="{ 'zero-count': opt.count === 0 }">{{ opt.count }} 人 · {{ pct(opt.ratio) }}</span>
              </div>
              <p class="chart-note">共 {{ overview.responses_count }} 份，各选项百分比已标注</p>
            </template>
          </div>

          <!-- 多选题：水平柱状图（百分比 = 选人/总人，可 > 100%） -->
          <div v-else-if="q.type === 'multi'" class="chart-area">
            <div v-if="!q.options || q.options.length === 0" class="no-data">暂无选项数据</div>
            <template v-else>
              <div v-for="opt in q.options" :key="opt.label" class="bar-row">
                <span class="bar-label">{{ opt.label }}</span>
                <div class="bar-track">
                  <div class="bar-fill bar-multi"
                    :style="{ width: opt.ratio > 0 ? Math.min(100, opt.ratio * 100) + '%' : '0%', minWidth: opt.ratio > 0 ? '4px' : '0' }"
                  ></div>
                </div>
                <span class="bar-stat" :class="{ 'zero-count': opt.count === 0 }">{{ opt.count }} 人 · {{ pct(opt.ratio) }}</span>
              </div>
              <p class="chart-note">多选题：百分比 = 选择该项人数 / 总填写人数，总和可超过 100%</p>
            </template>
          </div>

          <!-- 填空题：分页文本列表 -->
          <div v-else-if="q.type === 'text'" class="text-area">
            <div v-if="!q.texts || q.texts.length === 0" class="no-data">暂无填写数据</div>
            <ul v-else class="text-list">
              <li v-for="t in pagedTexts(q)" :key="t.response_id" class="text-item">
                <span class="text-anon">{{ t.anonymous_id }}</span>
                <span class="text-body">{{ t.value }}</span>
                <span class="text-time">{{ fmtDate(t.submitted_at) }}</span>
              </li>
            </ul>
            <div class="text-pagination">
              <button class="ghost-btn" :disabled="getTextPage(q.question_id) <= 1"
                @click="setTextPage(q.question_id, getTextPage(q.question_id) - 1)">上一页</button>
              <span>第 {{ getTextPage(q.question_id) }} / {{ textPages(q) }} 页 · 共 {{ q.texts_total }} 条</span>
              <button class="ghost-btn" :disabled="getTextPage(q.question_id) >= textPages(q)"
                @click="setTextPage(q.question_id, getTextPage(q.question_id) + 1)">下一页</button>
            </div>
          </div>

          <!-- 多项填空题：分页文本列表，value 为数组 -->
          <div v-else-if="q.type === 'multi-text'" class="text-area">
            <div v-if="!q.texts || q.texts.length === 0" class="no-data">暂无填写数据</div>
            <ul v-else class="text-list">
              <li v-for="t in pagedTexts(q)" :key="t.response_id" class="text-item">
                <span class="text-anon">{{ t.anonymous_id }}</span>
                <span class="text-body">{{ Array.isArray(t.value) ? t.value.join(' / ') : t.value }}</span>
                <span class="text-time">{{ fmtDate(t.submitted_at) }}</span>
              </li>
            </ul>
            <div class="text-pagination">
              <button class="ghost-btn" :disabled="getTextPage(q.question_id) <= 1"
                @click="setTextPage(q.question_id, getTextPage(q.question_id) - 1)">上一页</button>
              <span>第 {{ getTextPage(q.question_id) }} / {{ textPages(q) }} 页 · 共 {{ q.texts_total }} 条</span>
              <button class="ghost-btn" :disabled="getTextPage(q.question_id) >= textPages(q)"
                @click="setTextPage(q.question_id, getTextPage(q.question_id) + 1)">下一页</button>
            </div>
          </div>

          <!-- 量表题：水平柱状图 -->
          <div v-else-if="q.type === 'scale'" class="chart-area">
            <div v-if="!q.options || q.options.length === 0" class="no-data">暂无选项数据</div>
            <template v-else>
              <div v-for="opt in q.options" :key="opt.label" class="bar-row">
                <span class="bar-label">{{ opt.label }}</span>
                <div class="bar-track">
                  <div class="bar-fill bar-scale"
                    :style="{ width: opt.ratio > 0 ? pct(opt.ratio) : '0%', minWidth: opt.ratio > 0 ? '4px' : '0' }"
                  ></div>
                </div>
                <span class="bar-stat" :class="{ 'zero-count': opt.count === 0 }">{{ opt.count }} 人 · {{ pct(opt.ratio) }}</span>
              </div>
              <p class="chart-note">共 {{ overview.responses_count }} 份，各分值分布已标注</p>
            </template>
          </div>
        </div>
      </section>
    </template>

  </div>
</template>

<style scoped>
.analytics {
  min-height: 100vh;
  padding: 40px 48px;
  background: radial-gradient(circle at top left, #edf3ff 0%, #f7f9ff 45%, #ffffff 100%);
}

/* ── 页头 ── */
.page-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 36px;
}
.page-header h1 {
  font-family: 'Newsreader', serif;
  font-size: 30px;
  margin: 0 0 4px;
}
.subtitle { color: #7a8fa8; font-size: 13px; margin: 0; }
.back-btn {
  color: #1e4fb4;
  font-weight: 600;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 15px;
  padding: 8px 12px;
  border-radius: 8px;
  white-space: nowrap;
  transition: background 0.2s;
}
.back-btn:hover { background: rgba(30,79,180,0.08); }

/* ── 区域通用 ── */
.section {
  background: #fff;
  border-radius: 20px;
  padding: 28px 32px;
  margin-bottom: 28px;
  box-shadow: 0 8px 24px rgba(16,35,63,0.08);
}
.section-title {
  font-size: 17px;
  font-weight: 700;
  color: #1a2f54;
  margin: 0 0 20px;
}

/* ── 总览头部 ── */
.overview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.overview-header .section-title { margin: 0; }
.export-btns { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }

/* ── 总览 ── */
.survey-title-display {
  font-size: 20px;
  font-weight: 600;
  color: #1e3a6e;
  margin: 0 0 20px;
}
.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}
.ov-card {
  background: #f4f8ff;
  border-radius: 14px;
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.ov-label { font-size: 12px; color: #7a8fa8; }
.ov-value { font-size: 26px; font-weight: 700; color: #1a2f54; }
.ov-value.accent { color: #1e4fb4; }
.ov-sub { font-size: 12px; color: #9aaec4; }
.progress-track {
  height: 8px;
  background: #dce8ff;
  border-radius: 99px;
  overflow: hidden;
  margin-top: 4px;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #2b63d6, #60a5fa);
  border-radius: 99px;
  transition: width 0.6s ease;
}

/* ── 单题块 ── */
.q-block {
  border: 1px solid #e8f0fe;
  border-radius: 14px;
  padding: 20px 24px;
  margin-bottom: 18px;
}
.q-block:last-child { margin-bottom: 0; }
.q-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
  flex-wrap: wrap;
}
.q-no {
  background: #1e4fb4;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 99px;
}
.q-type-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 9px;
  border-radius: 99px;
}
.type-single  { background: #e8f4fd; color: #0369a1; }
.type-multi   { background: #f0fdf4; color: #166534; }
.type-text    { background: #fef9ec; color: #92400e; }
.type-multi-text { background: #fdf4ff; color: #6b21a8; }
.type-scale   { background: #f0f2ff; color: #4f46e5; }
.q-title { font-size: 15px; font-weight: 600; color: #1a2f54; }

/* ── 柱状图 ── */
.chart-area { display: flex; flex-direction: column; gap: 12px; }
.bar-row {
  display: grid;
  grid-template-columns: 120px 1fr 120px;
  align-items: center;
  gap: 12px;
}
.bar-label { font-size: 13px; color: #3d5170; text-align: right; }
.bar-track {
  height: 20px;
  background: #eef3fb;
  border-radius: 99px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  border-radius: 99px;
  transition: width 0.5s ease;
}
.bar-single { background: linear-gradient(90deg, #2b63d6, #60a5fa); }
.bar-multi  { background: linear-gradient(90deg, #059669, #34d399); }
.bar-scale  { background: linear-gradient(90deg, #4f46e5, #818cf8); }
.bar-stat { font-size: 12px; color: #6a7d95; }
.bar-stat.zero-count { color: #b8c8db; }
.chart-note { font-size: 12px; color: #9aaec4; margin-top: 4px; }

/* ── 文本列表 ── */
.text-area { display: flex; flex-direction: column; gap: 12px; }
.text-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.text-item {
  display: grid;
  grid-template-columns: 60px 1fr 88px;
  gap: 10px;
  align-items: start;
  padding: 10px 14px;
  background: #f8faff;
  border-radius: 10px;
  font-size: 13px;
}
.text-anon { color: #9aaec4; font-size: 12px; }
.text-body { color: #253354; line-height: 1.5; }
.text-time { color: #b8c8db; font-size: 11px; text-align: right; }
.text-pagination {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 13px;
  color: #6a7d95;
}
.no-data { color: #b8c8db; font-size: 14px; padding: 12px 0; }

.primary-btn {
  background: linear-gradient(180deg, #2b63d6, #1e4fb4);
  color: #fff;
  border: none;
  padding: 10px 22px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  box-shadow: 0 6px 18px rgba(30,79,180,0.18);
  transition: transform 0.15s;
}
.primary-btn:hover { transform: translateY(-1px); }
.ghost-btn {
  background: transparent;
  border: 1px solid #dce8ff;
  color: #1e4fb4;
  padding: 9px 18px;
  border-radius: 10px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
}
.ghost-btn:hover:not(:disabled) { background: #f0f6ff; }
.ghost-btn:disabled, .disabled-btn { opacity: 0.45; cursor: not-allowed; }

/* ── 加载 / 错误状态 ── */
.state-block {
  text-align: center;
  padding: 80px 20px;
  color: #6a7d95;
  font-size: 15px;
}
.error-block { color: #c0392b; }
.spinner {
  width: 36px;
  height: 36px;
  border: 4px solid #dce8ff;
  border-top-color: #1e4fb4;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ─────────────────────────────────────
   移动端适配 ≤ 640px
───────────────────────────────────── */
@media (max-width: 640px) {
  .analytics { padding: 20px 16px; }

  .page-header { flex-direction: column; gap: 6px; }
  .page-header h1 { font-size: 24px; }

  .section { padding: 18px 16px; }
  .section-title { font-size: 15px; }

  /* 总览头部：导出按钟折行到标题下方 */
  .overview-header { flex-direction: column; align-items: flex-start; }
  .export-btns { width: 100%; }
  .export-btns .primary-btn,
  .export-btns .ghost-btn { flex: 1; text-align: center; font-size: 13px; padding: 9px 10px; }

  /* 总览卡片：2 列 */
  .overview-grid { grid-template-columns: 1fr 1fr; }
  .ov-value { font-size: 22px; }

  /* 柱状图：标签和数据同行，柱子占满宽 */
  .bar-row {
    grid-template-columns: 1fr auto;
    grid-template-rows: auto auto;
    row-gap: 4px;
  }
  .bar-label { text-align: left; grid-column: 1; grid-row: 1; }
  .bar-stat  { grid-column: 2; grid-row: 1; font-size: 11px; white-space: nowrap; }
  .bar-track { grid-column: 1 / -1; grid-row: 2; }

  /* 文本题：时间占满行 */
  .text-item {
    grid-template-columns: 52px 1fr;
    grid-template-rows: auto auto;
  }
  .text-time { grid-column: 1 / -1; text-align: left; }

  .text-pagination { flex-wrap: wrap; justify-content: center; font-size: 12px; }
  .ghost-btn { padding: 7px 12px; font-size: 12px; }
}
</style>
