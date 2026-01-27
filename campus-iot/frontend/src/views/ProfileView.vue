<template>
  <div class="profile-view">
    <!-- Profile Header -->
    <div class="profile-hero mb-8">
      <div class="hero-content">
        <div class="avatar-section">
          <v-avatar 
            :color="user?.avatar_color || '#3b82f6'" 
            size="120" 
            class="profile-avatar"
            @click="showAvatarPicker = true"
          >
            <span class="text-h3 font-weight-bold text-white">{{ userInitials }}</span>
            <div class="avatar-overlay">
              <v-icon>mdi-camera</v-icon>
            </div>
          </v-avatar>
          <v-chip 
            :color="user?.role_info?.color" 
            variant="flat" 
            class="mt-3"
          >
            <v-icon start size="14">{{ user?.role_info?.icon }}</v-icon>
            {{ user?.role_info?.name }}
          </v-chip>
        </div>
        <div class="user-info">
          <h1 class="text-h3 font-weight-black mb-2">{{ user?.first_name }} {{ user?.last_name }}</h1>
          <p class="text-body-1 opacity-80 mb-1">{{ user?.email }}</p>
          <p class="text-body-2 opacity-60">{{ user?.department }}</p>
        </div>
      </div>
      <div class="hero-decoration"></div>
    </div>

    <v-row>
      <!-- Personal Information -->
      <v-col cols="12" lg="6">
        <v-card class="profile-card">
          <v-card-title class="d-flex align-center pa-6 pb-4">
            <v-icon start color="primary" size="28">mdi-account-edit</v-icon>
            <span class="text-h6 font-weight-bold">Informations personnelles</span>
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-6">
            <v-form @submit.prevent="saveProfile" ref="profileForm">
              <v-text-field
                v-model="profileData.first_name"
                label="Prénom"
                prepend-inner-icon="mdi-account"
                variant="outlined"
                class="mb-4"
                :rules="[rules.required]"
              ></v-text-field>

              <v-text-field
                v-model="profileData.last_name"
                label="Nom"
                prepend-inner-icon="mdi-account"
                variant="outlined"
                class="mb-4"
                :rules="[rules.required]"
              ></v-text-field>

              <v-text-field
                v-model="profileData.department"
                label="Département"
                prepend-inner-icon="mdi-domain"
                variant="outlined"
                class="mb-4"
              ></v-text-field>

              <v-text-field
                :model-value="user?.email"
                label="Email"
                prepend-inner-icon="mdi-email"
                variant="outlined"
                disabled
                hint="L'email ne peut pas être modifié"
              ></v-text-field>

              <v-btn
                type="submit"
                color="primary"
                size="large"
                class="mt-6"
                :loading="saving"
                block
              >
                <v-icon start>mdi-content-save</v-icon>
                Enregistrer les modifications
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Security -->
      <v-col cols="12" lg="6">
        <v-card class="profile-card mb-6">
          <v-card-title class="d-flex align-center pa-6 pb-4">
            <v-icon start color="warning" size="28">mdi-shield-lock</v-icon>
            <span class="text-h6 font-weight-bold">Sécurité</span>
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-6">
            <v-form @submit.prevent="changePassword" ref="passwordForm">
              <v-text-field
                v-model="passwordData.current"
                label="Mot de passe actuel"
                prepend-inner-icon="mdi-lock"
                :append-inner-icon="showCurrentPassword ? 'mdi-eye-off' : 'mdi-eye'"
                @click:append-inner="showCurrentPassword = !showCurrentPassword"
                :type="showCurrentPassword ? 'text' : 'password'"
                variant="outlined"
                class="mb-4"
                :rules="[rules.required]"
              ></v-text-field>

              <v-text-field
                v-model="passwordData.new"
                label="Nouveau mot de passe"
                prepend-inner-icon="mdi-lock-plus"
                :append-inner-icon="showNewPassword ? 'mdi-eye-off' : 'mdi-eye'"
                @click:append-inner="showNewPassword = !showNewPassword"
                :type="showNewPassword ? 'text' : 'password'"
                variant="outlined"
                class="mb-4"
                :rules="[rules.required, rules.minLength]"
              ></v-text-field>

              <v-text-field
                v-model="passwordData.confirm"
                label="Confirmer le mot de passe"
                prepend-inner-icon="mdi-lock-check"
                :type="showNewPassword ? 'text' : 'password'"
                variant="outlined"
                class="mb-2"
                :rules="[rules.required, rules.match]"
              ></v-text-field>

              <v-btn
                type="submit"
                color="warning"
                size="large"
                class="mt-4"
                :loading="changingPassword"
                block
              >
                <v-icon start>mdi-key-change</v-icon>
                Changer le mot de passe
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>

        <!-- Account Stats -->
        <v-card class="profile-card">
          <v-card-title class="d-flex align-center pa-6 pb-4">
            <v-icon start color="info" size="28">mdi-chart-box</v-icon>
            <span class="text-h6 font-weight-bold">Statistiques du compte</span>
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-6">
            <v-list bg-color="transparent" density="comfortable">
              <v-list-item>
                <template v-slot:prepend>
                  <v-avatar color="success" variant="tonal" size="40">
                    <v-icon>mdi-calendar-check</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title>Membre depuis</v-list-item-title>
                <template v-slot:append>
                  <span class="font-weight-semibold">{{ formatDate(user?.created_at) }}</span>
                </template>
              </v-list-item>

              <v-list-item>
                <template v-slot:prepend>
                  <v-avatar color="info" variant="tonal" size="40">
                    <v-icon>mdi-clock-outline</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title>Dernière connexion</v-list-item-title>
                <template v-slot:append>
                  <span class="font-weight-semibold">{{ formatDateTime(user?.last_login) }}</span>
                </template>
              </v-list-item>

              <v-list-item>
                <template v-slot:prepend>
                  <v-avatar :color="user?.role_info?.color" variant="tonal" size="40">
                    <v-icon>{{ user?.role_info?.icon }}</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title>Niveau d'accès</v-list-item-title>
                <template v-slot:append>
                  <v-chip :color="user?.role_info?.color" size="small">
                    {{ user?.role_info?.name }}
                  </v-chip>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Avatar Color Picker Dialog -->
    <v-dialog v-model="showAvatarPicker" max-width="400">
      <v-card>
        <v-card-title class="d-flex align-center pa-6 pb-4">
          <v-icon start color="primary">mdi-palette</v-icon>
          Choisir une couleur
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-6">
          <div class="color-grid">
            <v-avatar
              v-for="color in avatarColors"
              :key="color"
              :color="color"
              size="48"
              class="color-option"
              :class="{ selected: selectedColor === color }"
              @click="selectedColor = color"
            >
              <v-icon v-if="selectedColor === color" color="white">mdi-check</v-icon>
            </v-avatar>
          </div>
        </v-card-text>
        <v-divider />
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="showAvatarPicker = false">Annuler</v-btn>
          <v-btn color="primary" variant="flat" @click="saveAvatarColor">
            Appliquer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000" location="top">
      <div class="d-flex align-center">
        <v-icon start>{{ snackbar.icon }}</v-icon>
        {{ snackbar.text }}
      </div>
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import axios from 'axios'

const authStore = useAuthStore()
const { user } = storeToRefs(authStore)

const profileForm = ref(null)
const passwordForm = ref(null)

const profileData = ref({
  first_name: '',
  last_name: '',
  department: ''
})

const passwordData = ref({
  current: '',
  new: '',
  confirm: ''
})

const saving = ref(false)
const changingPassword = ref(false)
const showCurrentPassword = ref(false)
const showNewPassword = ref(false)
const showAvatarPicker = ref(false)
const selectedColor = ref('')

const avatarColors = [
  '#ef4444', '#f97316', '#f59e0b', '#eab308',
  '#84cc16', '#22c55e', '#10b981', '#14b8a6',
  '#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1',
  '#8b5cf6', '#a855f7', '#d946ef', '#ec4899',
  '#f43f5e', '#64748b'
]

const snackbar = ref({
  show: false,
  text: '',
  color: 'success',
  icon: 'mdi-check-circle'
})

const rules = {
  required: v => !!v || 'Champ requis',
  minLength: v => v.length >= 6 || 'Minimum 6 caractères',
  match: v => v === passwordData.value.new || 'Les mots de passe ne correspondent pas'
}

const userInitials = computed(() => {
  if (!user.value) return ''
  return `${user.value.first_name?.[0] || ''}${user.value.last_name?.[0] || ''}`.toUpperCase()
})

function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  })
}

function formatDateTime(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString('fr-FR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function showNotification(text, type = 'success') {
  snackbar.value = {
    show: true,
    text,
    color: type,
    icon: type === 'success' ? 'mdi-check-circle' : type === 'error' ? 'mdi-alert-circle' : 'mdi-information'
  }
}

async function saveProfile() {
  const { valid } = await profileForm.value.validate()
  if (!valid) return

  saving.value = true
  try {
    const response = await axios.put('/api/auth/profile', profileData.value)
    authStore.user = response.data
    showNotification('Profil mis à jour avec succès')
  } catch (e) {
    showNotification(e.response?.data?.detail || 'Erreur lors de la mise à jour', 'error')
  } finally {
    saving.value = false
  }
}

async function changePassword() {
  const { valid } = await passwordForm.value.validate()
  if (!valid) return

  changingPassword.value = true
  try {
    await axios.put('/api/auth/password', {
      current_password: passwordData.value.current,
      new_password: passwordData.value.new
    })
    showNotification('Mot de passe modifié avec succès')
    passwordData.value = { current: '', new: '', confirm: '' }
  } catch (e) {
    showNotification(e.response?.data?.detail || 'Erreur lors du changement de mot de passe', 'error')
  } finally {
    changingPassword.value = false
  }
}

async function saveAvatarColor() {
  try {
    const response = await axios.put('/api/auth/profile', {
      avatar_color: selectedColor.value
    })
    authStore.user = response.data
    showAvatarPicker.value = false
    showNotification('Couleur mise à jour')
  } catch (e) {
    showNotification('Erreur', 'error')
  }
}

onMounted(() => {
  if (user.value) {
    profileData.value = {
      first_name: user.value.first_name,
      last_name: user.value.last_name,
      department: user.value.department
    }
    selectedColor.value = user.value.avatar_color || '#3b82f6'
  }
})
</script>

<style scoped lang="scss">
.profile-view {
  max-width: 1200px;
  margin: 0 auto;
}

.profile-hero {
  position: relative;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 50%, #1e40af 100%);
  border-radius: 24px;
  padding: 48px;
  overflow: hidden;
}

.hero-content {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 32px;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.profile-avatar {
  cursor: pointer;
  position: relative;
  transition: transform 0.2s ease;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);

  &:hover {
    transform: scale(1.05);

    .avatar-overlay {
      opacity: 1;
    }
  }
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.user-info {
  color: white;
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

.profile-card {
  border-radius: 16px;
}

.color-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
}

.color-option {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;

  &:hover {
    transform: scale(1.1);
  }

  &.selected {
    box-shadow: 0 0 0 3px white, 0 0 0 5px currentColor;
    transform: scale(1.1);
  }
}
</style>
