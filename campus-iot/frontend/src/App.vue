<template>
  <v-app>
    <!-- Login/Register pages (no nav) -->
    <template v-if="currentRoute?.meta?.hideNav">
      <v-main>
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </v-main>
    </template>

    <!-- Main app with navigation -->
    <template v-else>
      <!-- Navigation Drawer -->
      <v-navigation-drawer
        v-model="drawer"
        :rail="rail"
        permanent
        class="bg-surface"
      >
        <v-list-item
          nav
          class="pa-4"
        >
          <template v-slot:prepend>
            <v-avatar color="primary" size="40">
              <v-icon>mdi-home-automation</v-icon>
            </v-avatar>
          </template>
          <v-list-item-title class="text-h6 font-weight-bold">
            Campus IoT
          </v-list-item-title>
          <v-list-item-subtitle>CESI Nancy</v-list-item-subtitle>
        </v-list-item>

        <v-divider class="my-2"></v-divider>

        <v-list nav density="comfortable">
          <v-list-item
            v-for="route in navRoutes"
            :key="route.path"
            :to="route.path"
            :prepend-icon="route.meta.icon"
            :title="route.meta.title"
            rounded="lg"
            class="mb-1"
          >
            <template v-slot:append v-if="route.name === 'Alerts' && alertCount > 0">
              <v-badge
                :content="alertCount"
                color="error"
                inline
              ></v-badge>
            </template>
            <template v-slot:append v-if="route.meta.requiresAdmin">
              <v-icon size="14" color="error">mdi-shield-crown</v-icon>
            </template>
          </v-list-item>
        </v-list>

        <template v-slot:append>
          <v-divider></v-divider>
          
          <!-- User info -->
          <v-list nav v-if="user">
            <v-list-item 
              :class="rail ? 'px-0 py-3 justify-center' : 'px-4 py-3'"
              @click="router.push('/profile')"
              style="cursor: pointer"
            >
              <template v-slot:prepend>
                <v-avatar 
                  :color="user.avatar_color || (isAdmin ? 'error' : 'primary')" 
                  size="36"
                  :class="rail ? 'mx-auto' : ''"
                >
                  <span class="text-body-2 font-weight-bold text-white">{{ userInitials }}</span>
                </v-avatar>
              </template>
              <v-list-item-title v-if="!rail" class="text-body-2 font-weight-medium">
                {{ user.first_name }} {{ user.last_name }}
              </v-list-item-title>
              <v-list-item-subtitle v-if="!rail" class="text-caption">
                <v-icon size="12" class="mr-1">{{ user.role_info?.icon || 'mdi-account' }}</v-icon>
                {{ user.role_info?.name || 'Utilisateur' }}
              </v-list-item-subtitle>
              <template v-slot:append v-if="!rail">
                <v-icon size="16" class="text-medium-emphasis">mdi-chevron-right</v-icon>
              </template>
            </v-list-item>
          </v-list>
          
          <v-list nav>
            <v-list-item
              @click="toggleTheme"
              :prepend-icon="isDark ? 'mdi-weather-sunny' : 'mdi-weather-night'"
              :title="isDark ? 'Mode clair' : 'Mode sombre'"
              rounded="lg"
            ></v-list-item>
            <v-list-item
              @click="rail = !rail"
              :prepend-icon="rail ? 'mdi-chevron-right' : 'mdi-chevron-left'"
              :title="rail ? 'Étendre' : 'Réduire'"
              rounded="lg"
            ></v-list-item>
            <v-list-item
              @click="logout"
              prepend-icon="mdi-logout"
              title="Déconnexion"
              rounded="lg"
              color="error"
            ></v-list-item>
          </v-list>
        </template>
      </v-navigation-drawer>

      <!-- App Bar -->
      <v-app-bar flat class="bg-surface border-b">
        <v-app-bar-title>
          <span class="text-h6">{{ currentRoute?.meta?.title || 'Dashboard' }}</span>
        </v-app-bar-title>

        <template v-slot:append>
          <!-- Connection Status -->
          <v-chip
            :color="wsConnected ? 'success' : 'error'"
            variant="tonal"
            size="small"
            class="mr-2"
          >
            <v-icon start size="small">
              {{ wsConnected ? 'mdi-wifi' : 'mdi-wifi-off' }}
            </v-icon>
            {{ wsConnected ? 'Connecté' : 'Déconnecté' }}
          </v-chip>

          <!-- Last Update -->
          <v-chip
            v-if="lastUpdate"
            variant="tonal"
            size="small"
            class="mr-4"
          >
            <v-icon start size="small">mdi-clock-outline</v-icon>
            {{ formatTime(lastUpdate) }}
          </v-chip>

          <!-- Notifications -->
          <v-btn icon variant="text" class="mr-2">
            <v-badge
              :content="alertCount"
              :model-value="alertCount > 0"
              color="error"
              :class="{ 'notification-badge': alertCount > 0 }"
            >
              <v-icon :class="{ 'bell-ring': alertCount > 0 }">mdi-bell-outline</v-icon>
            </v-badge>
          </v-btn>
        </template>
      </v-app-bar>

      <!-- Main Content -->
      <v-main class="bg-background">
        <v-container fluid class="pa-6">
          <v-alert
            v-if="!isOnline"
            type="warning"
            variant="tonal"
            class="mb-6"
            border="start"
          >
            Mode hors‑ligne activé — affichage des données mises en cache.
          </v-alert>
          <router-view v-slot="{ Component }">
            <transition name="page" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </v-container>
      </v-main>

      <!-- Notification Center -->
      <NotificationCenter />
    </template>
  </v-app>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTheme } from 'vuetify'
import { getNavRoutes } from '@/router'
import { useSensorsStore } from '@/stores/sensors'
import { useAlertsStore } from '@/stores/alerts'
import { useAuthStore } from '@/stores/auth'
import { useBuildingStore } from '@/stores/building'
import { useSettingsStore } from '@/stores/settings'
import { useWebSocket } from '@/composables/useWebSocket'
import { useNotifications } from '@/composables/useNotifications'
import { storeToRefs } from 'pinia'
import NotificationCenter from '@/components/NotificationCenter.vue'

// Theme - with localStorage persistence
const theme = useTheme()
const isDark = computed(() => theme.global.current.value.dark)

// Load saved theme from localStorage
const savedTheme = localStorage.getItem('campus-iot-theme')
if (savedTheme) {
  theme.global.name.value = savedTheme
}

const toggleTheme = () => {
  const newTheme = isDark.value ? 'light' : 'dark'
  theme.global.name.value = newTheme
  localStorage.setItem('campus-iot-theme', newTheme)
}

// Navigation - with localStorage persistence
const drawer = ref(true)
const savedRail = localStorage.getItem('campus-iot-rail')
const rail = ref(savedRail === 'true')

// Watch rail changes to save to localStorage
watch(rail, (newVal) => {
  localStorage.setItem('campus-iot-rail', String(newVal))
})
const route = useRoute()
const router = useRouter()
const currentRoute = computed(() => route)

// Auth
const authStore = useAuthStore()
const { user, isAdmin } = storeToRefs(authStore)

const userInitials = computed(() => {
  if (!user.value) return ''
  return `${user.value.first_name?.[0] || ''}${user.value.last_name?.[0] || ''}`.toUpperCase()
})

// Dynamic nav routes based on user role and permissions
const navRoutes = computed(() => {
  const permissions = user.value?.role_info?.permissions || []
  return getNavRoutes(user.value?.role || 'user', permissions)
})

const permissions = computed(() => user.value?.role_info?.permissions || [])
const canDashboard = computed(() => permissions.value.includes('all') || permissions.value.includes('dashboard'))
const canSensors = computed(() => permissions.value.includes('all') || permissions.value.includes('sensors'))
const canAlerts = computed(() => permissions.value.includes('all') || permissions.value.includes('alerts'))
const canBuilding = computed(() => permissions.value.includes('all') || permissions.value.includes('building'))

// Stores
const sensorsStore = useSensorsStore()
const alertsStore = useAlertsStore()
const buildingStore = useBuildingStore()
const settingsStore = useSettingsStore()
const isOnline = ref(navigator.onLine)

// WebSocket
const { connected: wsConnected, disconnect: wsDisconnect, reconnect: wsReconnect } = useWebSocket()

// Notifications
const notifications = useNotifications()

// Computed
const alertCount = computed(() => alertsStore.activeCount)
const lastUpdate = computed(() => sensorsStore.lastUpdate)

const pollTimer = ref(null)
const scheduleTick = ref(Date.now())
const energySavingEnabled = computed(() => settingsStore.energySavingEnabled.value)
const energySavingRefreshInterval = computed(() => settingsStore.energySavingRefreshInterval.value)
const energySavingRefreshIntervalNight = computed(() => settingsStore.energySavingRefreshIntervalNight.value)
const energySavingDisableLive = computed(() => settingsStore.energySavingDisableLive.value)
const energyProfile = computed(() => settingsStore.energyProfile.value)
const energyScheduleEnabled = computed(() => settingsStore.energyScheduleEnabled.value)
const energyScheduleProfile = computed(() => settingsStore.energyScheduleProfile.value)
const energyScheduleDays = computed(() => settingsStore.energyScheduleDays.value)
const energyScheduleStart = computed(() => settingsStore.energyScheduleStart.value)
const energyScheduleEnd = computed(() => settingsStore.energyScheduleEnd.value)

const effectiveProfile = computed(() => {
  scheduleTick.value
  if (energyScheduleEnabled.value && isInSchedule()) {
    return energyScheduleProfile.value || 'eco'
  }
  if (energySavingEnabled.value) {
    return energyProfile.value || 'eco'
  }
  return 'normal'
})

const effectiveEnergyEnabled = computed(() => effectiveProfile.value !== 'normal')
const effectiveDisableLive = computed(() => {
  if (effectiveProfile.value === 'normal') return false
  if (effectiveProfile.value === 'night') return true
  return energySavingDisableLive.value
})
const effectiveRefreshInterval = computed(() => {
  if (effectiveProfile.value === 'night') return Number(energySavingRefreshIntervalNight.value) || 300
  return Number(energySavingRefreshInterval.value) || 120
})

async function fetchAllData() {
  if (!authStore.isAuthenticated) return
  const tasks = [settingsStore.fetchSettings()]
  if (canDashboard.value || canSensors.value) tasks.push(sensorsStore.fetchSensors())
  if (canDashboard.value || canAlerts.value) tasks.push(alertsStore.fetchAlerts())
  if (canDashboard.value || canBuilding.value) tasks.push(buildingStore.fetchSensors())
  await Promise.all(tasks)
}

function startEcoPolling() {
  if (pollTimer.value) clearInterval(pollTimer.value)
  const interval = Math.max(30, Number(effectiveRefreshInterval.value) || 120)
  pollTimer.value = setInterval(fetchAllData, interval * 1000)
}

function stopEcoPolling() {
  if (pollTimer.value) clearInterval(pollTimer.value)
  pollTimer.value = null
}

function isInSchedule() {
  if (!energyScheduleEnabled.value) return false
  const days = Array.isArray(energyScheduleDays.value) ? energyScheduleDays.value : []
  if (days.length && !days.includes(new Date().getDay() - 1 < 0 ? 6 : new Date().getDay() - 1)) {
    // JS getDay: 0=Dim... adjust to 0=Mon
    return false
  }
  const now = new Date()
  const nowMinutes = now.getHours() * 60 + now.getMinutes()

  const [startH, startM] = String(energyScheduleStart.value || '00:00').split(':').map(Number)
  const [endH, endM] = String(energyScheduleEnd.value || '00:00').split(':').map(Number)
  const start = (startH || 0) * 60 + (startM || 0)
  const end = (endH || 0) * 60 + (endM || 0)

  if (start === end) return false
  if (start < end) return nowMinutes >= start && nowMinutes <= end
  return nowMinutes >= start || nowMinutes <= end
}

// Helpers
function formatTime(date) {
  if (!date) return ''
  return new Date(date).toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function logout() {
  authStore.logout()
  router.push('/login')
}

// Lifecycle
onMounted(async () => {
  // Initialize auth
  await authStore.initAuth()

  // Load cached data immediately (offline support)
  sensorsStore.loadCache?.()
  alertsStore.loadCache?.()
  buildingStore.loadCache?.()
  
  await fetchAllData()

  const handleOnline = async () => {
    isOnline.value = true
    await fetchAllData()
  }

  const handleOffline = () => {
    isOnline.value = false
  }

  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)

  setInterval(() => {
    scheduleTick.value = Date.now()
  }, 60000)

  if (effectiveEnergyEnabled.value) {
    if (effectiveDisableLive.value) wsDisconnect()
    startEcoPolling()
  }
})

watch([effectiveEnergyEnabled, effectiveRefreshInterval], ([enabled]) => {
  if (enabled) startEcoPolling()
  else stopEcoPolling()
})

watch([effectiveEnergyEnabled, effectiveDisableLive], ([enabled, disableLive]) => {
  if (enabled && disableLive) {
    wsDisconnect()
  } else {
    wsReconnect()
  }
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.border-b {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
</style>
