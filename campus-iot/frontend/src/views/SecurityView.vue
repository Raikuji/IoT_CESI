<template>
  <div class="security-view">
    <!-- Header with stats -->
    <v-row class="mb-6">
      <v-col cols="12">
        <v-card class="security-header">
          <v-card-text class="d-flex align-center justify-space-between flex-wrap ga-4">
            <div class="d-flex align-center ga-4">
              <div class="security-icon" :class="securityScoreClass">
                <v-icon size="40">mdi-shield-lock</v-icon>
              </div>
              <div>
                <h1 class="text-h4 font-weight-bold mb-1">Sécurité IoT</h1>
                <p class="text-body-2 text-medium-emphasis mb-0">
                  HMAC-SHA256 • Blockchain • Intégrité des données
                </p>
              </div>
            </div>
            
            <div class="security-score">
              <div class="score-ring" :class="securityScoreClass">
                <svg viewBox="0 0 100 100">
                  <circle class="score-bg" cx="50" cy="50" r="42" />
                  <circle 
                    class="score-progress" 
                    cx="50" 
                    cy="50" 
                    r="42"
                    :style="{ strokeDasharray: `${(stats.security_score || 100) * 2.64} 264` }"
                  />
                </svg>
                <div class="score-content">
                  <span class="score-value">{{ stats.security_score || 100 }}</span>
                  <span class="score-label">Score</span>
                </div>
              </div>
              <!-- Confetti for 100% score -->
              <div v-if="(stats.security_score || 100) >= 100" class="confetti-container">
                <div v-for="i in 12" :key="i" class="confetti" :style="{ '--i': i }"></div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Stats Cards -->
    <v-row class="mb-6">
      <v-col cols="12" sm="6" md="3">
        <v-card class="stat-card">
          <v-card-text class="text-center">
            <v-icon size="32" color="primary" class="mb-2">mdi-cube-outline</v-icon>
            <div class="text-h4 font-weight-bold">{{ stats.blockchain?.total_blocks || 0 }}</div>
            <div class="text-body-2 text-medium-emphasis">Blocs</div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card class="stat-card">
          <v-card-text class="text-center">
            <v-icon size="32" :color="stats.blockchain?.chain_valid ? 'success' : 'error'" class="mb-2">
              {{ stats.blockchain?.chain_valid ? 'mdi-check-circle' : 'mdi-alert-circle' }}
            </v-icon>
            <div class="text-h4 font-weight-bold">{{ stats.blockchain?.chain_valid ? 'Valide' : 'Erreur' }}</div>
            <div class="text-body-2 text-medium-emphasis">Chaîne</div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card class="stat-card">
          <v-card-text class="text-center">
            <v-icon size="32" color="success" class="mb-2">mdi-check-decagram</v-icon>
            <div class="text-h4 font-weight-bold">{{ stats.blockchain?.valid_signatures || 0 }}</div>
            <div class="text-body-2 text-medium-emphasis">Signatures OK</div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card class="stat-card" :class="{ 'alert-card': stats.alerts?.unresolved > 0 }">
          <v-card-text class="text-center">
            <v-icon size="32" :color="stats.alerts?.unresolved > 0 ? 'warning' : 'grey'" class="mb-2">
              mdi-alert
            </v-icon>
            <div class="text-h4 font-weight-bold">{{ stats.alerts?.unresolved || 0 }}</div>
            <div class="text-body-2 text-medium-emphasis">Alertes</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <!-- Blockchain Viewer -->
      <v-col cols="12" lg="8">
        <v-card class="blockchain-card">
          <v-card-title class="d-flex align-center justify-space-between">
            <span>
              <v-icon start color="primary">mdi-link-variant</v-icon>
              Blockchain
            </span>
            <div class="d-flex ga-2">
              <v-btn
                variant="outlined"
                size="small"
                @click="verifyChain"
                :loading="verifying"
              >
                <v-icon start>mdi-check-all</v-icon>
                Vérifier
              </v-btn>
              <v-btn
                variant="outlined"
                size="small"
                color="primary"
                @click="loadBlockchain"
              >
                <v-icon>mdi-refresh</v-icon>
              </v-btn>
            </div>
          </v-card-title>
          
          <v-card-text>
            <div class="blockchain-chain" v-if="blocks.length > 0">
              <transition-group name="block-enter" appear>
              <div
                v-for="(block, index) in blocks"
                :key="block.id"
                class="block-item"
                :class="{ 'genesis': block.index === 0 }"
                :style="{ '--delay': `${index * 0.1}s` }"
              >
                <div class="block-header">
                  <v-chip
                    size="small"
                    :color="block.index === 0 ? 'purple' : 'primary'"
                    variant="flat"
                  >
                    #{{ block.index }}
                  </v-chip>
                  <v-icon
                    size="small"
                    :color="block.signature_valid ? 'success' : 'error'"
                  >
                    {{ block.signature_valid ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                  </v-icon>
                </div>
                
                <div class="block-content">
                  <div class="block-data">
                    <span class="data-type">{{ block.sensor_type }}</span>
                    <span class="data-value">{{ block.sensor_value }}</span>
                  </div>
                  <div class="block-hash">
                    <code>{{ block.hash?.substring(0, 16) }}...</code>
                  </div>
                  <div class="block-time">
                    {{ formatTime(block.timestamp) }}
                  </div>
                </div>
                
                <div class="block-link" v-if="index < blocks.length - 1">
                  <v-icon size="20" color="primary">mdi-arrow-down</v-icon>
                </div>
              </div>
              </transition-group>
            </div>
            
            <v-alert v-else type="info" variant="tonal">
              Aucun bloc dans la blockchain. Les données seront ajoutées automatiquement.
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Security Alerts & Tools -->
      <v-col cols="12" lg="4">
        <!-- Test Signature Tool -->
        <v-card class="mb-4">
          <v-card-title>
            <v-icon start color="primary">mdi-key</v-icon>
            Test HMAC
          </v-card-title>
          <v-card-text>
            <v-text-field
              v-model="testMessage"
              label="Message à signer"
              variant="outlined"
              density="compact"
              class="mb-2"
            ></v-text-field>
            <v-btn
              color="primary"
              variant="flat"
              block
              @click="signMessage"
              :loading="signing"
            >
              <v-icon start>mdi-pencil-lock</v-icon>
              Signer
            </v-btn>
            
            <div v-if="signedResult" class="mt-3">
              <v-alert type="success" variant="tonal" density="compact">
                <div class="text-caption">Signature:</div>
                <code class="text-caption">{{ signedResult.signature?.substring(0, 32) }}...</code>
              </v-alert>
            </div>

            <v-textarea
              v-model="signedPayload"
              label="Payload signé"
              placeholder="temperature:23.5|ts:...|sig:..."
              variant="outlined"
              density="compact"
              rows="3"
              class="mt-3"
            ></v-textarea>
            <v-btn
              color="success"
              variant="flat"
              block
              class="mt-2"
              @click="verifyHmac"
              :loading="verifyingHmac"
              :disabled="!signedPayload"
            >
              <v-icon start>mdi-shield-check</v-icon>
              Vérifier
            </v-btn>

            <v-btn
              color="primary"
              variant="text"
              block
              class="mt-1"
              @click="generateSignedPayload"
              :loading="generatingPayload"
            >
              <v-icon start>mdi-test-tube</v-icon>
              Générer un exemple
            </v-btn>

            <div v-if="hmacVerifyResult" class="mt-3">
              <v-alert
                :type="hmacVerifyResult.valid ? 'success' : 'error'"
                variant="tonal"
                density="compact"
              >
                <div class="text-caption">
                  {{ hmacVerifyResult.valid ? 'Signature valide' : 'Signature invalide' }}
                </div>
                <div class="text-caption text-medium-emphasis">
                  {{ hmacVerifyResult.message }}
                </div>
              </v-alert>
            </div>
          </v-card-text>
        </v-card>

        <!-- Security Alerts -->
        <v-card>
          <v-card-title class="d-flex align-center justify-space-between">
            <span>
              <v-icon start color="warning">mdi-alert</v-icon>
              Alertes Sécurité
            </span>
            <v-chip size="small" color="warning" v-if="alerts.length > 0">
              {{ alerts.length }}
            </v-chip>
          </v-card-title>
          
          <v-card-text>
            <v-list v-if="alerts.length > 0" density="compact" bg-color="transparent">
              <v-list-item
                v-for="alert in alerts.slice(0, 5)"
                :key="alert.id"
                class="alert-item"
              >
                <template #prepend>
                  <v-icon
                    :color="getSeverityColor(alert.severity)"
                    size="small"
                  >
                    {{ getSeverityIcon(alert.severity) }}
                  </v-icon>
                </template>
                <v-list-item-title class="text-body-2">
                  {{ alert.alert_type }}
                </v-list-item-title>
                <v-list-item-subtitle class="text-caption">
                  {{ formatTime(alert.timestamp) }}
                </v-list-item-subtitle>
                <template #append>
                  <v-btn
                    v-if="!alert.resolved"
                    icon
                    variant="text"
                    size="small"
                    @click="resolveAlert(alert.id)"
                  >
                    <v-icon size="small">mdi-check</v-icon>
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>
            
            <v-alert v-else type="success" variant="tonal" density="compact" :icon="false">
              <v-icon start>mdi-shield-check</v-icon>
              Aucune alerte de sécurité
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Verification Result Dialog -->
    <v-dialog v-model="verifyDialog" max-width="400">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon
            :color="verifyResult?.valid ? 'success' : 'error'"
            class="mr-2"
          >
            {{ verifyResult?.valid ? 'mdi-check-circle' : 'mdi-alert-circle' }}
          </v-icon>
          Vérification Blockchain
        </v-card-title>
        <v-card-text>
          <p>{{ verifyResult?.message }}</p>
          <p class="text-caption text-medium-emphasis">
            {{ verifyResult?.blocks_verified }} blocs vérifiés
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="verifyDialog = false">Fermer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// State
const stats = ref({})
const blocks = ref([])
const alerts = ref([])
const testMessage = ref('temperature:23.5')
const signedResult = ref(null)
const signedPayload = ref('')
const hmacVerifyResult = ref(null)
const verifyResult = ref(null)
const verifyDialog = ref(false)
const verifying = ref(false)
const signing = ref(false)
const verifyingHmac = ref(false)
const generatingPayload = ref(false)
const snackbar = ref({ show: false, text: '', color: 'success' })

// Computed
const securityScoreClass = computed(() => {
  const score = stats.value.security_score || 100
  if (score >= 80) return 'score-good'
  if (score >= 50) return 'score-warning'
  return 'score-danger'
})

// Methods
async function loadStats() {
  try {
    const res = await fetch(`${API_URL}/security/stats`)
    stats.value = await res.json()
  } catch (e) {
    console.error('Failed to load stats:', e)
  }
}

async function loadBlockchain() {
  try {
    const res = await fetch(`${API_URL}/security/blockchain?limit=20`)
    const data = await res.json()
    blocks.value = data.blocks || []
  } catch (e) {
    console.error('Failed to load blockchain:', e)
  }
}

async function loadAlerts() {
  try {
    const res = await fetch(`${API_URL}/security/alerts?unresolved_only=true&limit=10`)
    const data = await res.json()
    alerts.value = data.alerts || []
  } catch (e) {
    console.error('Failed to load alerts:', e)
  }
}

async function verifyChain() {
  verifying.value = true
  try {
    const res = await fetch(`${API_URL}/security/blockchain/verify`)
    verifyResult.value = await res.json()
    verifyDialog.value = true
  } catch (e) {
    console.error('Failed to verify chain:', e)
  } finally {
    verifying.value = false
  }
}

async function signMessage() {
  if (!testMessage.value) return
  
  signing.value = true
  try {
    const res = await fetch(`${API_URL}/security/sign?message=${encodeURIComponent(testMessage.value)}`, {
      method: 'POST'
    })
    signedResult.value = await res.json()
    signedPayload.value = signedResult.value?.signed_format || ''
    hmacVerifyResult.value = null
  } catch (e) {
    console.error('Failed to sign message:', e)
  } finally {
    signing.value = false
  }
}

async function generateSignedPayload() {
  generatingPayload.value = true
  try {
    const res = await fetch(`${API_URL}/security/test-signature`)
    const data = await res.json()
    signedPayload.value = data.full_payload || ''
    testMessage.value = data.message_to_sign || testMessage.value
    hmacVerifyResult.value = null
  } catch (e) {
    console.error('Failed to generate signed payload:', e)
  } finally {
    generatingPayload.value = false
  }
}

async function verifyHmac() {
  if (!signedPayload.value) return
  verifyingHmac.value = true
  try {
    const res = await fetch(`${API_URL}/security/verify?raw_data=${encodeURIComponent(signedPayload.value)}`, {
      method: 'POST'
    })
    hmacVerifyResult.value = await res.json()
  } catch (e) {
    console.error('Failed to verify HMAC:', e)
  } finally {
    verifyingHmac.value = false
  }
}

async function resolveAlert(alertId) {
  try {
    await fetch(`${API_URL}/security/alerts/${alertId}/resolve`, { method: 'POST' })
    snackbar.value = { show: true, text: 'Alerte résolue', color: 'success' }
    loadAlerts()
    loadStats()
  } catch (e) {
    console.error('Failed to resolve alert:', e)
  }
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getSeverityColor(severity) {
  const colors = {
    critical: 'error',
    warning: 'warning',
    info: 'info'
  }
  return colors[severity] || 'grey'
}

function getSeverityIcon(severity) {
  const icons = {
    critical: 'mdi-alert-octagon',
    warning: 'mdi-alert',
    info: 'mdi-information'
  }
  return icons[severity] || 'mdi-alert'
}

onMounted(() => {
  loadStats()
  loadBlockchain()
  loadAlerts()
})
</script>

<style scoped lang="scss">
.security-view {
  min-height: 100%;
}

.security-header {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.1) 0%, transparent 100%);
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
}

.security-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &.score-good {
    background: rgba(76, 175, 80, 0.15);
    color: #4caf50;
  }
  
  &.score-warning {
    background: rgba(255, 152, 0, 0.15);
    color: #ff9800;
  }
  
  &.score-danger {
    background: rgba(244, 67, 54, 0.15);
    color: #f44336;
  }
}

.security-score {
  position: relative;
  
  .score-ring {
    width: 100px;
    height: 100px;
    position: relative;
    
    svg {
      width: 100%;
      height: 100%;
      transform: rotate(-90deg);
      
      circle {
        fill: none;
        stroke-width: 6;
        stroke-linecap: round;
      }
      
      .score-bg {
        stroke: rgba(255, 255, 255, 0.1);
      }
      
      .score-progress {
        stroke: currentColor;
        transition: stroke-dasharray 1s ease;
        animation: score-fill 1.5s ease forwards;
      }
    }
    
    .score-content {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      text-align: center;
    }
    
    &.score-good {
      color: #22c55e;
      .score-value { color: #22c55e; }
    }
    
    &.score-warning {
      color: #f59e0b;
      .score-value { color: #f59e0b; }
    }
    
    &.score-danger {
      color: #ef4444;
      .score-value { color: #ef4444; }
    }
    
    .score-value {
      font-size: 1.5rem;
      font-weight: bold;
      display: block;
    }
    
    .score-label {
      font-size: 0.65rem;
      opacity: 0.7;
    }
  }
  
  .confetti-container {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    pointer-events: none;
    
    .confetti {
      position: absolute;
      width: 8px;
      height: 8px;
      border-radius: 2px;
      animation: confetti-burst 2s ease-out infinite;
      animation-delay: calc(var(--i) * 0.1s);
      
      &:nth-child(1) { background: #ff6b6b; }
      &:nth-child(2) { background: #ffa502; }
      &:nth-child(3) { background: #22c55e; }
      &:nth-child(4) { background: #3b82f6; }
      &:nth-child(5) { background: #a855f7; }
      &:nth-child(6) { background: #00d4ff; }
      &:nth-child(7) { background: #ff6b6b; }
      &:nth-child(8) { background: #ffa502; }
      &:nth-child(9) { background: #22c55e; }
      &:nth-child(10) { background: #3b82f6; }
      &:nth-child(11) { background: #a855f7; }
      &:nth-child(12) { background: #00d4ff; }
    }
  }
}

@keyframes score-fill {
  from {
    stroke-dasharray: 0 264;
  }
}

@keyframes confetti-burst {
  0% {
    transform: translate(0, 0) rotate(0deg) scale(1);
    opacity: 1;
  }
  100% {
    transform: translate(
      calc(cos(var(--i) * 30deg) * 60px),
      calc(sin(var(--i) * 30deg) * 60px - 20px)
    ) rotate(360deg) scale(0);
    opacity: 0;
  }
}

.stat-card {
  transition: transform 0.2s;
  
  &:hover {
    transform: translateY(-2px);
  }
  
  &.alert-card {
    border: 1px solid rgba(255, 152, 0, 0.5);
  }
}

.blockchain-card {
  min-height: 500px;
}

.blockchain-chain {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

// Block animation
.block-enter-enter-active {
  animation: block-slide-in 0.5s ease forwards;
  animation-delay: var(--delay);
  opacity: 0;
}

@keyframes block-slide-in {
  from {
    opacity: 0;
    transform: translateX(-30px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}

.block-item {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
  padding: 12px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateX(4px);
    border-color: rgba(var(--v-theme-primary), 0.3);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }
  
  &.genesis {
    border-color: rgba(156, 39, 176, 0.5);
    background: rgba(156, 39, 176, 0.1);
  }
  
  .block-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }
  
  .block-content {
    .block-data {
      display: flex;
      gap: 8px;
      align-items: baseline;
      
      .data-type {
        font-weight: 600;
        color: rgb(var(--v-theme-primary));
      }
      
      .data-value {
        font-size: 1.1rem;
      }
    }
    
    .block-hash {
      margin-top: 4px;
      
      code {
        font-size: 0.75rem;
        opacity: 0.6;
        background: rgba(var(--v-theme-on-surface), 0.05);
        padding: 2px 6px;
        border-radius: 4px;
      }
    }
    
    .block-time {
      font-size: 0.75rem;
      opacity: 0.5;
      margin-top: 4px;
    }
  }
  
  .block-link {
    display: flex;
    justify-content: center;
    margin-top: 8px;
  }
}

.alert-item {
  border-radius: 8px;
  margin-bottom: 4px;
  
  &:hover {
    background: rgba(var(--v-theme-surface-variant), 0.3);
  }
}
</style>
