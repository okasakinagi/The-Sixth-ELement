<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getRiskControl, getRiskRules, toggleRiskRule, deleteRiskRule, createRiskRule, updateRiskRule } from '@/utils/adminApi'
import { useAdminTheme } from '@/composables/useAdminTheme'

const router = useRouter()
const { initTheme, themeVars } = useAdminTheme()
const riskData = ref(null)
const rulesData = ref([])
const loading = ref(true)
const currentType = ref('short_duration')
const currentTab = ref('events')
const showRuleModal = ref(false)
const editingRule = ref(null)

const riskTypes = [
  { key: 'short_duration', label: '短时长回答' },
  { key: 'suspicious_users', label: '可疑用户' },
  { key: 'abnormal_surveys', label: '异常问卷' },
]

const eventTypeOptions = [
  { value: 'short_duration', label: '短时长回答' },
  { value: 'ip_anomaly', label: 'IP异常' },
  { value: 'device_anomaly', label: '设备异常' },
  { value: 'time_anomaly', label: '时间异常' },
  { value: 'fixed_answer', label: '固定答案检测' },
]

const severityOptions = [
  { value: 'low', label: '低' },
  { value: 'medium', label: '中' },
  { value: 'high', label: '高' },
]

const actionOptions = [
  { value: 'log', label: '仅记录' },
  { value: 'mark_suspicious', label: '标记为可疑' },
  { value: 'restrict_user', label: '禁用用户' },
  { value: 'alert_admin', label: '告警通知管理员' },
]

const newRule = ref({
  rule_code: '',
  rule_name: '',
  description: '',
  priority: 100,
  event_type: 'short_duration',
  severity: 'medium',
  conditions: {},
  actions: ['log'],
})

async function fetchRiskData() {
  try {
    const data = await getRiskControl(currentType.value)
    riskData.value = data
  } catch (e) {
    console.error(e)
  }
}

async function fetchRulesData() {
  try {
    const data = await getRiskRules()
    rulesData.value = data.rules || []
  } catch (e) {
    console.error(e)
  }
}

async function fetchAllData() {
  loading.value = true
  try {
    await Promise.all([fetchRiskData(), fetchRulesData()])
  } finally {
    loading.value = false
  }
}

async function changeType(type) {
  currentType.value = type
  await fetchRiskData()
}

function getSeverityClass(severity) {
  if (severity === 'high') return 'severity-high'
  if (severity === 'medium') return 'severity-medium'
  if (severity === 'low') return 'severity-low'
  return ''
}

function formatDuration(seconds) {
  if (!seconds) return '-'
  return `${seconds}秒`
}

async function handleToggleRule(ruleId) {
  try {
    await toggleRiskRule(ruleId)
    await fetchAllData()
  } catch (e) {
    console.error(e)
  }
}

async function handleDeleteRule(ruleId) {
  if (!confirm('确定要删除这个规则吗？')) return
  try {
    await deleteRiskRule(ruleId)
    await fetchAllData()
  } catch (e) {
    console.error(e)
  }
}

function openCreateRule() {
  editingRule.value = null
  newRule.value = {
    rule_code: '',
    rule_name: '',
    description: '',
    priority: 100,
    event_type: 'short_duration',
    severity: 'medium',
    conditions: {},
    actions: ['log'],
  }
  showRuleModal.value = true
}

function openEditRule(rule) {
  editingRule.value = rule
  newRule.value = { ...rule }
  showRuleModal.value = true
}

async function handleSaveRule() {
  try {
    if (editingRule.value) {
      await updateRiskRule(editingRule.value.id, newRule.value)
    } else {
      await createRiskRule(newRule.value)
    }
    showRuleModal.value = false
    await fetchAllData()
  } catch (e) {
    console.error(e)
  }
}

function formatConditions(conditions) {
  if (!conditions || Object.keys(conditions).length === 0) return '无'
  return JSON.stringify(conditions, null, 2)
}

function formatActions(actions) {
  if (!actions || actions.length === 0) return '无'
  const actionMap = {
    'log': '仅记录',
    'mark_suspicious': '标记为可疑',
    'restrict_user': '禁用用户',
    'alert_admin': '告警通知管理员',
  }
  return actions.map(a => actionMap[a] || a).join(', ')
}

onMounted(() => {
  initTheme()
  fetchAllData()
})
</script>

<template>
  <div class="admin-dashboard" :style="{
    '--admin-bg-primary': themeVars.bgPrimary,
    '--admin-bg-secondary': themeVars.bgSecondary,
    '--admin-bg-card': themeVars.bgCard,
    '--admin-text-primary': themeVars.textPrimary,
    '--admin-text-secondary': themeVars.textSecondary,
    '--admin-text-muted': themeVars.textMuted,
    '--admin-border-color': themeVars.borderColor,
    '--admin-accent-gradient': themeVars.accentGradient,
  }">
    <main class="admin-main">
      
      <header class="page-header">
        <div class="breadcrumb">
          <router-link to="/admin" class="breadcrumb-item">🏠 管理首页</router-link>
          <span class="breadcrumb-sep">/</span>
          <span class="breadcrumb-current">风控与异常监测</span>
        </div>
        <div class="header-top">
          <h1 class="page-title">风控与异常监测</h1>
        </div>
      </header>

      <div v-if="loading" class="loading">加载中...</div>
      <template v-else>
        <section class="section">
          <h2 class="section-title">异常行为统计</h2>
          <div class="stats-grid">
            <div class="stat-card warning">
              <div class="stat-icon">⏱️</div>
              <div class="stat-content">
                <div class="stat-value">{{ riskData?.short_duration_count || 0 }}</div>
                <div class="stat-label">填写时间异常（&lt;10秒）</div>
              </div>
            </div>
            <div class="stat-card danger">
              <div class="stat-icon">👤</div>
              <div class="stat-content">
                <div class="stat-value">{{ riskData?.suspicious_users || 0 }}</div>
                <div class="stat-label">可疑用户数量</div>
              </div>
            </div>
            <div class="stat-card danger">
              <div class="stat-icon">📝</div>
              <div class="stat-content">
                <div class="stat-value">{{ riskData?.abnormal_surveys || 0 }}</div>
                <div class="stat-label">可疑问卷数量</div>
              </div>
            </div>
          </div>
        </section>

        <section class="section">
          <div class="section-header">
            <h2 class="section-title">风控管理</h2>
          </div>
          <div class="type-tabs">
            <button
              :class="['tab-btn', { active: currentTab === 'events' }]"
              @click="currentTab = 'events'"
            >
              事件明细
            </button>
            <button
              :class="['tab-btn', { active: currentTab === 'rules' }]"
              @click="currentTab = 'rules'"
            >
              规则管理
            </button>
          </div>

          <!-- 事件明细 -->
          <div v-if="currentTab === 'events'">
            <div class="type-tabs secondary-tabs">
              <button
                v-for="rt in riskTypes"
                :key="rt.key"
                :class="['tab-btn', { active: currentType === rt.key }]"
                @click="changeType(rt.key)"
              >
                {{ rt.label }}
              </button>
            </div>
            <div v-if="riskData?.items?.length > 0" class="event-list">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>用户</th>
                    <th v-if="currentType === 'short_duration'">问卷</th>
                    <th v-if="currentType === 'short_duration'">填写时长</th>
                    <th v-if="currentType === 'short_duration'">严重程度</th>
                    <th v-if="currentType === 'suspicious_users'">事件类型</th>
                    <th v-if="currentType === 'suspicious_users'">严重程度</th>
                    <th v-if="currentType === 'abnormal_surveys'">问卷</th>
                    <th v-if="currentType === 'abnormal_surveys'">发布者</th>
                    <th v-if="currentType === 'abnormal_surveys'">严重程度</th>
                    <th>时间</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in riskData.items" :key="item.id">
                    <td>{{ item.id }}</td>
                    <td>{{ item.user_nickname || '匿名' }}</td>
                    <td v-if="currentType === 'short_duration'">{{ item.survey_title || '-' }}</td>
                    <td v-if="currentType === 'short_duration'">{{ formatDuration(item.duration_seconds) }}</td>
                    <td v-if="currentType === 'short_duration'">
                      <span class="severity-badge" :class="getSeverityClass(item.severity)">{{ item.severity }}</span>
                    </td>
                    <td v-if="currentType === 'suspicious_users'">{{ item.event_type }}</td>
                    <td v-if="currentType === 'suspicious_users'">
                      <span class="severity-badge" :class="getSeverityClass(item.severity)">{{ item.severity }}</span>
                    </td>
                    <td v-if="currentType === 'abnormal_surveys'">{{ item.survey_title || '-' }}</td>
                    <td v-if="currentType === 'abnormal_surveys'">{{ item.owner_nickname || '-' }}</td>
                    <td v-if="currentType === 'abnormal_surveys'">
                      <span class="severity-badge" :class="getSeverityClass(item.severity)">{{ item.severity }}</span>
                    </td>
                    <td>{{ item.created_at?.slice(0, 19) }}</td>
                  </tr>
                </tbody>
              </table>
              <div class="pagination-info">
                共 {{ riskData.total }} 条记录，第 {{ riskData.page }} / {{ Math.ceil(riskData.total / riskData.page_size) }} 页
              </div>
            </div>
            <div v-else class="empty-state">
              <p>暂无风控事件记录</p>
            </div>
          </div>

          <!-- 规则管理 -->
          <div v-if="currentTab === 'rules'">
            <div class="rules-header">
              <button class="btn-primary" @click="openCreateRule">+ 新建规则</button>
            </div>
            <div v-if="rulesData?.length > 0" class="rules-list">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>规则名称</th>
                    <th>事件类型</th>
                    <th>严重程度</th>
                    <th>优先级</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="rule in rulesData" :key="rule.id">
                    <td>
                      <div class="rule-name">{{ rule.rule_name }}</div>
                      <div class="rule-code">{{ rule.rule_code }}</div>
                      <div v-if="rule.description" class="rule-desc">{{ rule.description }}</div>
                    </td>
                    <td>{{ eventTypeOptions.find(o => o.value === rule.event_type)?.label || rule.event_type }}</td>
                    <td>
                      <span class="severity-badge" :class="getSeverityClass(rule.severity)">{{ severityOptions.find(o => o.value === rule.severity)?.label || rule.severity }}</span>
                    </td>
                    <td>{{ rule.priority }}</td>
                    <td>
                      <span :class="['status-badge', rule.enabled ? 'enabled' : 'disabled']">{{ rule.enabled ? '启用' : '禁用' }}</span>
                    </td>
                    <td>
                      <div class="action-buttons">
                        <button class="btn-sm btn-secondary" @click="openEditRule(rule)">编辑</button>
                        <button class="btn-sm btn-secondary" @click="handleToggleRule(rule.id)">{{ rule.enabled ? '禁用' : '启用' }}</button>
                        <button class="btn-sm btn-danger" @click="handleDeleteRule(rule.id)">删除</button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="empty-state">
              <p>暂无风控规则</p>
            </div>
          </div>
        </section>

        <section class="section">
          <h2 class="section-title">风控说明</h2>
          <div class="info-cards">
            <div class="info-card">
              <h3>填写时间异常</h3>
              <p>用户在短时间内完成问卷填写，视为异常行为。可能是刷单、机器填写等行为。</p>
            </div>
            <div class="info-card">
              <h3>可疑用户</h3>
              <p>被标记为可疑状态的用户，需要管理员审核确认其行为是否违规。</p>
            </div>
            <div class="info-card">
              <h3>可疑问卷</h3>
              <p>存在异常数据的问卷，如完成率异常、答案模式异常等，需要管理员检查。</p>
            </div>
          </div>
        </section>
      </template>
    </main>

    <!-- 规则编辑弹窗 -->
    <div v-if="showRuleModal" class="modal-overlay" @click.self="showRuleModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ editingRule ? '编辑规则' : '新建规则' }}</h3>
          <button class="close-btn" @click="showRuleModal = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>规则编码 *</label>
            <input v-model="newRule.rule_code" type="text" placeholder="例如: short_duration_30s" />
          </div>
          <div class="form-group">
            <label>规则名称 *</label>
            <input v-model="newRule.rule_name" type="text" placeholder="例如: 短时长回答（<30秒）" />
          </div>
          <div class="form-group">
            <label>规则描述</label>
            <textarea v-model="newRule.description" placeholder="描述规则的用途" rows="3"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>优先级</label>
              <input v-model.number="newRule.priority" type="number" min="1" />
            </div>
            <div class="form-group">
              <label>事件类型</label>
              <select v-model="newRule.event_type">
                <option v-for="opt in eventTypeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>严重程度</label>
              <select v-model="newRule.severity">
                <option v-for="opt in severityOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>触发条件 (JSON)</label>
            <textarea v-model="newRule.conditions" placeholder='例如: {"duration_threshold": 30}' rows="4"></textarea>
          </div>
          <div class="form-group">
            <label>处理动作</label>
            <div class="checkbox-group">
              <label v-for="opt in actionOptions" :key="opt.value">
                <input type="checkbox" :value="opt.value" v-model="newRule.actions" />
                {{ opt.label }}
              </label>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showRuleModal = false">取消</button>
          <button class="btn-primary" @click="handleSaveRule">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-dashboard {
  display: flex;
  min-height: 100vh;
  background: var(--admin-bg-primary);
}

.admin-main {
  flex: 1;
  padding: 24px;
  background: var(--admin-bg-primary);
}

.page-header {
  margin-bottom: 24px;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 13px;
}

.breadcrumb-item {
  color: #667eea;
  text-decoration: none;
  transition: all 0.2s ease;
}

.breadcrumb-item:hover {
  color: #764ba2;
  text-decoration: underline;
}

.breadcrumb-sep {
  color: var(--admin-text-muted);
}

.breadcrumb-current {
  color: var(--admin-text-secondary);
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  color: var(--admin-text-primary);
  margin: 0;
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--admin-text-secondary);
}

.section {
  background: var(--admin-bg-card);
  border: 1px solid var(--admin-border-color);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: bold;
  color: var(--admin-text-primary);
  margin: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.stat-card {
  background: var(--admin-bg-secondary);
  border: 1px solid var(--admin-border-color);
  border-radius: 10px;
  padding: 20px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.stat-card.warning {
  background: #fff3e0;
  color: #e65100;
}

.stat-card.danger {
  background: #ffebee;
  color: #c62828;
}

.stat-icon {
  font-size: 32px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: var(--admin-text-primary);
}

.stat-label {
  font-size: 13px;
  color: var(--admin-text-secondary);
  margin-top: 4px;
}

.stat-card.warning .stat-value,
.stat-card.warning .stat-label {
  color: #e65100;
}

.stat-card.danger .stat-value,
.stat-card.danger .stat-label {
  color: #c62828;
}

.info-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.info-card {
  background: var(--admin-bg-secondary);
  border: 1px solid var(--admin-border-color);
  border-radius: 10px;
  padding: 20px;
}

.info-card h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--admin-text-primary);
  margin: 0 0 8px 0;
}

.info-card p {
  font-size: 13px;
  color: var(--admin-text-secondary);
  margin: 0;
  line-height: 1.5;
}

.type-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.secondary-tabs {
  margin-top: 16px;
}

.tab-btn {
  padding: 8px 16px;
  background: var(--admin-bg-secondary);
  border: 1px solid var(--admin-border-color);
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: var(--admin-text-secondary);
  transition: all 0.2s;
}

.tab-btn:hover {
  background: var(--admin-bg-card);
  color: var(--admin-text-primary);
}

.tab-btn.active {
  background: var(--admin-accent-gradient);
  color: white;
  border-color: transparent;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 12px;
}

.data-table th {
  background: var(--admin-bg-secondary);
  padding: 12px 14px;
  text-align: left;
  font-weight: 600;
  font-size: 12px;
  color: var(--admin-text-primary);
  border-bottom: 1px solid var(--admin-border-color);
}

.data-table td {
  padding: 12px 14px;
  font-size: 13px;
  color: var(--admin-text-primary);
  border-bottom: 1px solid var(--admin-border-color);
}

.data-table tr:last-child td {
  border-bottom: none;
}

.severity-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}

.severity-badge.severity-high {
  background: #ffebee;
  color: #c62828;
}

.severity-badge.severity-medium {
  background: #fff3e0;
  color: #ef6c00;
}

.severity-badge.severity-low {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
}

.status-badge.enabled {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-badge.disabled {
  background: #f5f5f5;
  color: #9e9e9e;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--admin-text-muted);
}

.pagination-info {
  margin-top: 16px;
  text-align: center;
  font-size: 13px;
  color: var(--admin-text-secondary);
}

.rule-name {
  font-weight: 600;
  color: var(--admin-text-primary);
}

.rule-code {
  font-size: 12px;
  color: var(--admin-text-muted);
  margin-top: 4px;
}

.rule-desc {
  font-size: 12px;
  color: var(--admin-text-secondary);
  margin-top: 4px;
}

.rules-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.btn-primary {
  background: var(--admin-accent-gradient);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  background: var(--admin-bg-secondary);
  color: var(--admin-text-primary);
  border: 1px solid var(--admin-border-color);
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: var(--admin-bg-card);
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.btn-danger {
  background: #ffebee;
  color: #c62828;
  border: 1px solid #ef9a9a;
}

.btn-danger:hover {
  background: #ffcdd2;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: var(--admin-bg-card);
  border-radius: 16px;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid var(--admin-border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--admin-text-primary);
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--admin-text-muted);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--admin-bg-secondary);
  color: var(--admin-text-primary);
}

.modal-body {
  padding: 24px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 24px;
  border-top: 1px solid var(--admin-border-color);
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--admin-text-primary);
  margin-bottom: 8px;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--admin-border-color);
  border-radius: 8px;
  font-size: 14px;
  background: var(--admin-bg-primary);
  color: var(--admin-text-primary);
  transition: all 0.2s;
  box-sizing: border-box;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 400;
  cursor: pointer;
  margin: 0;
}

.checkbox-group input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}
</style>
