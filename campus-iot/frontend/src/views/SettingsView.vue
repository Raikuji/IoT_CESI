<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold mb-1">Paramètres</h1>
        <p class="text-body-2 text-medium-emphasis">
          Configuration du système
        </p>
      </div>
    </div>

    <v-row>
      <!-- Alert Rules -->
      <v-col cols="12" lg="6">
        <v-card color="surface">
          <v-card-title class="d-flex align-center">
            <v-icon start>mdi-bell-cog</v-icon>
            Règles d'alerte
            <v-spacer></v-spacer>
            <v-btn color="primary" size="small" prepend-icon="mdi-plus" @click="showAddRule = true">
              Ajouter
            </v-btn>
          </v-card-title>
          <v-card-text>
            <v-list bg-color="transparent">
              <v-list-item
                v-for="rule in alertRules"
                :key="rule.id"
                class="mb-2 rounded-lg"
                :class="{ 'opacity-50': !rule.is_active }"
              >
                <template v-slot:prepend>
                  <v-avatar :color="getSeverityColor(rule.severity)" variant="tonal">
                    <v-icon>{{ getSeverityIcon(rule.severity) }}</v-icon>
                  </v-avatar>
                </template>
                
                <v-list-item-title>{{ rule.message }}</v-list-item-title>
                <v-list-item-subtitle>
                  {{ getSensorName(rule.sensor_id) }} {{ rule.condition }} {{ rule.threshold }}
                </v-list-item-subtitle>

                <template v-slot:append>
                  <v-switch
                    v-model="rule.is_active"
                    color="primary"
                    hide-details
                    density="compact"
                    @change="toggleRule(rule)"
                  ></v-switch>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- System Info -->
      <v-col cols="12" lg="6">
        <v-card color="surface">
          <v-card-title>
            <v-icon start>mdi-information</v-icon>
            Informations système
          </v-card-title>
          <v-card-text>
            <v-list bg-color="transparent" density="compact">
              <v-list-item>
                <v-list-item-title>Version</v-list-item-title>
                <template v-slot:append>
                  <v-chip size="small" color="primary">1.0.0</v-chip>
                </template>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>Broker MQTT</v-list-item-title>
                <template v-slot:append>
                  <v-chip size="small" color="success">Connecté</v-chip>
                </template>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>Base de données</v-list-item-title>
                <template v-slot:append>
                  <v-chip size="small" color="success">PostgreSQL</v-chip>
                </template>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>Capteurs actifs</v-list-item-title>
                <template v-slot:append>
                  {{ sensors.length }}
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>

        <!-- Theme Settings -->
        <v-card color="surface" class="mt-4">
          <v-card-title>
            <v-icon start>mdi-palette</v-icon>
            Apparence
          </v-card-title>
          <v-card-text>
            <v-list bg-color="transparent">
              <v-list-item>
                <v-list-item-title>Thème sombre</v-list-item-title>
                <template v-slot:append>
                  <v-switch
                    v-model="isDark"
                    color="primary"
                    hide-details
                    @change="toggleTheme"
                  ></v-switch>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>

        <!-- About -->
        <v-card color="surface" class="mt-4">
          <v-card-text class="text-center py-6">
            <v-avatar color="primary" size="64" class="mb-4">
              <v-icon size="32">mdi-home-automation</v-icon>
            </v-avatar>
            <h3 class="text-h6 mb-2">Campus IoT</h3>
            <p class="text-body-2 text-medium-emphasis mb-4">
              Système de monitoring IoT pour le campus CESI Cassiope
            </p>
            <v-chip variant="tonal" color="secondary">
              Projet A4 - Groupe 3
            </v-chip>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Add Rule Dialog -->
    <v-dialog v-model="showAddRule" max-width="500">
      <v-card color="surface">
        <v-card-title>
          <v-icon start>mdi-plus</v-icon>
          Nouvelle règle d'alerte
        </v-card-title>
        <v-card-text>
          <v-form @submit.prevent="addRule">
            <v-select
              v-model="newRule.sensor_id"
              :items="sensorOptions"
              label="Capteur"
              required
            ></v-select>
            <v-row>
              <v-col cols="6">
                <v-select
                  v-model="newRule.condition"
                  :items="conditionOptions"
                  label="Condition"
                  required
                ></v-select>
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model.number="newRule.threshold"
                  label="Seuil"
                  type="number"
                  required
                ></v-text-field>
              </v-col>
            </v-row>
            <v-text-field
              v-model="newRule.message"
              label="Message d'alerte"
              required
            ></v-text-field>
            <v-select
              v-model="newRule.severity"
              :items="severityOptions"
              label="Sévérité"
              required
            ></v-select>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="showAddRule = false">Annuler</v-btn>
          <v-btn color="primary" @click="addRule">Ajouter</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useTheme } from 'vuetify'
import { useSensorsStore } from '@/stores/sensors'
import { useAlertsStore } from '@/stores/alerts'
import axios from 'axios'

const theme = useTheme()
const sensorsStore = useSensorsStore()
const alertsStore = useAlertsStore()

const { sensors } = storeToRefs(sensorsStore)
const { rules: alertRules } = storeToRefs(alertsStore)

const isDark = ref(theme.global.current.value.dark)
const showAddRule = ref(false)

const newRule = ref({
  sensor_id: null,
  condition: '>',
  threshold: 0,
  message: '',
  severity: 'warning'
})

const sensorOptions = computed(() => 
  sensors.value.map(s => ({ title: s.name, value: s.id }))
)

const conditionOptions = [
  { title: 'Supérieur à (>)', value: '>' },
  { title: 'Inférieur à (<)', value: '<' },
  { title: 'Égal à (==)', value: '==' },
  { title: 'Supérieur ou égal (>=)', value: '>=' },
  { title: 'Inférieur ou égal (<=)', value: '<=' }
]

const severityOptions = [
  { title: 'Critique', value: 'danger' },
  { title: 'Avertissement', value: 'warning' },
  { title: 'Information', value: 'info' }
]

function toggleTheme() {
  theme.global.name.value = isDark.value ? 'dark' : 'light'
}

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

function getSensorName(sensorId) {
  const sensor = sensors.value.find(s => s.id === sensorId)
  return sensor?.name || 'Inconnu'
}

async function toggleRule(rule) {
  try {
    await axios.patch(`/api/alerts/rules/${rule.id}`, {
      is_active: rule.is_active
    })
  } catch (e) {
    console.error('Failed to toggle rule:', e)
  }
}

async function addRule() {
  try {
    await axios.post('/api/alerts/rules', newRule.value)
    await alertsStore.fetchRules()
    showAddRule.value = false
    newRule.value = {
      sensor_id: null,
      condition: '>',
      threshold: 0,
      message: '',
      severity: 'warning'
    }
  } catch (e) {
    console.error('Failed to add rule:', e)
  }
}

onMounted(() => {
  alertsStore.fetchRules()
})
</script>
