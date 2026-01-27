import { ref, readonly } from 'vue'

const notifications = ref([])
let notificationId = 0

export function useNotifications() {
  function addNotification(notification) {
    const id = ++notificationId
    const newNotification = {
      id,
      type: 'info',
      timeout: 5000,
      ...notification,
      timestamp: new Date()
    }
    
    notifications.value.unshift(newNotification)
    
    // Auto-remove after timeout
    if (newNotification.timeout > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, newNotification.timeout)
    }
    
    // Keep only last 10 notifications
    if (notifications.value.length > 10) {
      notifications.value = notifications.value.slice(0, 10)
    }
    
    return id
  }
  
  function removeNotification(id) {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index !== -1) {
      notifications.value.splice(index, 1)
    }
  }
  
  function clearAll() {
    notifications.value = []
  }
  
  // Convenience methods
  function success(title, message = '') {
    return addNotification({ type: 'success', title, message, icon: 'mdi-check-circle' })
  }
  
  function error(title, message = '') {
    return addNotification({ type: 'error', title, message, icon: 'mdi-alert-circle', timeout: 8000 })
  }
  
  function warning(title, message = '') {
    return addNotification({ type: 'warning', title, message, icon: 'mdi-alert' })
  }
  
  function info(title, message = '') {
    return addNotification({ type: 'info', title, message, icon: 'mdi-information' })
  }
  
  function alert(alertData) {
    const severityMap = {
      danger: 'error',
      warning: 'warning',
      info: 'info'
    }
    return addNotification({
      type: severityMap[alertData.severity] || 'warning',
      title: 'Alerte Capteur',
      message: alertData.message,
      icon: 'mdi-bell-alert',
      timeout: 10000,
      alert: alertData
    })
  }
  
  return {
    notifications: readonly(notifications),
    addNotification,
    removeNotification,
    clearAll,
    success,
    error,
    warning,
    info,
    alert
  }
}
