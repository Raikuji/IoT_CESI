<template>
  <v-app>
    <!-- Navigation Drawer -->
    <v-navigation-drawer
      v-model="drawer"
      :rail="rail"
      permanent
      class="bg-surface"
    >
      <v-list-item
        :prepend-avatar="rail ? undefined : undefined"
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
        <v-list-item-subtitle>CESI Cassiope</v-list-item-subtitle>
      </v-list-item>

      <v-divider class="my-2"></v-divider>

      <v-list nav density="comfortable">
        <v-list-item
          v-for="route in routes"
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
        </v-list-item>
      </v-list>

      <template v-slot:append>
        <v-divider></v-divider>
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
          >
            <v-icon>mdi-bell-outline</v-icon>
          </v-badge>
        </v-btn>
      </template>
    </v-app-bar>

    <!-- Main Content -->
    <v-main class="bg-background">
      <v-container fluid class="pa-6">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTheme } from 'vuetify'
import { routes } from '@/router'
import { useSensorsStore } from '@/stores/sensors'
import { useAlertsStore } from '@/stores/alerts'
import { useWebSocket } from '@/composables/useWebSocket'

// Theme
const theme = useTheme()
const isDark = computed(() => theme.global.current.value.dark)
const toggleTheme = () => {
  theme.global.name.value = isDark.value ? 'light' : 'dark'
}

// Navigation
const drawer = ref(true)
const rail = ref(false)
const route = useRoute()
const currentRoute = computed(() => routes.find(r => r.path === route.path))

// Stores
const sensorsStore = useSensorsStore()
const alertsStore = useAlertsStore()

// WebSocket
const { connected: wsConnected } = useWebSocket()

// Computed
const alertCount = computed(() => alertsStore.activeCount)
const lastUpdate = computed(() => sensorsStore.lastUpdate)

// Helpers
function formatTime(date) {
  if (!date) return ''
  return new Date(date).toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// Lifecycle
onMounted(async () => {
  await sensorsStore.fetchSensors()
  await alertsStore.fetchAlerts()
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
