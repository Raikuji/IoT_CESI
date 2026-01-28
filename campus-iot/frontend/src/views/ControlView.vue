<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold mb-1">Contrôle</h1>
        <p class="text-body-2 text-medium-emphasis">
          Pilotage des actionneurs
        </p>
      </div>
      <v-chip v-if="lastSyncTime" color="success" variant="tonal" size="small">
        <v-icon start size="14">mdi-sync</v-icon>
        Sync: {{ lastSyncTime }}
      </v-chip>
    </div>

    <v-row>
      <!-- Heating Control -->
      <v-col cols="12" lg="6">
        <v-card class="gradient-border" color="surface">
          <v-card-title class="d-flex align-center">
            <v-avatar color="error" variant="tonal" size="40" class="mr-3">
              <v-icon>mdi-radiator</v-icon>
            </v-avatar>
            Chauffage
            <v-spacer></v-spacer>
            <v-chip :color="heatingMode === 'auto' ? 'success' : 'warning'" variant="tonal">
              {{ heatingMode === 'auto' ? 'Automatique' : 'Manuel' }}
            </v-chip>
          </v-card-title>
          
          <v-card-text class="pa-6">
            <!-- Mode Toggle -->
            <div class="d-flex align-center justify-center mb-6">
              <v-btn-toggle v-model="heatingMode" mandatory color="primary" @update:model-value="saveHeatingMode">
                <v-btn value="manual" prepend-icon="mdi-hand-back-left">
                  Manuel
                </v-btn>
                <v-btn value="auto" prepend-icon="mdi-robot">
                  Auto
                </v-btn>
              </v-btn-toggle>
            </div>

            <!-- Manual Control -->
            <div v-if="heatingMode === 'manual'" class="text-center">
              <div class="mb-4">
                <span class="text-h2 font-weight-bold text-primary">{{ heatingValue }}</span>
                <span class="text-h5 text-medium-emphasis">%</span>
              </div>
              
              <v-slider
                v-model="heatingValue"
                :min="0"
                :max="100"
                :step="5"
                color="primary"
                track-color="grey-darken-3"
                thumb-label
                class="mx-4"
              >
                <template v-slot:prepend>
                  <v-icon color="info">mdi-snowflake</v-icon>
                </template>
                <template v-slot:append>
                  <v-icon color="error">mdi-fire</v-icon>
                </template>
              </v-slider>

              <v-btn
                color="primary"
                size="large"
                class="mt-4"
                @click="sendHeatingCommand"
                :loading="sendingCommand"
              >
                <v-icon start>mdi-send</v-icon>
                Appliquer
              </v-btn>
            </div>

            <!-- Auto Control -->
            <div v-else class="text-center">
              <div class="mb-4">
                <div class="text-body-1 text-medium-emphasis mb-2">Température cible</div>
                <div class="d-flex align-center justify-center ga-4">
                  <v-btn icon variant="tonal" @click="setpoint--; saveSetpoint()">
                    <v-icon>mdi-minus</v-icon>
                  </v-btn>
                  <span class="text-h2 font-weight-bold">{{ setpoint }}</span>
                  <span class="text-h5 text-medium-emphasis">°C</span>
                  <v-btn icon variant="tonal" @click="setpoint++; saveSetpoint()">
                    <v-icon>mdi-plus</v-icon>
                  </v-btn>
                </div>
              </div>

              <v-alert type="info" variant="tonal" class="mt-4">
                <v-icon start>mdi-robot</v-icon>
                Le chauffage s'ajustera automatiquement pour atteindre {{ setpoint }}°C
              </v-alert>

              <v-btn
                color="primary"
                size="large"
                class="mt-4"
                @click="sendSetpoint"
                :loading="sendingCommand"
              >
                <v-icon start>mdi-check</v-icon>
                Valider
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Current Status -->
      <v-col cols="12" lg="6">
        <v-card color="surface" class="h-100">
          <v-card-title class="d-flex align-center">
            <v-icon start>mdi-information-outline</v-icon>
            État actuel
          </v-card-title>
          
          <v-card-text>
            <v-list bg-color="transparent">
              <v-list-item>
                <template v-slot:prepend>
                  <v-avatar color="error" variant="tonal">
                    <v-icon>mdi-thermometer</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title>Température actuelle</v-list-item-title>
                <template v-slot:append>
                  <span class="text-h5 font-weight-bold">{{ currentTemp }}°C</span>
                </template>
              </v-list-item>

              <v-list-item>
                <template v-slot:prepend>
                  <v-avatar color="warning" variant="tonal">
                    <v-icon>mdi-radiator</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title>Position vanne</v-list-item-title>
                <template v-slot:append>
                  <span class="text-h5 font-weight-bold">{{ heatingValue }}%</span>
                </template>
              </v-list-item>

              <v-list-item>
                <template v-slot:prepend>
                  <v-avatar color="success" variant="tonal">
                    <v-icon>mdi-target</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title>Consigne</v-list-item-title>
                <template v-slot:append>
                  <span class="text-h5 font-weight-bold">{{ setpoint }}°C</span>
                </template>
              </v-list-item>

              <v-list-item>
                <template v-slot:prepend>
                  <v-avatar color="info" variant="tonal">
                    <v-icon>mdi-clock-outline</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title>Dernière commande</v-list-item-title>
                <template v-slot:append>
                  <span class="text-body-1">{{ lastCommandTime }}</span>
                </template>
              </v-list-item>
            </v-list>

            <!-- Visual Indicator -->
            <div class="mt-6 pa-4 rounded-lg" :style="{ background: getHeatGradient }">
              <div class="d-flex align-center justify-center">
                <v-icon size="64" :color="heatingValue > 50 ? 'error' : 'info'">
                  {{ heatingValue > 50 ? 'mdi-fire' : 'mdi-snowflake' }}
                </v-icon>
              </div>
              <div class="text-center mt-2 text-body-2">
                {{ heatingValue > 70 ? 'Chauffage fort' : heatingValue > 30 ? 'Chauffage modéré' : 'Chauffage faible' }}
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Command History -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card color="surface">
          <v-card-title>
            <v-icon start>mdi-history</v-icon>
            Historique des commandes
          </v-card-title>
          <v-card-text>
            <v-timeline v-if="commandHistory.length" side="end" density="compact">
              <v-timeline-item
                v-for="cmd in commandHistory"
                :key="cmd.id"
                :dot-color="cmd.source === 'auto' ? 'success' : 'warning'"
                size="small"
              >
                <template v-slot:opposite>
                  <span class="text-body-2 text-medium-emphasis">
                    {{ formatTime(cmd.created_at) }}
                  </span>
                </template>
                <div>
                  <strong>{{ cmd.command_value }}%</strong>
                  <v-chip size="x-small" class="ml-2" variant="tonal">
                    {{ cmd.source }}
                  </v-chip>
                </div>
              </v-timeline-item>
            </v-timeline>
            <div v-else class="text-center text-medium-emphasis pa-4">
              Aucune commande enregistrée
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useSensorsStore } from '@/stores/sensors'
import { useSettingsStore } from '@/stores/settings'
import { useWebSocket } from '@/composables/useWebSocket'
import axios from 'axios'

const sensorsStore = useSensorsStore()
const settingsStore = useSettingsStore()
const { temperature } = storeToRefs(sensorsStore)
const { onMessage } = useWebSocket()

const heatingMode = ref('manual')
const heatingValue = ref(45)
const setpoint = ref(21)
const sendingCommand = ref(false)
const commandHistory = ref([])
const lastSyncTime = ref(null)

const currentTemp = computed(() => {
  return temperature.value?.latest_value?.toFixed(1) || '--'
})

const lastCommandTime = computed(() => {
  if (!commandHistory.value.length) return '--'
  return formatTime(commandHistory.value[0].created_at)
})

const getHeatGradient = computed(() => {
  const intensity = heatingValue.value / 100
  return `linear-gradient(135deg, 
    rgba(0, 212, 255, ${0.2 * (1 - intensity)}) 0%, 
    rgba(255, 107, 107, ${0.3 * intensity}) 100%)`
})

function formatTime(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Load saved settings from backend
async function loadSettings() {
  try {
    const response = await axios.get('/api/settings/')
    const settings = response.data
    
    // Find heating settings
    const modeSet = settings.find(s => s.key === 'heating_mode')
    const valueSet = settings.find(s => s.key === 'heating_value')
    const setpointSet = settings.find(s => s.key === 'heating_setpoint')
    
    if (modeSet) heatingMode.value = modeSet.value
    if (valueSet) heatingValue.value = parseInt(valueSet.value) || 45
    if (setpointSet) setpoint.value = parseInt(setpointSet.value) || 21
    
    lastSyncTime.value = formatTime(new Date().toISOString())
  } catch (e) {
    console.error('Failed to load settings:', e)
  }
}

// Save heating mode
async function saveHeatingMode() {
  try {
    await axios.put('/api/settings/heating_mode', {
      value: heatingMode.value
    })
    broadcastChange('heating_mode', heatingMode.value)
  } catch (e) {
    console.error('Failed to save heating mode:', e)
  }
}

// Save setpoint
async function saveSetpoint() {
  try {
    await axios.put('/api/settings/heating_setpoint', {
      value: String(setpoint.value)
    })
    broadcastChange('heating_setpoint', setpoint.value)
  } catch (e) {
    console.error('Failed to save setpoint:', e)
  }
}

// Broadcast change via WebSocket
function broadcastChange(key, value) {
  // The backend will broadcast via WebSocket when settings change
  lastSyncTime.value = formatTime(new Date().toISOString())
}

async function sendHeatingCommand() {
  sendingCommand.value = true
  try {
    // Save the value in settings
    await axios.put('/api/settings/heating_value', {
      value: String(heatingValue.value)
    })
    
    // Try to send command to actuator if one exists
    try {
      const actuators = await axios.get('/api/actuators/')
      if (actuators.data.length > 0) {
        await axios.post(`/api/actuators/${actuators.data[0].id}/command`, {
          value: heatingValue.value,
          source: 'manual'
        })
        await fetchCommandHistory()
      }
    } catch (actuatorError) {
      // No actuator configured - settings are still saved
      console.log('No actuator configured, settings saved')
    }
    
    broadcastChange('heating_value', heatingValue.value)
  } catch (e) {
    console.error('Failed to send command:', e)
  } finally {
    sendingCommand.value = false
  }
}

async function sendSetpoint() {
  sendingCommand.value = true
  try {
    await saveSetpoint()
    
    await axios.post('/api/actuators/heating/mode', {
      mode: 'auto',
      setpoint: setpoint.value
    })
  } catch (e) {
    console.error('Failed to send setpoint:', e)
  } finally {
    sendingCommand.value = false
  }
}

async function fetchCommandHistory() {
  try {
    // First check if actuator exists
    const actuators = await axios.get('/api/actuators/')
    if (actuators.data.length === 0) {
      // No actuators yet - that's fine, just show empty history
      commandHistory.value = []
      return
    }
    
    // Get commands from first actuator
    const actuatorId = actuators.data[0].id
    const response = await axios.get(`/api/actuators/${actuatorId}/commands`, {
      params: { limit: 10 }
    })
    commandHistory.value = response.data
  } catch (e) {
    // Silently handle - no actuators configured yet
    commandHistory.value = []
  }
}

// Handle WebSocket messages for real-time sync
function handleWebSocketMessage(data) {
  if (data.type === 'system_setting_updated') {
    const { key, value } = data
    
    if (key === 'heating_mode') {
      heatingMode.value = value
    } else if (key === 'heating_value') {
      heatingValue.value = parseInt(value) || 45
    } else if (key === 'heating_setpoint') {
      setpoint.value = parseInt(value) || 21
    }
    
    lastSyncTime.value = formatTime(new Date().toISOString())
  } else if (data.type === 'actuator_command') {
    // Refresh command history when new command arrives
    fetchCommandHistory()
  }
}

// Subscribe to WebSocket messages
let unsubscribe = null

onMounted(() => {
  loadSettings()
  fetchCommandHistory()
  
  // Listen for WebSocket updates
  unsubscribe = onMessage(handleWebSocketMessage)
})

onUnmounted(() => {
  if (unsubscribe) {
    unsubscribe()
  }
})
</script>
