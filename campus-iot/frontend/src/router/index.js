import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  // Public routes
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { guest: true, hideNav: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { guest: true, hideNav: true }
  },
  
  // Protected routes
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { 
      icon: 'mdi-view-dashboard', 
      title: 'Dashboard', 
      requiresAuth: true,
      permission: 'dashboard'
    }
  },
  {
    path: '/building',
    name: 'Building',
    component: () => import('@/views/BuildingView.vue'),
    meta: { 
      icon: 'mdi-office-building', 
      title: 'Bâtiment Orion', 
      requiresAuth: true,
      permission: 'building'
    }
  },
  {
    path: '/sensors',
    name: 'Sensors',
    component: () => import('@/views/SensorsView.vue'),
    meta: { 
      icon: 'mdi-chip', 
      title: 'Capteurs', 
      requiresAuth: true,
      permission: 'sensors'
    }
  },
  {
    path: '/alerts',
    name: 'Alerts',
    component: () => import('@/views/AlertsView.vue'),
    meta: { 
      icon: 'mdi-bell-alert', 
      title: 'Alertes', 
      requiresAuth: true,
      permission: 'alerts'
    }
  },
  {
    path: '/control',
    name: 'Control',
    component: () => import('@/views/ControlView.vue'),
    meta: { 
      icon: 'mdi-tune-vertical', 
      title: 'Contrôle', 
      requiresAuth: true,
      permission: 'control',
      roles: ['admin', 'technician']
    }
  },
  {
    path: '/room/:roomId?',
    name: 'Room',
    component: () => import('@/views/RoomView.vue'),
    meta: { 
      icon: 'mdi-floor-plan', 
      title: 'Détail Salle', 
      requiresAuth: true,
      hideInNav: true
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: { 
      icon: 'mdi-cog', 
      title: 'Paramètres', 
      requiresAuth: true
    }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { 
      icon: 'mdi-account-circle', 
      title: 'Mon Profil', 
      requiresAuth: true,
      hideInNav: true
    }
  },
  {
    path: '/activity',
    name: 'Activity',
    component: () => import('@/views/ActivityView.vue'),
    meta: { 
      icon: 'mdi-history', 
      title: 'Journal d\'activité', 
      requiresAuth: true,
      requiresAdmin: true
    }
  },
  {
    path: '/security',
    name: 'Security',
    component: () => import('@/views/SecurityView.vue'),
    meta: { 
      icon: 'mdi-shield-lock', 
      title: 'Sécurité', 
      requiresAuth: true,
      permission: 'security'
    }
  },
  
  // Admin only
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/AdminView.vue'),
    meta: { 
      icon: 'mdi-shield-crown', 
      title: 'Administration', 
      requiresAuth: true,
      requiresAdmin: true,
      adminOnly: true
    }
  },
  
  // Catch all
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login'
  }
]

// Get navigation routes based on user role
export function getNavRoutes(userRole = 'user', permissions = []) {
  const hasPermission = (perm) => permissions.includes('all') || permissions.includes(perm)
  const isAdmin = userRole === 'admin'
  
  return routes.filter(r => {
    // Hide guest routes and hidden routes
    if (r.meta?.hideNav || r.meta?.guest || r.meta?.hideInNav) return false
    
    // Must have an icon to show in nav
    if (!r.meta?.icon) return false
    
    // Admin-only routes
    if (r.meta?.adminOnly && !isAdmin) return false
    
    // Role-based access
    if (r.meta?.roles && !r.meta.roles.includes(userRole)) return false
    
    // Permission-based access
    if (r.meta?.permission && !hasPermission(r.meta.permission)) return false
    
    return true
  })
}

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // Initialize auth if not done
  if (!authStore.user && authStore.token) {
    await authStore.initAuth()
  }
  
  const isAuthenticated = authStore.isAuthenticated
  const isAdmin = authStore.isAdmin
  const userRole = authStore.userRole
  const permissions = authStore.user?.role_info?.permissions || []
  
  // Guest routes - redirect to home if logged in
  if (to.meta.guest && isAuthenticated) {
    return next('/')
  }
  
  // Protected routes - redirect to login if not authenticated
  if (to.meta.requiresAuth && !isAuthenticated) {
    return next('/login')
  }
  
  // Admin routes
  if (to.meta.requiresAdmin && !isAdmin) {
    return next('/')
  }
  
  // Role-based access
  if (to.meta.roles && !to.meta.roles.includes(userRole)) {
    return next('/')
  }
  
  // Permission-based access
  if (to.meta.permission) {
    const hasPermission = permissions.includes('all') || permissions.includes(to.meta.permission)
    if (!hasPermission) {
      return next('/')
    }
  }
  
  next()
})

export default router
export { routes }
