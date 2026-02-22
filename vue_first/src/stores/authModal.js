import { defineStore } from 'pinia'

export const useAuthModalStore = defineStore('authModal', {
  state: () => ({
    visible: false,
    mode: 'login', // 'login' 或 'register'
  }),
  actions: {
    open(mode = 'login') {
      this.mode = mode
      this.visible = true
    },
    close() {
      this.visible = false
    },
  }
})