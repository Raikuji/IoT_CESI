<template>
  <v-card class="mb-4" color="surface">
    <v-card-title class="d-flex align-center">
      <v-avatar color="error" variant="tonal" size="40" class="mr-3">
        <v-icon>mdi-radiator</v-icon>
      </v-avatar>
      État du Chauffage
      <v-spacer></v-spacer>
      <v-chip color="success" variant="tonal" size="small">
        <v-icon start size="14">mdi-check-circle</v-icon>
        EN DIRECT
      </v-chip>
    </v-card-title>

    <v-card-text class="pa-6">
      <v-row class="mb-4">
        <v-col cols="12" sm="6">
          <div class="text-center">
            <p class="text-body-2 text-medium-emphasis mb-2">Salle</p>
            <p class="text-h5 font-weight-bold">{{ currentState.room || 'N/A' }}</p>
          </div>
        </v-col>
        <v-col cols="12" sm="6">
          <div class="text-center">
            <p class="text-body-2 text-medium-emphasis mb-2">Mode</p>
            <v-chip :color="currentState.mode === 'auto' ? 'success' : 'warning'" variant="tonal">
              {{ currentState.mode === 'auto' ? 'Automatique' : 'Manuel' }}
            </v-chip>
          </div>
        </v-col>
      </v-row>

      <v-divider class="my-4"></v-divider>

      <v-row>
        <v-col cols="12" sm="6">
          <div class="text-center">
            <p class="text-body-2 text-medium-emphasis mb-2">Température cible</p>
            <div class="d-flex align-center justify-center">
              <span class="text-h3 font-weight-bold text-primary">{{ currentState.setpoint || '--' }}</span>
              <span class="text-h6 ml-2">°C</span>
            </div>
          </div>
        </v-col>
        <v-col cols="12" sm="6">
          <div class="text-center">
            <p class="text-body-2 text-medium-emphasis mb-2">Dernière mise à jour</p>
            <p class="text-body-2">{{ lastUpdate }}</p>
          </div>
        </v-col>
      </v-row>

      <v-progress-linear
        class="mt-4"
        :value="((currentState.setpoint || 0) / 30) * 100"
        color="error"
        height="8"
      ></v-progress-linear>
    </v-card-text>

    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn
        variant="tonal"
        size="small"
        @click="fetchHeatingState"
        :loading="loading"
      >
        <v-icon start>mdi-refresh</v-icon>
        Actualiser
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const currentState = ref({
  room: null,
  mode: 'manual',
  setpoint: null
})

const lastUpdate = ref('Jamais')
const loading = ref(false)

const fetchHeatingState = async () => {
  loading.value = true
  try {
    const response = await fetch('http://localhost:8000/api/actuators/heating/state')
    if (response.ok) {
      const data = await response.json()
      currentState.value = data
      lastUpdate.value = new Date().toLocaleTimeString('fr-FR')
    }
  } catch (error) {
    console.error('Erreur lors de la récupération:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchHeatingState()
  // Rafraîchir toutes les 5 secondes
  setInterval(fetchHeatingState, 5000)
})
</script>

<style scoped>
.gradient-border {
  border: 2px solid;
  border-image: linear-gradient(135deg, #ff6b6b, #ff8787) 1;
}
</style>
