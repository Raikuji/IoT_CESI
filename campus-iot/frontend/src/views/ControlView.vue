<template>
  <div>
    <!-- Header -->
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold mb-1">Contrôle du Chauffage</h1>
        <p class="text-body-2 text-medium-emphasis">
          Envoi de commandes MQTT par salle
        </p>
      </div>
      <v-chip :color="isAuthenticated ? 'success' : 'error'" variant="tonal">
        <v-icon start>{{ isAuthenticated ? 'mdi-check-circle' : 'mdi-alert-circle' }}</v-icon>
        {{ isAuthenticated ? 'Connecté' : 'Non connecté' }}
      </v-chip>
    </div>

    <!-- Auth Alert -->
    <v-alert v-if="!isAuthenticated" type="error" variant="tonal" class="mb-6">
      Vous devez être connecté pour utiliser cette page.
      <v-btn color="error" variant="tonal" class="ml-4" href="/login">Se connecter</v-btn>
    </v-alert>

    <div v-if="isAuthenticated">
      <!-- Room Input -->
      <v-card class="mb-4">
        <v-card-title>
          <v-icon start>mdi-door</v-icon>
          Sélection de la salle
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="room"
            label="Nom de la salle"
            placeholder="X003, C101, B205..."
            prepend-icon="mdi-home"
            variant="outlined"
            hint="Entrez le nom de la salle à contrôler"
            persistent-hint
          />
        </v-card-text>
      </v-card>

      <!-- Mode Selection Tabs -->
      <v-card>
        <v-tabs v-model="selectedTab" bg-color="primary">
          <v-tab value="manual">
            <v-icon start>mdi-hand-back-left</v-icon>
            Mode Manuel
          </v-tab>
          <v-tab value="auto">
            <v-icon start>mdi-robot</v-icon>
            Mode Auto
          </v-tab>
          <v-tab value="eco">
            <v-icon start>mdi-leaf</v-icon>
            Mode Éco
          </v-tab>
        </v-tabs>

        <v-window v-model="selectedTab">
          <!-- MANUAL MODE -->
          <v-window-item value="manual">
            <v-card-text class="pa-6">
              <v-alert type="info" variant="tonal" class="mb-4">
                <strong>Mode Manuel :</strong> Définissez une température fixe pour la salle
              </v-alert>
              
              <div class="text-center mb-4">
                <div class="text-h2 font-weight-bold text-primary">{{ manualTemp }}°C</div>
                <div class="text-caption text-medium-emphasis">Température cible</div>
              </div>

              <v-slider
                v-model="manualTemp"
                :min="10"
                :max="30"
                :step="1"
                color="primary"
                thumb-label
                show-ticks
                class="mb-6"
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
                size="x-large"
                block
                @click="sendCommand('manual', manualTemp, null)"
                :loading="loading"
              >
                <v-icon start>mdi-send</v-icon>
                Envoyer Mode Manuel ({{ manualTemp }}°C)
              </v-btn>
            </v-card-text>
          </v-window-item>

          <!-- AUTO MODE -->
          <v-window-item value="auto">
            <v-card-text class="pa-6">
              <v-alert type="success" variant="tonal" class="mb-4">
                <strong>Mode Auto :</strong> La température s'ajuste automatiquement selon la consigne
              </v-alert>
              
              <div class="text-center mb-4">
                <div class="text-h2 font-weight-bold text-success">{{ autoTemp }}°C</div>
                <div class="text-caption text-medium-emphasis">Température de consigne</div>
              </div>

              <v-slider
                v-model="autoTemp"
                :min="10"
                :max="30"
                :step="1"
                color="success"
                thumb-label
                show-ticks
                class="mb-6"
              >
                <template v-slot:prepend>
                  <v-icon color="info">mdi-snowflake</v-icon>
                </template>
                <template v-slot:append>
                  <v-icon color="error">mdi-fire</v-icon>
                </template>
              </v-slider>

              <v-btn
                color="success"
                size="x-large"
                block
                @click="sendCommand('auto', autoTemp, null)"
                :loading="loading"
              >
                <v-icon start>mdi-send</v-icon>
                Envoyer Mode Auto ({{ autoTemp }}°C)
              </v-btn>
            </v-card-text>
          </v-window-item>

          <!-- ECO MODE -->
          <v-window-item value="eco">
            <v-card-text class="pa-6">
              <v-alert type="warning" variant="tonal" class="mb-4">
                <strong>Mode Éco :</strong> Température réduite pour économiser l'énergie
              </v-alert>
              
              <v-row>
                <v-col cols="12" md="6">
                  <div class="text-center mb-4">
                    <div class="text-h3 font-weight-bold text-warning">{{ ecoNormalTemp }}°C</div>
                    <div class="text-caption text-medium-emphasis">Température normale</div>
                  </div>
                  <v-slider
                    v-model="ecoNormalTemp"
                    :min="10"
                    :max="30"
                    :step="1"
                    color="warning"
                    thumb-label
                    show-ticks
                  />
                </v-col>

                <v-col cols="12" md="6">
                  <div class="text-center mb-4">
                    <div class="text-h3 font-weight-bold text-success">{{ ecoReducedTemp }}°C</div>
                    <div class="text-caption text-medium-emphasis">Température réduite (éco)</div>
                  </div>
                  <v-slider
                    v-model="ecoReducedTemp"
                    :min="10"
                    :max="30"
                    :step="1"
                    color="success"
                    thumb-label
                    show-ticks
                  />
                </v-col>
              </v-row>

              <v-btn
                color="warning"
                size="x-large"
                block
                @click="sendCommand('eco', ecoNormalTemp, ecoReducedTemp)"
                :loading="loading"
                class="mt-4"
              >
                <v-icon start>mdi-send</v-icon>
                Envoyer Mode Éco (Normal: {{ ecoNormalTemp }}°C | Réduit: {{ ecoReducedTemp }}°C)
              </v-btn>
            </v-card-text>
          </v-window-item>
        </v-window>
      </v-card>

      <!-- Last Command -->
      <v-card v-if="lastCommand" class="mt-4">
        <v-card-title class="bg-success text-white">
          <v-icon start color="white">mdi-check-circle</v-icon>
          Dernière commande envoyée
        </v-card-title>
        <v-card-text class="pa-4">
          <v-list bg-color="transparent" density="compact">
            <v-list-item>
              <v-list-item-title>Salle</v-list-item-title>
              <template v-slot:append>
                <strong>{{ lastCommand.room }}</strong>
              </template>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>Mode</v-list-item-title>
              <template v-slot:append>
                <v-chip :color="getModeColor(lastCommand.mode)" size="small">
                  {{ lastCommand.mode.toUpperCase() }}
                </v-chip>
              </template>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>Température</v-list-item-title>
              <template v-slot:append>
                <strong>{{ lastCommand.setpoint }}°C</strong>
              </template>
            </v-list-item>
            <v-list-item v-if="lastCommand.ecoSetpoint">
              <v-list-item-title>Température éco</v-list-item-title>
              <template v-slot:append>
                <strong>{{ lastCommand.ecoSetpoint }}°C</strong>
              </template>
            </v-list-item>
          </v-list>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'

const room = ref('X003')
const selectedTab = ref('manual')
const manualTemp = ref(21)
const autoTemp = ref(21)
const ecoNormalTemp = ref(21)
const ecoReducedTemp = ref(19)
const loading = ref(false)
const lastCommand = ref(null)

const mqttUsername = ref('groupe3')
const mqttPassword = ref('campus-iot')

const isAuthenticated = computed(() => {
  return !!localStorage.getItem('token')
})

function getModeColor(mode) {
  switch(mode) {
    case 'manual': return 'primary'
    case 'auto': return 'success'
    case 'eco': return 'warning'
    default: return 'grey'
  }
}

async function sendCommand(mode, setpoint, ecoSetpoint) {
  const token = localStorage.getItem('token')
  
  if (!token) {
    alert('❌ Vous devez être connecté')
    return
  }
  
  if (!room.value) {
    alert('❌ Veuillez entrer une salle')
    return
  }
  
  loading.value = true
  
  try {
    console.log('📤 Envoi:', { room: room.value, mode, setpoint, ecoSetpoint })
    
    await axios.post(
      `http://localhost:8000/api/actuators/rooms/${room.value}/heating/mode?mode=${mode}&setpoint=${setpoint}`,
      {},
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    )
    
    console.log('✅ Mode envoyé')
    
    if (mode === 'eco' && ecoSetpoint) {
      await axios.post(
        `http://localhost:8000/api/actuators/rooms/${room.value}/eco-setpoint?eco_setpoint=${ecoSetpoint}`,
        {},
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      )
      console.log('✅ Eco setpoint envoyé')
    }
    
    lastCommand.value = {
      room: room.value,
      mode: mode,
      setpoint: setpoint,
      ecoSetpoint: ecoSetpoint
    }
    
    alert('✅ Commande envoyée avec succès !')
    
  } catch (error) {
    console.error('❌ Erreur:', error)
    
    if (error.response?.status === 401) {
      alert('❌ Erreur d\'authentification. Reconnectez-vous.')
    } else {
      alert('❌ Erreur: ' + (error.response?.data?.detail || error.message))
    }
  } finally {
    loading.value = false
  }
}
</script>
