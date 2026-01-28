<template>
  <v-dialog v-model="dialogVisible" max-width="500" class="qr-dialog">
    <v-card class="qr-card">
      <!-- Header with gradient -->
      <div class="qr-header">
        <div class="header-bg"></div>
        <div class="header-content">
          <v-btn 
            icon 
            variant="text" 
            size="small" 
            class="close-btn"
            @click="close"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
          <div class="room-badge">
            <v-icon size="20" class="mr-2">mdi-qrcode</v-icon>
            QR Code
          </div>
          <h2 class="room-id-title">{{ room?.id }}</h2>
          <p class="room-name-subtitle">{{ room?.name }}</p>
        </div>
      </div>

      <!-- QR Code Display -->
      <v-card-text class="qr-content">
        <div class="qr-container" :class="{ 'loading': loading }">
          <div v-if="loading" class="qr-loading">
            <v-progress-circular indeterminate color="primary" size="64" />
            <p class="mt-4 text-medium-emphasis">Génération du QR code...</p>
          </div>
          <div v-else class="qr-display">
            <div class="qr-frame" :class="selectedTheme">
              <img 
                :src="qrCodeData" 
                alt="QR Code"
                class="qr-image"
              />
            </div>
            
            <!-- Theme selector -->
            <div class="theme-selector mt-4">
              <v-btn-toggle v-model="selectedTheme" mandatory density="compact">
                <v-btn value="light" size="small">
                  <v-icon start size="16">mdi-white-balance-sunny</v-icon>
                  Clair
                </v-btn>
                <v-btn value="dark" size="small">
                  <v-icon start size="16">mdi-moon-waning-crescent</v-icon>
                  Sombre
                </v-btn>
              </v-btn-toggle>
            </div>
          </div>
        </div>

        <!-- URL Preview -->
        <div class="url-preview mt-4">
          <v-text-field
            :model-value="roomURL"
            label="URL de la salle"
            variant="outlined"
            density="compact"
            readonly
            hide-details
            prepend-inner-icon="mdi-link"
          >
            <template #append-inner>
              <v-btn
                icon
                variant="text"
                size="small"
                @click="copyURL"
                :color="copied ? 'success' : 'default'"
              >
                <v-icon>{{ copied ? 'mdi-check' : 'mdi-content-copy' }}</v-icon>
              </v-btn>
            </template>
          </v-text-field>
        </div>

        <!-- Floor Info -->
        <div class="floor-info mt-4">
          <v-chip color="primary" variant="tonal" class="mr-2">
            <v-icon start size="16">mdi-stairs</v-icon>
            Étage {{ room?.floor }}
          </v-chip>
          <v-chip v-if="room?.type" :color="getRoomTypeColor(room.type)" variant="tonal">
            <v-icon start size="16">{{ getRoomTypeIcon(room.type) }}</v-icon>
            {{ getRoomTypeName(room.type) }}
          </v-chip>
        </div>
      </v-card-text>

      <!-- Actions -->
      <v-card-actions class="qr-actions pa-4">
        <v-row dense>
          <v-col cols="6">
            <v-btn
              color="primary"
              variant="flat"
              block
              @click="downloadPNG"
              :loading="downloading === 'png'"
            >
              <v-icon start>mdi-download</v-icon>
              PNG
            </v-btn>
          </v-col>
          <v-col cols="6">
            <v-btn
              color="secondary"
              variant="flat"
              block
              @click="downloadSVG"
              :loading="downloading === 'svg'"
            >
              <v-icon start>mdi-download</v-icon>
              SVG
            </v-btn>
          </v-col>
          <v-col cols="12">
            <v-btn
              color="success"
              variant="tonal"
              block
              @click="printQR"
              :loading="downloading === 'print'"
            >
              <v-icon start>mdi-printer</v-icon>
              Imprimer (avec affiche)
            </v-btn>
          </v-col>
        </v-row>
      </v-card-actions>

      <!-- Footer tip -->
      <div class="qr-footer">
        <v-icon size="16" class="mr-2">mdi-cellphone</v-icon>
        <span>Scannez avec l'appareil photo de votre téléphone</span>
      </div>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useQRCode } from '@/composables/useQRCode'

const props = defineProps({
  modelValue: Boolean,
  room: Object
})

const emit = defineEmits(['update:modelValue'])

const { 
  generateBrandedQR, 
  downloadQRAsPNG, 
  downloadQRAsSVG, 
  generatePrintablePDF,
  getRoomURL,
  copyRoomURL
} = useQRCode()

// State
const loading = ref(false)
const qrCodeData = ref('')
const selectedTheme = ref('dark')
const copied = ref(false)
const downloading = ref(null)

// Computed
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const roomURL = computed(() => props.room ? getRoomURL(props.room.id) : '')

// Watch for dialog open
watch(() => props.modelValue, async (isOpen) => {
  if (isOpen && props.room) {
    await generateQR()
  }
})

// Watch theme changes
watch(selectedTheme, async () => {
  if (props.room) {
    await generateQR()
  }
})

// Methods
async function generateQR() {
  loading.value = true
  try {
    qrCodeData.value = await generateBrandedQR(props.room.id, selectedTheme.value)
  } catch (err) {
    console.error('Failed to generate QR:', err)
  } finally {
    loading.value = false
  }
}

async function downloadPNG() {
  downloading.value = 'png'
  try {
    await downloadQRAsPNG(props.room.id, props.room.name || props.room.id)
  } finally {
    downloading.value = null
  }
}

async function downloadSVG() {
  downloading.value = 'svg'
  try {
    await downloadQRAsSVG(props.room.id, props.room.name || props.room.id)
  } finally {
    downloading.value = null
  }
}

async function printQR() {
  downloading.value = 'print'
  try {
    await generatePrintablePDF(props.room.id, props.room)
  } finally {
    downloading.value = null
  }
}

async function copyURL() {
  const success = await copyRoomURL(props.room.id)
  if (success) {
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  }
}

function close() {
  dialogVisible.value = false
}

function getRoomTypeColor(type) {
  const colors = {
    classroom: 'blue',
    lab: 'purple',
    meeting: 'orange',
    office: 'green',
    common: 'cyan',
    utility: 'grey'
  }
  return colors[type] || 'grey'
}

function getRoomTypeIcon(type) {
  const icons = {
    classroom: 'mdi-school',
    lab: 'mdi-flask',
    meeting: 'mdi-account-group',
    office: 'mdi-desk',
    common: 'mdi-sofa',
    utility: 'mdi-wrench'
  }
  return icons[type] || 'mdi-door'
}

function getRoomTypeName(type) {
  const names = {
    classroom: 'Salle de cours',
    lab: 'Laboratoire',
    meeting: 'Salle de réunion',
    office: 'Bureau',
    common: 'Espace commun',
    utility: 'Local technique'
  }
  return names[type] || type
}
</script>

<style scoped lang="scss">
.qr-card {
  border-radius: 24px !important;
  overflow: hidden;
  background: rgb(var(--v-theme-surface));
}

.qr-header {
  position: relative;
  padding: 32px 24px;
  text-align: center;
  color: white;
  overflow: hidden;
  
  .header-bg {
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, #00ff9d 0%, #00d4ff 50%, #a855f7 100%);
    opacity: 0.9;
  }
  
  .header-content {
    position: relative;
    z-index: 1;
  }
  
  .close-btn {
    position: absolute;
    top: 8px;
    right: 8px;
    color: white;
  }
  
  .room-badge {
    display: inline-flex;
    align-items: center;
    background: rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(10px);
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 12px;
  }
  
  .room-id-title {
    font-size: 2.5rem;
    font-weight: 800;
    margin: 0;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  }
  
  .room-name-subtitle {
    font-size: 1rem;
    opacity: 0.9;
    margin: 8px 0 0;
  }
}

.qr-content {
  padding: 24px;
}

.qr-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 280px;
  
  &.loading {
    .qr-display { display: none; }
  }
}

.qr-loading {
  text-align: center;
}

.qr-display {
  text-align: center;
}

.qr-frame {
  display: inline-block;
  padding: 16px;
  border-radius: 20px;
  transition: all 0.3s ease;
  
  &.light {
    background: white;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  }
  
  &.dark {
    background: #1a1a2e;
    box-shadow: 0 8px 32px rgba(0, 255, 157, 0.2);
  }
}

.qr-image {
  width: 200px;
  height: 200px;
  display: block;
}

.theme-selector {
  display: flex;
  justify-content: center;
}

.url-preview {
  :deep(.v-field) {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
  }
}

.floor-info {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
}

.qr-actions {
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.qr-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 24px;
  background: rgba(var(--v-theme-primary), 0.1);
  font-size: 12px;
  color: rgb(var(--v-theme-primary));
}

// Animation for QR code appearance
.qr-frame {
  animation: qr-appear 0.5s ease;
}

@keyframes qr-appear {
  from {
    opacity: 0;
    transform: scale(0.8) rotate(-5deg);
  }
  to {
    opacity: 1;
    transform: scale(1) rotate(0);
  }
}
</style>
