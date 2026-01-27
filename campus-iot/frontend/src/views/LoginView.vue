<template>
  <div class="login-page">
    <div class="login-container">
      <!-- Logo & Title -->
      <div class="text-center mb-8">
        <v-avatar color="primary" size="80" class="mb-4 logo-avatar">
          <v-icon size="48">mdi-home-automation</v-icon>
        </v-avatar>
        <h1 class="text-h4 font-weight-bold mb-2">Campus IoT</h1>
        <p class="text-body-2 text-medium-emphasis">Bâtiment Orion - CESI Nancy</p>
      </div>

      <!-- Login Card -->
      <v-card class="login-card" elevation="0">
        <v-card-text class="pa-8">
          <h2 class="text-h5 font-weight-bold mb-6 text-center">Connexion</h2>

          <v-form @submit.prevent="handleLogin" ref="form">
            <v-text-field
              v-model="email"
              label="Email"
              type="email"
              prepend-inner-icon="mdi-email"
              variant="outlined"
              :rules="[rules.required, rules.email]"
              class="mb-4"
              autocomplete="email"
            ></v-text-field>

            <v-text-field
              v-model="password"
              label="Mot de passe"
              :type="showPassword ? 'text' : 'password'"
              prepend-inner-icon="mdi-lock"
              :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append-inner="showPassword = !showPassword"
              variant="outlined"
              :rules="[rules.required]"
              class="mb-2"
              autocomplete="current-password"
            ></v-text-field>

            <v-alert
              v-if="error"
              type="error"
              variant="tonal"
              class="mb-4"
              closable
              @click:close="error = null"
            >
              {{ error }}
            </v-alert>

            <v-btn
              type="submit"
              color="primary"
              size="large"
              block
              :loading="loading"
              class="mb-4"
            >
              <v-icon start>mdi-login</v-icon>
              Se connecter
            </v-btn>

            <div class="text-center">
              <span class="text-body-2 text-medium-emphasis">Pas encore de compte ?</span>
              <router-link to="/register" class="text-primary ml-1">S'inscrire</router-link>
            </div>
          </v-form>
        </v-card-text>
      </v-card>

      <!-- Footer -->
      <p class="text-center text-caption text-medium-emphasis mt-6">
        © 2026 CESI Nancy - Projet IoT
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = ref(null)
const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref(null)

const rules = {
  required: v => !!v || 'Champ requis',
  email: v => /.+@.+\..+/.test(v) || 'Email invalide'
}

async function handleLogin() {
  const { valid } = await form.value.validate()
  if (!valid) return

  loading.value = true
  error.value = null

  const result = await authStore.login(email.value, password.value)
  
  loading.value = false
  
  if (result.success) {
    router.push('/')
  } else {
    error.value = result.error
  }
}
</script>

<style scoped lang="scss">
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: 
    radial-gradient(ellipse at top, rgba(var(--v-theme-primary), 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at bottom, rgba(var(--v-theme-secondary), 0.1) 0%, transparent 50%),
    rgb(var(--v-theme-background));
  padding: 24px;
}

.login-container {
  width: 100%;
  max-width: 420px;
}

.logo-avatar {
  box-shadow: 0 8px 32px rgba(var(--v-theme-primary), 0.3);
}

.login-card {
  background: rgba(var(--v-theme-surface), 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
  border-radius: 16px;
}
</style>
