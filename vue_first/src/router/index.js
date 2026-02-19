import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Recognize from '../views/Recognize.vue'
import Camera from "@/views/Camera.vue";

const routes = [
  { path: '/', component: Login },
  { path: '/register', component: Register },
  { path: '/recognize', component: Recognize },
  { path: '/camera', component: Camera}
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
