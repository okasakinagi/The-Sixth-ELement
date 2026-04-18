import { ref, watch, computed } from 'vue'

const STORAGE_KEY = 'admin_theme'

const isDark = ref(false)

const themeVars = computed(() => {
  if (isDark.value) {
    return {
      bgPrimary: '#121212',
      bgSecondary: '#1e1e1e',
      bgCard: '#252525',
      textPrimary: '#ffffff',
      textSecondary: '#e0e0e0',
      textMuted: '#9e9e9e',
      borderColor: '#333333',
      accentGradient: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
    }
  }
  return {
    bgPrimary: '#ffffff',
    bgSecondary: '#f5f7fa',
    bgCard: '#ffffff',
    textPrimary: '#1a1a2e',
    textSecondary: '#666666',
    textMuted: '#999999',
    borderColor: '#e8ecf0',
    accentGradient: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
  }
})

function initTheme() {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    isDark.value = saved === 'dark'
  } else {
    isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
  }
  applyTheme()
}

function toggleTheme() {
  isDark.value = !isDark.value
  localStorage.setItem(STORAGE_KEY, isDark.value ? 'dark' : 'light')
  applyTheme()
}

function applyTheme() {
  const vars = themeVars.value
  const root = document.documentElement

  root.style.setProperty('--admin-bg-primary', vars.bgPrimary)
  root.style.setProperty('--admin-bg-secondary', vars.bgSecondary)
  root.style.setProperty('--admin-bg-card', vars.bgCard)
  root.style.setProperty('--admin-text-primary', vars.textPrimary)
  root.style.setProperty('--admin-text-secondary', vars.textSecondary)
  root.style.setProperty('--admin-text-muted', vars.textMuted)
  root.style.setProperty('--admin-border-color', vars.borderColor)
  root.style.setProperty('--admin-accent-gradient', vars.accentGradient)

  document.body.classList.toggle('admin-dark', isDark.value)
  document.body.classList.toggle('admin-light', !isDark.value)
}

export function useAdminTheme() {
  return {
    isDark,
    themeVars,
    initTheme,
    toggleTheme,
  }
}
