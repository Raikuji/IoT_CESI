<template>
  <div class="activity-view">
    <!-- Header -->
    <div class="activity-hero mb-8">
      <div class="hero-content">
        <div class="hero-icon">
          <v-icon size="48" color="white">mdi-history</v-icon>
        </div>
        <div class="hero-text">
          <h1 class="text-h3 font-weight-black mb-2">Journal d'activité</h1>
          <p class="text-body-1 opacity-80">
            Historique de toutes les actions effectuées sur le système
          </p>
        </div>
      </div>
      <div class="hero-actions">
        <v-btn
          variant="outlined"
          color="white"
          @click="exportLogs"
          :loading="exporting"
        >
          <v-icon start>mdi-download</v-icon>
          Exporter
        </v-btn>
        <v-btn
          variant="flat"
          color="white"
          class="text-primary"
          @click="fetchLogs"
          :loading="loading"
        >
          <v-icon start>mdi-refresh</v-icon>
          Actualiser
        </v-btn>
      </div>
      <div class="hero-decoration"></div>
    </div>

    <v-row>
      <!-- Filters -->
      <v-col cols="12" lg="3">
        <v-card class="filters-card mb-6">
          <v-card-title class="d-flex align-center pa-5 pb-3">
            <v-icon start color="primary">mdi-filter</v-icon>
            <span class="font-weight-bold">Filtres</span>
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-5">
            <v-text-field
              v-model="search"
              prepend-inner-icon="mdi-magnify"
              label="Rechercher"
              variant="outlined"
              density="compact"
              hide-details
              class="mb-4"
            ></v-text-field>

            <v-select
              v-model="filterAction"
              :items="actionOptions"
              label="Type d'action"
              variant="outlined"
              density="compact"
              hide-details
              clearable
              class="mb-4"
            ></v-select>

            <v-select
              v-model="filterPeriod"
              :items="periodOptions"
              label="Période"
              variant="outlined"
              density="compact"
              hide-details
            ></v-select>
          </v-card-text>
        </v-card>

        <!-- Stats -->
        <v-card class="stats-card">
          <v-card-title class="d-flex align-center pa-5 pb-3">
            <v-icon start color="info">mdi-chart-pie</v-icon>
            <span class="font-weight-bold">Statistiques</span>
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-5">
            <div class="stat-item mb-4">
              <div class="d-flex justify-space-between mb-1">
                <span class="text-body-2">Connexions</span>
                <span class="font-weight-bold">{{ getActionCount('login') }}</span>
              </div>
              <v-progress-linear
                :model-value="getActionPercentage('login')"
                color="success"
                height="6"
                rounded
              ></v-progress-linear>
            </div>

            <div class="stat-item mb-4">
              <div class="d-flex justify-space-between mb-1">
                <span class="text-body-2">Alertes</span>
                <span class="font-weight-bold">{{ getActionCount('alert_triggered') }}</span>
              </div>
              <v-progress-linear
                :model-value="getActionPercentage('alert_triggered')"
                color="warning"
                height="6"
                rounded
              ></v-progress-linear>
            </div>

            <div class="stat-item mb-4">
              <div class="d-flex justify-space-between mb-1">
                <span class="text-body-2">Commandes</span>
                <span class="font-weight-bold">{{ getActionCount('command_sent') }}</span>
              </div>
              <v-progress-linear
                :model-value="getActionPercentage('command_sent')"
                color="purple"
                height="6"
                rounded
              ></v-progress-linear>
            </div>

            <div class="stat-item">
              <div class="d-flex justify-space-between mb-1">
                <span class="text-body-2">Modifications</span>
                <span class="font-weight-bold">{{ getActionCount('user_updated') + getActionCount('settings_changed') }}</span>
              </div>
              <v-progress-linear
                :model-value="getActionPercentage('user_updated')"
                color="info"
                height="6"
                rounded
              ></v-progress-linear>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Activity Timeline -->
      <v-col cols="12" lg="9">
        <v-card class="timeline-card">
          <v-card-title class="d-flex align-center pa-5 pb-3">
            <v-icon start color="primary">mdi-timeline-clock</v-icon>
            <span class="font-weight-bold">Historique</span>
            <v-spacer />
            <v-chip variant="tonal" color="primary">
              {{ filteredLogs.length }} événements
            </v-chip>
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-0">
            <div v-if="loading" class="text-center py-12">
              <v-progress-circular indeterminate color="primary" size="48"></v-progress-circular>
              <p class="text-body-2 text-medium-emphasis mt-4">Chargement...</p>
            </div>

            <div v-else-if="filteredLogs.length === 0" class="text-center py-12 text-medium-emphasis">
              <v-icon size="64" class="mb-4">mdi-history</v-icon>
              <p class="text-body-1">Aucune activité trouvée</p>
            </div>

            <v-virtual-scroll
              v-else
              :items="filteredLogs"
              :item-height="80"
              height="600"
              class="activity-list"
            >
              <template v-slot:default="{ item }">
                <div class="activity-item" :class="item.action">
                  <div class="activity-icon" :style="{ background: item.color }">
                    <v-icon color="white" size="20">{{ item.icon }}</v-icon>
                  </div>
                  <div class="activity-content">
                    <div class="activity-title">
                      {{ item.label }}
                      <v-chip
                        v-if="item.user_name"
                        size="x-small"
                        variant="tonal"
                        class="ml-2"
                      >
                        {{ item.user_name }}
                      </v-chip>
                    </div>
                    <div class="activity-details" v-if="item.details">
                      {{ formatDetails(item.details) }}
                    </div>
                    <div class="activity-time">
                      {{ formatDateTime(item.timestamp) }}
                    </div>
                  </div>
                  <div class="activity-badge">
                    <v-chip
                      :color="getActionCategory(item.action).color"
                      size="x-small"
                      variant="flat"
                    >
                      {{ getActionCategory(item.action).label }}
                    </v-chip>
                  </div>
                </div>
              </template>
            </v-virtual-scroll>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useActivityStore } from '@/stores/activity'
import { useExport } from '@/composables/useExport'
import { storeToRefs } from 'pinia'

const activityStore = useActivityStore()
const { logs, loading } = storeToRefs(activityStore)
const { exportActivityLogs, exporting } = useExport()

const search = ref('')
const filterAction = ref(null)
const filterPeriod = ref('all')

const actionOptions = [
  { title: 'Connexion', value: 'login' },
  { title: 'Déconnexion', value: 'logout' },
  { title: 'Alerte déclenchée', value: 'alert_triggered' },
  { title: 'Alerte résolue', value: 'alert_resolved' },
  { title: 'Commande envoyée', value: 'command_sent' },
  { title: 'Utilisateur créé', value: 'user_created' },
  { title: 'Utilisateur modifié', value: 'user_updated' },
  { title: 'Rôle modifié', value: 'role_changed' },
  { title: 'Export données', value: 'export_data' }
]

const periodOptions = [
  { title: 'Tout', value: 'all' },
  { title: 'Aujourd\'hui', value: 'today' },
  { title: '7 derniers jours', value: '7d' },
  { title: '30 derniers jours', value: '30d' }
]

const actionCategories = {
  login: { color: 'success', label: 'Auth' },
  logout: { color: 'grey', label: 'Auth' },
  alert_triggered: { color: 'warning', label: 'Alerte' },
  alert_resolved: { color: 'success', label: 'Alerte' },
  command_sent: { color: 'purple', label: 'Contrôle' },
  user_created: { color: 'info', label: 'Admin' },
  user_updated: { color: 'info', label: 'Admin' },
  user_deleted: { color: 'error', label: 'Admin' },
  role_changed: { color: 'warning', label: 'Admin' },
  settings_changed: { color: 'grey', label: 'Config' },
  export_data: { color: 'info', label: 'Export' },
  sensor_add: { color: 'success', label: 'Capteur' },
  sensor_remove: { color: 'error', label: 'Capteur' }
}

const filteredLogs = computed(() => {
  let result = logs.value

  // Filter by search
  if (search.value) {
    const s = search.value.toLowerCase()
    result = result.filter(log =>
      log.label?.toLowerCase().includes(s) ||
      log.user_name?.toLowerCase().includes(s) ||
      JSON.stringify(log.details)?.toLowerCase().includes(s)
    )
  }

  // Filter by action type
  if (filterAction.value) {
    result = result.filter(log => log.action === filterAction.value)
  }

  // Filter by period
  if (filterPeriod.value !== 'all') {
    const now = new Date()
    let cutoff = new Date()
    
    if (filterPeriod.value === 'today') {
      cutoff.setHours(0, 0, 0, 0)
    } else if (filterPeriod.value === '7d') {
      cutoff.setDate(now.getDate() - 7)
    } else if (filterPeriod.value === '30d') {
      cutoff.setDate(now.getDate() - 30)
    }

    result = result.filter(log => new Date(log.timestamp) >= cutoff)
  }

  return result
})

function getActionCount(action) {
  return logs.value.filter(l => l.action === action).length
}

function getActionPercentage(action) {
  if (logs.value.length === 0) return 0
  return (getActionCount(action) / logs.value.length) * 100
}

function getActionCategory(action) {
  return actionCategories[action] || { color: 'grey', label: 'Autre' }
}

function formatDateTime(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('fr-FR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatDetails(details) {
  if (!details) return ''
  if (typeof details === 'string') {
    try {
      details = JSON.parse(details)
    } catch {
      return details
    }
  }
  return Object.entries(details)
    .map(([k, v]) => `${k}: ${v}`)
    .join(' • ')
}

async function fetchLogs() {
  await activityStore.fetchLogs(100)
}

function exportLogs() {
  exportActivityLogs(filteredLogs.value)
  activityStore.addLog('export_data', { type: 'activity_logs', count: filteredLogs.value.length })
}

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped lang="scss">
.activity-view {
  max-width: 1400px;
  margin: 0 auto;
}

.activity-hero {
  position: relative;
  background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 50%, #5b21b6 100%);
  border-radius: 24px;
  padding: 48px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.hero-content {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 24px;
}

.hero-icon {
  width: 96px;
  height: 96px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.hero-text {
  color: white;
}

.hero-actions {
  position: relative;
  z-index: 2;
  display: flex;
  gap: 12px;
}

.hero-decoration {
  position: absolute;
  top: -50%;
  right: -10%;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
  border-radius: 50%;
}

.filters-card, .stats-card, .timeline-card {
  border-radius: 16px;
}

.activity-list {
  .activity-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px 24px;
    border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.05);
    transition: background 0.2s ease;

    &:hover {
      background: rgba(var(--v-theme-primary), 0.03);
    }
  }
}

.activity-icon {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.activity-content {
  flex: 1;
  min-width: 0;
}

.activity-title {
  font-weight: 600;
  font-size: 0.9375rem;
  display: flex;
  align-items: center;
}

.activity-details {
  font-size: 0.8125rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.activity-time {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.4);
  margin-top: 4px;
}

.activity-badge {
  flex-shrink: 0;
}

.stat-item {
  .text-body-2 {
    color: rgba(var(--v-theme-on-surface), 0.7);
  }
}
</style>
