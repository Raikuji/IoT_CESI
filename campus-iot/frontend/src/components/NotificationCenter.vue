<template>
  <div class="notification-center">
    <TransitionGroup name="notification" tag="div" class="notification-list">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        class="notification-item"
        :class="notification.type"
      >
        <div class="notification-icon">
          <v-icon :color="getColor(notification.type)">{{ notification.icon }}</v-icon>
        </div>
        <div class="notification-content">
          <div class="notification-title">{{ notification.title }}</div>
          <div v-if="notification.message" class="notification-message">
            {{ notification.message }}
          </div>
          <div class="notification-time">{{ formatTime(notification.timestamp) }}</div>
        </div>
        <v-btn
          icon
          variant="text"
          size="x-small"
          class="notification-close"
          @click="removeNotification(notification.id)"
        >
          <v-icon size="16">mdi-close</v-icon>
        </v-btn>
        <div class="notification-progress" :style="{ animationDuration: notification.timeout + 'ms' }"></div>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { useNotifications } from '@/composables/useNotifications'

const { notifications, removeNotification } = useNotifications()

function getColor(type) {
  const colors = {
    success: '#22c55e',
    error: '#ef4444',
    warning: '#f59e0b',
    info: '#3b82f6'
  }
  return colors[type] || colors.info
}

function formatTime(date) {
  return new Date(date).toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped lang="scss">
.notification-center {
  position: fixed;
  top: 80px;
  right: 24px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 380px;
  width: 100%;
  pointer-events: none;
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: rgba(30, 30, 40, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  position: relative;
  overflow: hidden;
  pointer-events: auto;

  &.success {
    border-left: 4px solid #22c55e;
  }
  &.error {
    border-left: 4px solid #ef4444;
  }
  &.warning {
    border-left: 4px solid #f59e0b;
  }
  &.info {
    border-left: 4px solid #3b82f6;
  }
}

.notification-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 600;
  font-size: 0.9375rem;
  color: white;
  margin-bottom: 2px;
}

.notification-message {
  font-size: 0.8125rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.4;
}

.notification-time {
  font-size: 0.6875rem;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 4px;
}

.notification-close {
  flex-shrink: 0;
  opacity: 0.5;
  transition: opacity 0.2s;

  &:hover {
    opacity: 1;
  }
}

.notification-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background: linear-gradient(90deg, rgba(255,255,255,0.3), rgba(255,255,255,0.1));
  animation: progress linear forwards;
  width: 100%;
}

@keyframes progress {
  from { width: 100%; }
  to { width: 0%; }
}

// Transitions
.notification-enter-active {
  animation: slideIn 0.3s ease;
}

.notification-leave-active {
  animation: slideOut 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(100px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideOut {
  from {
    opacity: 1;
    transform: translateX(0);
  }
  to {
    opacity: 0;
    transform: translateX(100px);
  }
}
</style>
