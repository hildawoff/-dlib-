import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Recognize from '../views/Recognize.vue'

const routes = [
  { path: '/', component: Login },
  { path: '/register', component: Register },
  { path: '/recognize', component: Recognize }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
