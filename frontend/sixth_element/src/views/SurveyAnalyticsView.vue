<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const surveyId = computed(() => route.params.id)

const goBack = () => router.back()

// --- Mock submissions data (示例数据) ---
// 字段映射到数据库列：
// id -> FillRecord.id
// user_id, user_nickname -> AppUser.id / AppUser.nickname
// submitted_at -> FillRecord.created_at
// duration_seconds -> FillRecord.duration_seconds
// status -> FillRecord.status
// points_awarded -> FillRecord.points_awarded
// answers_summary -> 简要答题摘要（用于列表与搜索）
const mockSubmissions = ref([
  { id: 'f_1001', user_id: 'u_201', user_nickname: '小明', submitted_at: '2026-02-25T10:12:00Z', duration_seconds: 190, status: 'approved', points_awarded: 5, raw_answers: { q1: 'A', q2: 'B' } },
  { id: 'f_1002', user_id: 'u_342', user_nickname: '小华', submitted_at: '2026-02-25T11:01:00Z', duration_seconds: 260, status: 'approved', points_awarded: 4, raw_answers: { q1: 'C', q2: 'A' } },
  { id: 'f_1003', user_id: 'u_410', user_nickname: '小红', submitted_at: '2026-02-24T21:22:00Z', duration_seconds: 98, status: 'pending', points_awarded: 0, raw_answers: { q1: 'B' } },
  { id: 'f_1004', user_id: 'u_128', user_nickname: '小刚', submitted_at: '2026-02-23T09:45:00Z', duration_seconds: 420, status: 'rejected', points_awarded: 0, raw_answers: { q1: 'D' } },
  { id: 'f_1005', user_id: 'u_215', user_nickname: '小丽', submitted_at: '2026-02-22T14:30:00Z', duration_seconds: 210, status: 'approved', points_awarded: 5, raw_answers: { q1: 'A', q2: 'C' } },
  { id: 'f_1006', user_id: 'u_999', user_nickname: '小王', submitted_at: '2026-02-20T08:21:00Z', duration_seconds: 130, status: 'approved', points_awarded: 3, raw_answers: { q1: 'B' } },
  { id: 'f_1007', user_id: 'u_501', user_nickname: '小陈', submitted_at: '2026-02-19T18:05:00Z', duration_seconds: 300, status: 'approved', points_awarded: 2, raw_answers: { q1: 'D', q2: 'D' } },
  { id: 'f_1008', user_id: 'u_302', user_nickname: '小李', submitted_at: '2026-02-18T12:10:00Z', duration_seconds: 175, status: 'approved', points_awarded: 4, raw_answers: { q1: 'A' } },
  { id: 'f_1009', user_id: 'u_777', user_nickname: '小赵', submitted_at: '2026-02-17T09:55:00Z', duration_seconds: 240, status: 'pending', points_awarded: 0, raw_answers: { q1: 'C' } },
  { id: 'f_1010', user_id: 'u_888', user_nickname: '小周', submitted_at: '2026-02-16T20:12:00Z', duration_seconds: 200, status: 'approved', points_awarded: 5, raw_answers: { q1: 'B' } },
  { id: 'f_1011', user_id: 'u_123', user_nickname: '小孙', submitted_at: '2026-02-15T15:00:00Z', duration_seconds: 210, status: 'approved', points_awarded: 4, raw_answers: { q1: 'A' } },
  { id: 'f_1012', user_id: 'u_456', user_nickname: '小周2', submitted_at: '2026-02-14T16:45:00Z', duration_seconds: 330, status: 'rejected', points_awarded: 0, raw_answers: { q1: 'D' } },
])

// Filters & pagination state
const keyword = ref('')
const statusFilter = ref('all')
const page = ref(1)
const pageSize = ref(6)
const showSubmissionModal = ref(false)
const selectedSubmission = ref(null)

function openSubmission(s) { selectedSubmission.value = s; showSubmissionModal.value = true }
function closeSubmissionModal() { selectedSubmission.value = null; showSubmissionModal.value = false }

// 状态显示映射（前端显示中文并带样式）
function statusText(status) {
  if (!status) return '-' 
  switch (status) {
    case 'pending': return '待审核'
    case 'approved': return '已通过'
    case 'rejected': return '已拒绝'
    default: return status
  }
}

function statusBadgeClass(status) {
  switch (status) {
    case 'pending': return 'badge-pending'
    case 'approved': return 'badge-approved'
    case 'rejected': return 'badge-rejected'
    default: return 'badge-unknown'
  }
}

const filtered = computed(() => {
  const kw = (keyword.value || '').trim().toLowerCase()
  return mockSubmissions.value.filter((s) => {
    if (statusFilter.value !== 'all' && s.status !== statusFilter.value) return false
    if (!kw) return true
    return (s.id && s.id.toLowerCase().includes(kw)) || (s.user_nickname && s.user_nickname.toLowerCase().includes(kw))
  })
})

const total = computed(() => filtered.value.length)
const pages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
const paginated = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filtered.value.slice(start, start + pageSize.value)
})

const submissionCount = computed(() => mockSubmissions.value.length)
const approvedCount = computed(() => mockSubmissions.value.filter(s => s.status === 'approved').length)
const approvedRate = computed(() => {
  const total = submissionCount.value || 1
  return Math.round((approvedCount.value / total) * 100)
})

function prevPage() { if (page.value > 1) page.value-- }
function nextPage() { if (page.value < pages.value) page.value++ }

// CSV download (当前筛选结果)
function downloadCSV() {
  const rows = [['填报ID', '用户ID', '用户名', '提交时间', '用时(秒)', '状态', '奖励积分']]
  filtered.value.forEach((s) => {
    rows.push([s.id, s.user_id, s.user_nickname, s.submitted_at, String(s.duration_seconds), statusText(s.status), String(s.points_awarded || 0)])
  })
  const csvBody = rows.map((r) => r.map((c) => `"${String(c).replace(/"/g,'""')}"`).join(',')).join('\n')
  // 增加 BOM 避免 Excel 中文乱码
  const csv = '\uFEFF' + csvBody
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `survey_${surveyId.value || 'unknown'}_submissions.csv`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="analytics">
    <header>
      <button class="back" type="button" @click="goBack">← 返回</button>
      <h1>数据分析</h1>
      <p>问卷 {{ surveyId }} 的概览数据（示例）</p>
    </header>

    <section class="grid">
      <article class="card">
        <h2>完成率</h2>
        <p class="metric">100%</p>
        <p class="hint">采集份数已达标（示例）</p>
      </article>
      <article class="card">
        <h2>平均用时</h2>
        <p class="metric">3'12"</p>
        <p class="hint">高于同类问卷 12%（示例）</p>
      </article>
      <article class="card">
        <h2>通过率</h2>
        <p class="metric">{{ approvedRate }}%</p>
        <p class="hint">已通过 {{ approvedCount }} / {{ submissionCount }}（示例）</p>
      </article>
    </section>

    <!-- 答卷列表与筛选 -->
    <section class="submissions">
      <div class="submissions-header">
        <h2>答卷列表（示例数据）</h2>
        <div class="actions">
          <input v-model="keyword" placeholder="搜索 ID / 用户名" />
          <select v-model="statusFilter">
            <option value="all">全部状态</option>
            <option value="approved">已通过</option>
            <option value="pending">待审核</option>
            <option value="rejected">已拒绝</option>
          </select>
          <button class="primary-button" type="button" @click="downloadCSV">导出当前筛选结果</button>
        </div>
      </div>

      <table class="submissions-table">
        <thead>
          <tr>
            <th>填报ID</th>
            <th>用户名</th>
            <th>提交时间</th>
            <th>用时(秒)</th>
            <th>状态</th>
            <th>满意度</th>
            <th>奖励积分</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in paginated" :key="s.id" @click="openSubmission(s)" class="clickable-row">
            <td>{{ s.id }}</td>
            <td>{{ s.user_nickname }}</td>
            <td>{{ s.submitted_at }}</td>
            <td>{{ s.duration_seconds }}</td>
            <td><span :class="['status-badge', statusBadgeClass(s.status)]">{{ statusText(s.status) }}</span></td>
            <td>{{ s.points_awarded }}</td>
          </tr>
          <tr v-if="paginated.length === 0">
            <td colspan="6">没有符合筛选条件的答卷（示例数据）</td>
          </tr>
        </tbody>
      </table>

      <div class="pagination">
        <button class="ghost-button" @click="prevPage" :disabled="page <= 1">上一页</button>
        <span>第 {{ page }} / {{ pages }} 页 · 共 {{ total }} 条</span>
        <button class="ghost-button" @click="nextPage" :disabled="page >= pages">下一页</button>
      </div>
    </section>
    
    <!-- 提交详情模态（示例） -->
    <div v-if="showSubmissionModal" class="modal-backdrop" @click.self="closeSubmissionModal">
      <div class="modal detail-modal">
        <h3>答卷详情：{{ selectedSubmission?.id || '' }}</h3>
        <p><strong>用户ID：</strong> {{ selectedSubmission?.user_id }}</p>
        <p><strong>用户名：</strong> {{ selectedSubmission?.user_nickname }}</p>
        <p><strong>提交时间：</strong> {{ selectedSubmission?.submitted_at }}</p>
        <p><strong>用时：</strong> {{ selectedSubmission?.duration_seconds }} 秒</p>
          <p><strong>状态：</strong> {{ statusText(selectedSubmission?.status) }}</p>
        <p><strong>奖励积分：</strong> {{ selectedSubmission?.points_awarded }}</p>
        <div style="margin-top:8px">
          <strong>原始答案：</strong>
          <pre style="white-space:pre-wrap;background:#f7f9fc;padding:8px;border-radius:6px">{{ selectedSubmission?.raw_answers ? JSON.stringify(selectedSubmission.raw_answers, null, 2) : '-' }}</pre>
        </div>
        <div class="modal-actions">
          <button class="ghost-button" type="button" @click="closeSubmissionModal">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.analytics {
  min-height: 100vh;
  padding: 48px;
  background: radial-gradient(circle at top left, #edf3ff 0%, #f7f9ff 45%, #ffffff 100%);
}

header {
  display: grid;
  gap: 10px;
  margin-bottom: 32px;
}

h1 {
  font-family: 'Newsreader', serif;
  font-size: 32px;
}

.back {
  color: #1e4fb4;
  font-weight: 600;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 15px;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.back:hover {
  background: rgba(30, 79, 180, 0.1);
  transform: translateX(-2px);
}

.grid {
  display: grid;
  gap: 20px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.card {
  background: #ffffff;
  padding: 24px;
  border-radius: 20px;
  box-shadow: 0 14px 30px rgba(16, 35, 63, 0.12);
  display: grid;
  gap: 10px;
}

.metric {
  font-size: 28px;
  font-weight: 600;
  color: #1e4fb4;
}

.hint {
  color: #6a7d95;
}

.submissions {
  margin-top: 28px;
}
.submissions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.submissions-header .actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.submissions-header .actions input,
.submissions-header .actions select {
  height: 38px;
  padding: 6px 10px;
  border: 1px solid #e6eefc;
  border-radius: 8px;
  background: #fff;
}
.primary-button {
  background: linear-gradient(180deg,#2b63d6,#1e4fb4);
  color: #fff;
  border: none;
  padding: 8px 14px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 6px 18px rgba(30,79,180,0.12);
}
.primary-button:hover{ transform: translateY(-1px) }
.ghost-button{
  background: transparent;
  border: 1px solid #dce8ff;
  color: #1e4fb4;
  padding: 6px 10px;
  border-radius: 8px;
  cursor: pointer;
}
.submissions-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}
.submissions-table th,
.submissions-table td {
  padding: 12px 10px;
  border-bottom: 1px solid #eef3fb;
  text-align: left;
}
.pagination {
  margin-top: 12px;
  display: flex;
  gap: 12px;
  align-items: center;
}
.submissions-table tr.clickable-row {
  cursor: pointer;
}
.submissions-table tr.clickable-row:hover {
  background: linear-gradient(90deg, rgba(38,101,212,0.03), rgba(38,101,212,0.02));
}

/* 状态 Badge 样式 */
.status-badge{
  display:inline-block;
  padding:4px 8px;
  border-radius:999px;
  font-size:12px;
  font-weight:600;
}
.badge-pending{ background:#fff7e6; color:#b86b00; border:1px solid rgba(184,107,0,0.08) }
.badge-approved{ background:#ecfbf3; color:#0b7a3a; border:1px solid rgba(11,122,58,0.08) }
.badge-rejected{ background:#fff1f1; color:#9b1e1e; border:1px solid rgba(155,30,30,0.06) }
.badge-unknown{ background:#f4f6f8; color:#536170; border:1px solid rgba(83,97,112,0.06) }

/* 模态样式（简洁） */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1200;
}
.modal.detail-modal {
  background: #ffffff;
  padding: 20px;
  border-radius: 12px;
  width: 520px;
  box-shadow: 0 10px 40px rgba(13,27,55,0.2);
}
.modal.detail-modal h3 {
  margin-top: 0;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}
</style>
