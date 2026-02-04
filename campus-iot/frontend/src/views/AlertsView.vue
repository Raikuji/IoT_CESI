<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold mb-1">
          {{ tab === 'alerts' ? 'Alertes' : 'Règles d’alerte' }}
        </h1>
        <p class="text-body-2 text-medium-emphasis">
          {{ tab === 'alerts' ? 'Gestion des alertes et notifications' : 'Configuration fine des seuils et escalades' }}
        </p>
      </div>
      <div class="d-flex ga-2">
        <template v-if="tab === 'alerts'">
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
        </template>
        <template v-else>
          <v-btn color="primary" prepend-icon="mdi-refresh" @click="refreshRules">
            Actualiser
          </v-btn>
          <v-btn color="primary" variant="tonal" prepend-icon="mdi-plus" @click="scrollToForm">
            Nouvelle règle
          </v-btn>
        </template>
      </div>
    </div>

    <v-tabs v-model="tab" color="primary" class="mb-6">
      <v-tab value="alerts">Alertes</v-tab>
      <v-tab value="rules">Règles</v-tab>
    </v-tabs>

    <v-window v-model="tab" class="bg-transparent">
      <v-window-item value="alerts">
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
              <v-col cols="12" sm="6" md="3">
                <v-select
                  v-model="filterSeverity"
                  :items="severityOptions"
                  label="Sévérité"
                  clearable
                  hide-details
                ></v-select>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-select
                  v-model="filterStatus"
                  :items="statusOptions"
                  label="Statut"
                  clearable
                  hide-details
                ></v-select>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-select
                  v-model="filterType"
                  :items="typeOptions"
                  label="Type"
                  clearable
                  hide-details
                ></v-select>
              </v-col>
              <v-col cols="12" sm="6" md="3">
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
      </v-window-item>

      <v-window-item value="rules">
        <v-card class="mb-6" ref="ruleFormCard">
          <v-card-title class="d-flex align-center">
            <v-icon start color="primary">mdi-tune-variant</v-icon>
            <span class="font-weight-bold">
              {{ isEditing ? 'Modifier la règle' : 'Créer une règle' }}
            </span>
            <v-spacer />
            <v-chip v-if="isEditing" size="small" color="info" variant="tonal">Edition</v-chip>
          </v-card-title>
          <v-divider />
          <v-card-text>
            <v-alert v-if="ruleError" type="error" variant="tonal" class="mb-4">
              {{ ruleError }}
            </v-alert>

            <v-row>
              <v-col cols="12" md="4">
                <v-text-field v-model="ruleForm.name" label="Nom" placeholder="Ex: Température X101" />
              </v-col>
              <v-col cols="12" md="4">
                <v-select v-model="ruleForm.target" :items="targetOptions" label="Cible" />
              </v-col>
              <v-col cols="12" md="4">
                <v-switch v-model="ruleForm.is_active" label="Active" color="primary" inset />
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" md="6" v-if="ruleForm.target === 'sensor'">
                <v-select
                  v-model="ruleForm.sensor_id"
                  :items="sensorOptions"
                  label="Capteur"
                />
              </v-col>
              <v-col cols="12" md="6" v-else>
                <v-select
                  v-model="ruleForm.sensor_type"
                  :items="sensorTypeOptions"
                  label="Type de capteur"
                />
              </v-col>
              <v-col cols="12" md="6" v-if="ruleForm.target !== 'sensor'">
                <v-combobox
                  v-model="ruleForm.room_id"
                  :items="roomOptions"
                  label="Salle"
                  placeholder="Ex: X101"
                />
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" md="3">
                <v-select v-model="ruleForm.condition" :items="conditionOptions" label="Condition" />
              </v-col>
              <v-col cols="12" md="3">
                <v-text-field v-model.number="ruleForm.threshold" type="number" label="Seuil" />
              </v-col>
              <v-col cols="12" md="3">
                <v-select v-model="ruleForm.severity" :items="severityOptions" label="Sévérité" />
              </v-col>
              <v-col cols="12" md="3">
                <v-text-field v-model.number="ruleForm.cooldown_minutes" type="number" label="Cooldown (min)" />
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" md="6">
                <v-text-field v-model="ruleForm.message" label="Message personnalisé" />
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="ruleForm.active_days"
                  :items="dayOptions"
                  label="Jours actifs"
                  multiple
                  clearable
                />
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" md="6">
                <v-text-field v-model="ruleForm.time_start" type="time" label="Début (HH:MM)" />
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field v-model="ruleForm.time_end" type="time" label="Fin (HH:MM)" />
              </v-col>
            </v-row>

            <v-row>
              <v-col cols="12" md="4">
                <v-switch v-model="ruleForm.escalation_enabled" label="Escalade" color="warning" inset />
              </v-col>
              <v-col cols="12" md="4" v-if="ruleForm.escalation_enabled">
                <v-text-field v-model.number="ruleForm.escalation_minutes" type="number" label="Après (min)" />
              </v-col>
              <v-col cols="12" md="4" v-if="ruleForm.escalation_enabled">
                <v-select v-model="ruleForm.escalation_severity" :items="severityOptions" label="Sévérité d’escalade" />
              </v-col>
            </v-row>
          </v-card-text>
          <v-card-actions class="justify-end">
            <v-btn v-if="isEditing" variant="text" @click="resetForm">Annuler</v-btn>
            <v-btn color="primary" :loading="ruleSaving" @click="submitRule">
              {{ isEditing ? 'Mettre à jour' : 'Créer' }}
            </v-btn>
          </v-card-actions>
        </v-card>

        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon start color="primary">mdi-format-list-bulleted</v-icon>
            <span class="font-weight-bold">Règles existantes</span>
          </v-card-title>
          <v-divider />
          <v-data-table
            :headers="ruleHeaders"
            :items="rules"
            :loading="rulesLoading"
            class="bg-transparent"
          >
            <template v-slot:item.target="{ item }">
              <span class="text-body-2">{{ formatRuleTarget(item) }}</span>
            </template>
            <template v-slot:item.condition="{ item }">
              <span class="text-body-2">{{ item.condition }} {{ item.threshold }}</span>
            </template>
            <template v-slot:item.severity="{ item }">
              <v-chip :color="getSeverityColor(item.severity)" size="small" variant="tonal">
                {{ item.severity }}
              </v-chip>
            </template>
            <template v-slot:item.schedule="{ item }">
              <span class="text-body-2">{{ formatSchedule(item) }}</span>
            </template>
            <template v-slot:item.escalation="{ item }">
              <span class="text-body-2">{{ formatEscalation(item) }}</span>
            </template>
            <template v-slot:item.is_active="{ item }">
              <v-switch
                v-model="item.is_active"
                density="compact"
                hide-details
                @update:modelValue="toggleRule(item)"
              />
            </template>
            <template v-slot:item.actions="{ item }">
              <v-btn icon variant="text" size="small" @click="editRule(item)">
                <v-icon>mdi-pencil</v-icon>
                <v-tooltip activator="parent">Modifier</v-tooltip>
              </v-btn>
              <v-btn icon variant="text" size="small" color="error" @click="removeRule(item)">
                <v-icon>mdi-delete</v-icon>
                <v-tooltip activator="parent">Supprimer</v-tooltip>
              </v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useAlertsStore } from '@/stores/alerts'
import { useSensorsStore } from '@/stores/sensors'

const alertsStore = useAlertsStore()
const sensorsStore = useSensorsStore()

const { alerts, loading, alertsByPriority, activeCount, rules } = storeToRefs(alertsStore)
const { sensors } = storeToRefs(sensorsStore)

const tab = ref('alerts')
const search = ref('')
const filterSeverity = ref(null)
const filterStatus = ref(null)
const filterType = ref(null)

const ruleSaving = ref(false)
const ruleError = ref('')
const isEditing = ref(false)
const editingRuleId = ref(null)
const ruleFormCard = ref(null)

const ruleForm = ref({
  name: '',
  target: 'sensor',
  sensor_id: null,
  sensor_type: null,
  room_id: '',
  condition: '>',
  threshold: null,
  severity: 'warning',
  message: '',
  is_active: true,
  active_days: [],
  time_start: '',
  time_end: '',
  cooldown_minutes: 5,
  escalation_enabled: false,
  escalation_minutes: 15,
  escalation_severity: 'danger'
})

const headers = [
  { title: 'Sévérité', key: 'severity', width: '120px' },
  { title: 'Message', key: 'message' },
  { title: 'Date', key: 'created_at', width: '180px' },
  { title: 'Statut', key: 'is_acknowledged', width: '120px' },
  { title: 'Actions', key: 'actions', width: '80px', sortable: false }
]

const ruleHeaders = [
  { title: 'Nom', key: 'name' },
  { title: 'Cible', key: 'target' },
  { title: 'Condition', key: 'condition' },
  { title: 'Sévérité', key: 'severity' },
  { title: 'Horaires', key: 'schedule' },
  { title: 'Escalade', key: 'escalation' },
  { title: 'Active', key: 'is_active', width: '100px' },
  { title: 'Actions', key: 'actions', width: '120px', sortable: false }
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

const typeOptions = [
  { title: 'Seuils', value: 'threshold' },
  { title: 'Anomalies', value: 'anomaly' }
]

const conditionOptions = ['>', '>=', '<', '<=', '==', '!=']

const targetOptions = [
  { title: 'Capteur', value: 'sensor' },
  { title: 'Type + Salle', value: 'room' },
  { title: 'Type (global)', value: 'type' }
]

const dayOptions = [
  { title: 'Lun', value: 0 },
  { title: 'Mar', value: 1 },
  { title: 'Mer', value: 2 },
  { title: 'Jeu', value: 3 },
  { title: 'Ven', value: 4 },
  { title: 'Sam', value: 5 },
  { title: 'Dim', value: 6 }
]

const sensorOptions = computed(() => sensors.value.map(s => ({
  title: `${s.name} (${s.type}${s.location ? ' • ' + s.location : ''})`,
  value: s.id
})))

const sensorTypeOptions = computed(() => {
  const types = new Set(sensors.value.map(s => s.type).filter(Boolean))
  return Array.from(types).sort().map(t => ({ title: t, value: t }))
})

const roomOptions = computed(() => {
  const rooms = new Set(sensors.value.map(s => s.location).filter(Boolean))
  return Array.from(rooms).sort()
})

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

  if (filterType.value === 'anomaly') {
    result = result.filter(a => String(a.type || '').startsWith('anomaly_'))
  }

  if (filterType.value === 'threshold') {
    result = result.filter(a => !String(a.type || '').startsWith('anomaly_'))
  }

  return result
})

const rulesLoading = computed(() => false)

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

function formatRuleTarget(rule) {
  if (rule.sensor_id) return `Capteur #${rule.sensor_id}`
  if (rule.room_id) return `${rule.sensor_type || 'Capteur'} • ${rule.room_id}`
  return rule.sensor_type || 'Global'
}

function formatSchedule(rule) {
  const days = Array.isArray(rule.active_days) && rule.active_days.length
    ? rule.active_days.map(d => dayOptions.find(o => o.value === d)?.title).filter(Boolean).join(', ')
    : 'Tous les jours'
  const time = rule.active_time_start && rule.active_time_end
    ? `${rule.active_time_start}–${rule.active_time_end}`
    : '24/7'
  return `${days} • ${time}`
}

function formatEscalation(rule) {
  if (!rule.escalation_minutes || !rule.escalation_severity) return '—'
  return `${rule.escalation_minutes} min → ${rule.escalation_severity}`
}

function buildRulePayload() {
  const payload = {
    name: ruleForm.value.name || null,
    condition: ruleForm.value.condition,
    threshold: ruleForm.value.threshold,
    severity: ruleForm.value.severity,
    message: ruleForm.value.message || null,
    is_active: ruleForm.value.is_active,
    active_days: ruleForm.value.active_days?.length ? ruleForm.value.active_days : null,
    active_time_start: ruleForm.value.time_start || null,
    active_time_end: ruleForm.value.time_end || null,
    cooldown_minutes: ruleForm.value.cooldown_minutes ?? 5
  }

  if (ruleForm.value.target === 'sensor') {
    payload.sensor_id = ruleForm.value.sensor_id
  } else if (ruleForm.value.target === 'room') {
    payload.sensor_type = ruleForm.value.sensor_type
    payload.room_id = ruleForm.value.room_id || null
  } else {
    payload.sensor_type = ruleForm.value.sensor_type
  }

  if (ruleForm.value.escalation_enabled) {
    payload.escalation_minutes = ruleForm.value.escalation_minutes
    payload.escalation_severity = ruleForm.value.escalation_severity
  }

  return payload
}

function resetForm() {
  ruleForm.value = {
    name: '',
    target: 'sensor',
    sensor_id: null,
    sensor_type: null,
    room_id: '',
    condition: '>',
    threshold: null,
    severity: 'warning',
    message: '',
    is_active: true,
    active_days: [],
    time_start: '',
    time_end: '',
    cooldown_minutes: 5,
    escalation_enabled: false,
    escalation_minutes: 15,
    escalation_severity: 'danger'
  }
  ruleError.value = ''
  isEditing.value = false
  editingRuleId.value = null
}

async function submitRule() {
  ruleSaving.value = true
  ruleError.value = ''
  const payload = buildRulePayload()

  const result = isEditing.value
    ? await alertsStore.updateRule(editingRuleId.value, payload)
    : await alertsStore.createRule(payload)

  ruleSaving.value = false

  if (!result.success) {
    ruleError.value = result.error || 'Erreur lors de la sauvegarde'
    return
  }

  resetForm()
}

function editRule(rule) {
  isEditing.value = true
  editingRuleId.value = rule.id

  ruleForm.value = {
    name: rule.name || '',
    target: rule.sensor_id ? 'sensor' : rule.room_id ? 'room' : 'type',
    sensor_id: rule.sensor_id || null,
    sensor_type: rule.sensor_type || null,
    room_id: rule.room_id || '',
    condition: rule.condition,
    threshold: rule.threshold,
    severity: rule.severity,
    message: rule.message || '',
    is_active: rule.is_active,
    active_days: rule.active_days || [],
    time_start: rule.active_time_start || '',
    time_end: rule.active_time_end || '',
    cooldown_minutes: rule.cooldown_minutes ?? 5,
    escalation_enabled: !!rule.escalation_minutes,
    escalation_minutes: rule.escalation_minutes || 15,
    escalation_severity: rule.escalation_severity || 'danger'
  }

  scrollToForm()
}

async function removeRule(rule) {
  await alertsStore.deleteRule(rule.id)
}

async function toggleRule(rule) {
  await alertsStore.updateRule(rule.id, { is_active: rule.is_active })
}

function scrollToForm() {
  if (ruleFormCard.value?.$el) {
    ruleFormCard.value.$el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
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

function refreshRules() {
  alertsStore.fetchRules()
}

onMounted(() => {
  alertsStore.fetchAlerts()
  alertsStore.fetchRules()
  sensorsStore.fetchSensors()
})
</script>
