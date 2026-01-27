<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold mb-1">Alertes</h1>
        <p class="text-body-2 text-medium-emphasis">
          Gestion des alertes et notifications
        </p>
      </div>
      <div class="d-flex ga-2">
        <v-btn
          v-if="activeCount > 0"
          color="warning"
          variant="tonal"
          prepend-icon="mdi-check-all"
          @click="acknowledgeAll"
        >
          Tout acquitter
        </v-btn>
        <v-btn color="primary" prepend-icon="mdi-refresh" @click="refresh">
          Actualiser
        </v-btn>
      </div>
    </div>

    <!-- Stats Cards -->
    <v-row class="mb-6">
      <v-col cols="12" sm="4">
        <v-card color="error" variant="tonal">
          <v-card-text class="d-flex align-center">
            <v-avatar color="error" size="48" class="mr-4">
              <v-icon>mdi-alert-circle</v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">{{ dangerCount }}</div>
              <div class="text-body-2">Critiques</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="4">
        <v-card color="warning" variant="tonal">
          <v-card-text class="d-flex align-center">
            <v-avatar color="warning" size="48" class="mr-4">
              <v-icon>mdi-alert</v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">{{ warningCount }}</div>
              <div class="text-body-2">Avertissements</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="4">
        <v-card color="info" variant="tonal">
          <v-card-text class="d-flex align-center">
            <v-avatar color="info" size="48" class="mr-4">
              <v-icon>mdi-information</v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">{{ infoCount }}</div>
              <div class="text-body-2">Informations</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Filters -->
    <v-card color="surface" class="mb-6">
      <v-card-text>
        <v-row align="center">
          <v-col cols="12" sm="4">
            <v-select
              v-model="filterSeverity"
              :items="severityOptions"
              label="Sévérité"
              clearable
              hide-details
            ></v-select>
          </v-col>
          <v-col cols="12" sm="4">
            <v-select
              v-model="filterStatus"
              :items="statusOptions"
              label="Statut"
              clearable
              hide-details
            ></v-select>
          </v-col>
          <v-col cols="12" sm="4">
            <v-text-field
              v-model="search"
              prepend-inner-icon="mdi-magnify"
              label="Rechercher"
              clearable
              hide-details
            ></v-text-field>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Alerts List -->
    <v-card color="surface">
      <v-data-table
        :headers="headers"
        :items="filteredAlerts"
        :search="search"
        :loading="loading"
        class="bg-transparent"
      >
        <template v-slot:item.severity="{ item }">
          <v-chip :color="getSeverityColor(item.severity)" size="small" variant="tonal">
            <v-icon start size="small">{{ getSeverityIcon(item.severity) }}</v-icon>
            {{ item.severity }}
          </v-chip>
        </template>

        <template v-slot:item.message="{ item }">
          <div class="py-2">
            <div class="font-weight-medium">{{ item.message }}</div>
            <div class="text-body-2 text-medium-emphasis">{{ item.type }}</div>
          </div>
        </template>

        <template v-slot:item.created_at="{ item }">
          {{ formatDate(item.created_at) }}
        </template>

        <template v-slot:item.is_acknowledged="{ item }">
          <v-chip
            :color="item.is_acknowledged ? 'success' : 'warning'"
            size="small"
            variant="tonal"
          >
            {{ item.is_acknowledged ? 'Acquitté' : 'Actif' }}
          </v-chip>
        </template>

        <template v-slot:item.actions="{ item }">
          <v-btn
            v-if="!item.is_acknowledged"
            icon
            variant="text"
            size="small"
            color="success"
            @click="acknowledge(item.id)"
          >
            <v-icon>mdi-check</v-icon>
            <v-tooltip activator="parent">Acquitter</v-tooltip>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useAlertsStore } from '@/stores/alerts'

const alertsStore = useAlertsStore()
const { alerts, loading, alertsByPriority, activeCount } = storeToRefs(alertsStore)

const search = ref('')
const filterSeverity = ref(null)
const filterStatus = ref(null)

const headers = [
  { title: 'Sévérité', key: 'severity', width: '120px' },
  { title: 'Message', key: 'message' },
  { title: 'Date', key: 'created_at', width: '180px' },
  { title: 'Statut', key: 'is_acknowledged', width: '120px' },
  { title: 'Actions', key: 'actions', width: '80px', sortable: false }
]

const severityOptions = [
  { title: 'Critique', value: 'danger' },
  { title: 'Avertissement', value: 'warning' },
  { title: 'Information', value: 'info' }
]

const statusOptions = [
  { title: 'Actif', value: false },
  { title: 'Acquitté', value: true }
]

const dangerCount = computed(() => alertsByPriority.value.danger?.length || 0)
const warningCount = computed(() => alertsByPriority.value.warning?.length || 0)
const infoCount = computed(() => alertsByPriority.value.info?.length || 0)

const filteredAlerts = computed(() => {
  let result = alerts.value
  
  if (filterSeverity.value) {
    result = result.filter(a => a.severity === filterSeverity.value)
  }
  
  if (filterStatus.value !== null) {
    result = result.filter(a => a.is_acknowledged === filterStatus.value)
  }
  
  return result
})

function getSeverityColor(severity) {
  const colors = { danger: 'error', warning: 'warning', info: 'info' }
  return colors[severity] || 'grey'
}

function getSeverityIcon(severity) {
  const icons = {
    danger: 'mdi-alert-circle',
    warning: 'mdi-alert',
    info: 'mdi-information'
  }
  return icons[severity] || 'mdi-bell'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('fr-FR')
}

function acknowledge(id) {
  alertsStore.acknowledgeAlert(id)
}

function acknowledgeAll() {
  alertsStore.acknowledgeAll()
}

function refresh() {
  alertsStore.fetchAlerts()
}
</script>
