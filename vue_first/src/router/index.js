import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Recognize from '../views/Recognize.vue'
import Camera from "../views/Camera.vue"
import Logs from "../views/Logs.vue"
import AdminRegister from '../views/AdminRegister.vue'
import UnknownList from "../views/UnknownList.vue"
import Homepage from "../views/Homepage.vue"
import Layout from "../components/Layout.vue"

const routes = [
  {
    path: '/',
    component: Layout,
    children:[
        { path: '', name: 'Home', component: Login },
        { path: 'register', name: 'register', component: Register },
        { path: 'recognize', name: 'recognize', component: Recognize },
        { path: 'camera', name: 'camera', component: Camera},
        { path: 'logs', name: 'logs', component: Logs},
        { path: 'admin/register', name: 'admin', component: AdminRegister},
        { path: 'unknown-users', name: 'unknown-users', component: UnknownList},
        { path: 'homepage', name: 'homepage', component: Homepage}
    ]
  }
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