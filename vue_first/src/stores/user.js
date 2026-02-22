import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    isLoggedIn: false,
    userInfo: null, // { name: '张三', avatar: '...' }
  }),
  actions: {
    login(userData) {
      this.isLoggedIn = true
      this.userInfo = userData
      // 可同时将 token 存入 localStorage
      localStorage.setItem('token', userData.token)
    },
    logout() {
      this.isLoggedIn = false
      this.userInfo = null
      localStorage.removeItem('token')
    },
    // 初始化时检查本地存储，恢复登录状态（可选）
    init() {
      const token = localStorage.getItem('token')
      if (token) {
        // 这里应调用接口验证 token 并获取用户信息，此处为简化直接假设有效
        this.isLoggedIn = true
        this.userInfo = { name: '已登录用户' } // 实际应从接口获取
      }
    }
  }
})