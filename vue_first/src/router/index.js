import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Recognize from '../views/Recognize.vue'
import Camera from "../views/Camera.vue"
import Logs from "../views/Logs.vue"
import AdminRegister from '../views/AdminRegister.vue'

const routes = [
  { path: '/', component: Login },
  { path: '/register', component: Register },
  { path: '/recognize', component: Recognize },
  { path: '/camera', component: Camera},
  { path: '/logs', component: Logs},
  { path: '/admin/register', component: AdminRegister}
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router


router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.meta.requiresAuth && !token) {
    next('/')
  } else {
    next()
  }
})