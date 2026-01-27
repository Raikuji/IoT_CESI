import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { icon: 'mdi-view-dashboard', title: 'Dashboard' }
  },
  {
    path: '/sensors',
    name: 'Sensors',
    component: () => import('@/views/SensorsView.vue'),
    meta: { icon: 'mdi-chip', title: 'Capteurs' }
  },
  {
    path: '/alerts',
    name: 'Alerts',
    component: () => import('@/views/AlertsView.vue'),
    meta: { icon: 'mdi-bell-alert', title: 'Alertes' }
  },
  {
    path: '/control',
    name: 'Control',
    component: () => import('@/views/ControlView.vue'),
    meta: { icon: 'mdi-tune-vertical', title: 'Contrôle' }
  },
  {
    path: '/room',
    name: 'Room',
    component: () => import('@/views/RoomView.vue'),
    meta: { icon: 'mdi-floor-plan', title: 'Plan Salle' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: { icon: 'mdi-cog', title: 'Paramètres' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
export { routes }
