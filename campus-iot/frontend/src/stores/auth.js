import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || null)
  const loading = ref(false)
  const error = ref(null)
  const roles = ref({})
  
  // User preferences (synced with Supabase)
  const preferences = ref({
    theme: 'dark',
    default_floor: 'RDC',
    notifications_enabled: true,
    email_alerts: false,
    sound_alerts: true,
    dashboard_layout: {},
    favorite_rooms: []
  })

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isTechnician = computed(() => ['admin', 'technician'].includes(user.value?.role))
  const isManager = computed(() => ['admin', 'manager'].includes(user.value?.role))
  const userRole = computed(() => user.value?.role || 'guest')
  const roleInfo = computed(() => user.value?.role_info || {})

  // Check if user has permission
  function hasPermission(permission) {
    if (!user.value?.role_info?.permissions) return false
    const perms = user.value.role_info.permissions
    return perms.includes('all') || perms.includes(permission)
  }

  // Set axios auth header
  function setAuthHeader(t) {
    if (t) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${t}`
    } else {
      delete axios.defaults.headers.common['Authorization']
    }
  }

  // Initialize auth from localStorage
  async function initAuth() {
    if (token.value) {
      setAuthHeader(token.value)
      try {
        await fetchUser()
        await fetchRoles()
        await fetchPreferences()
      } catch (e) {
        logout()
      }
    }
  }
  
  // Fetch user preferences from API
  async function fetchPreferences() {
    if (!token.value) return
    
    try {
      const response = await axios.get('/api/settings/preferences')
      preferences.value = response.data
      
      // Apply theme
      if (preferences.value.theme) {
        document.documentElement.setAttribute('data-theme', preferences.value.theme)
      }
    } catch (e) {
      console.error('Failed to fetch preferences:', e)
    }
  }
  
  // Update user preferences
  async function updatePreferences(data) {
    try {
      const response = await axios.put('/api/settings/preferences', data)
      preferences.value = response.data
      
      // Apply theme if changed
      if (data.theme) {
        document.documentElement.setAttribute('data-theme', data.theme)
      }
      
      return { success: true }
    } catch (e) {
      console.error('Failed to update preferences:', e)
      return { success: false, error: e.response?.data?.detail || e.message }
    }
  }
  
  // Add room to favorites
  async function addFavoriteRoom(roomId) {
    try {
      const response = await axios.post(`/api/settings/preferences/favorite-room/${roomId}`)
      preferences.value.favorite_rooms = response.data.favorites
      return { success: true }
    } catch (e) {
      return { success: false }
    }
  }
  
  // Remove room from favorites
  async function removeFavoriteRoom(roomId) {
    try {
      const response = await axios.delete(`/api/settings/preferences/favorite-room/${roomId}`)
      preferences.value.favorite_rooms = response.data.favorites
      return { success: true }
    } catch (e) {
      return { success: false }
    }
  }
  
  // Check if room is favorite
  function isRoomFavorite(roomId) {
    return preferences.value.favorite_rooms?.includes(roomId) || false
  }

  // Fetch available roles
  async function fetchRoles() {
    try {
      const response = await axios.get('/api/auth/roles')
      roles.value = response.data
    } catch (e) {
      console.error('Failed to fetch roles:', e)
    }
  }

  // Login
  async function login(email, password) {
    loading.value = true
    error.value = null
    
    try {
      const response = await axios.post('/api/auth/login', { email, password })
      
      token.value = response.data.access_token
      user.value = response.data.user
      
      localStorage.setItem('token', token.value)
      setAuthHeader(token.value)
      
      await fetchRoles()
      
      return { success: true }
    } catch (e) {
      error.value = e.response?.data?.detail || 'Erreur de connexion'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  // Register
  async function register(userData) {
    loading.value = true
    error.value = null
    
    try {
      const response = await axios.post('/api/auth/register', userData)
      
      token.value = response.data.access_token
      user.value = response.data.user
      
      localStorage.setItem('token', token.value)
      setAuthHeader(token.value)
      
      await fetchRoles()
      
      return { success: true }
    } catch (e) {
      error.value = e.response?.data?.detail || 'Erreur lors de l\'inscription'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  // Fetch current user
  async function fetchUser() {
    if (!token.value) return
    
    try {
      const response = await axios.get('/api/auth/me')
      user.value = response.data
    } catch (e) {
      throw e
    }
  }

  // Logout
  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    setAuthHeader(null)
  }

  // Update user profile
  async function updateProfile(data) {
    loading.value = true
    error.value = null
    
    try {
      const response = await axios.put('/api/auth/profile', data)
      user.value = response.data
      return { success: true }
    } catch (e) {
      error.value = e.response?.data?.detail || 'Erreur lors de la mise à jour'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  // Admin: Get all users
  async function getAllUsers() {
    if (!isAdmin.value) return []
    
    try {
      const response = await axios.get('/api/auth/users')
      return response.data
    } catch (e) {
      console.error('Failed to fetch users:', e)
      return []
    }
  }

  // Admin: Update user role
  async function updateUserRole(userId, role) {
    if (!isAdmin.value) return { success: false }
    
    try {
      await axios.put(`/api/auth/users/${userId}/role`, { role })
      return { success: true }
    } catch (e) {
      return { success: false, error: e.response?.data?.detail }
    }
  }

  // Admin: Delete user
  async function deleteUser(userId) {
    if (!isAdmin.value) return { success: false }
    
    try {
      await axios.delete(`/api/auth/users/${userId}`)
      return { success: true }
    } catch (e) {
      return { success: false, error: e.response?.data?.detail }
    }
  }

  return {
    user,
    token,
    loading,
    error,
    roles,
    preferences,
    isAuthenticated,
    isAdmin,
    isTechnician,
    isManager,
    userRole,
    roleInfo,
    hasPermission,
    initAuth,
    fetchRoles,
    fetchPreferences,
    updatePreferences,
    addFavoriteRoom,
    removeFavoriteRoom,
    isRoomFavorite,
    login,
    register,
    fetchUser,
    logout,
    updateProfile,
    getAllUsers,
    updateUserRole,
    deleteUser
  }
})
