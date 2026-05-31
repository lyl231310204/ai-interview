import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', () => {
  const role = ref('')
  const username = ref('')
  const isHR = computed(() => role.value === 'hr')
  const isLoggedIn = computed(() => !!role.value)

  const login = (r: string, name: string) => {
    role.value = r
    username.value = name
    localStorage.setItem('role', r)
    localStorage.setItem('token', 'ok')
    localStorage.setItem('user', JSON.stringify({ username: name }))
  }

  const logout = () => {
    role.value = ''
    username.value = ''
    localStorage.clear()
  }

  // 从 localStorage 恢复
  const restore = () => {
    if (!role.value) {
      const r = localStorage.getItem('role') || ''
      if (r) {
        role.value = r
        const u = localStorage.getItem('user') || '{}'
        try { username.value = JSON.parse(u).username || '' } catch {}
      }
    }
  }

  return { role, username, isHR, isLoggedIn, login, logout, restore }
})
