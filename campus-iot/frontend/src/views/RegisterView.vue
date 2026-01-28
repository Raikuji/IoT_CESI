<template>
  <div class="register-page">
    <!-- Animated Background -->
    <div class="animated-bg">
      <div class="floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
        <div class="shape shape-4"></div>
        <div class="shape shape-5"></div>
      </div>
      <div class="grid-overlay"></div>
    </div>

    <div class="register-container">
      <!-- Logo & Title -->
      <div class="text-center mb-8">
        <v-avatar color="primary" size="80" class="mb-4 logo-avatar pulse-glow">
          <v-icon size="48">mdi-home-automation</v-icon>
        </v-avatar>
        <h1 class="text-h4 font-weight-bold mb-2 title-gradient">Campus IoT</h1>
        <p class="text-body-2 text-medium-emphasis">Créer un compte</p>
      </div>

      <!-- Register Card -->
      <v-card class="register-card glass-effect" elevation="0">
        <v-card-text class="pa-8">
          <h2 class="text-h5 font-weight-bold mb-6 text-center">Inscription</h2>

          <v-form @submit.prevent="handleRegister" ref="form">
            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model="firstName"
                  label="Prénom"
                  prepend-inner-icon="mdi-account"
                  variant="outlined"
                  :rules="[rules.required]"
                  autocomplete="given-name"
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model="lastName"
                  label="Nom"
                  variant="outlined"
                  :rules="[rules.required]"
                  autocomplete="family-name"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-text-field
              v-model="email"
              label="Email"
              type="email"
              prepend-inner-icon="mdi-email"
              variant="outlined"
              :rules="[rules.required, rules.email]"
              class="mb-4"
              autocomplete="email"
              hint="Utilisez votre email @viacesi.fr"
            ></v-text-field>

            <v-text-field
              v-model="password"
              label="Mot de passe"
              :type="showPassword ? 'text' : 'password'"
              prepend-inner-icon="mdi-lock"
              :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append-inner="showPassword = !showPassword"
              variant="outlined"
              :rules="[rules.required, rules.minLength]"
              class="mb-4"
              autocomplete="new-password"
            ></v-text-field>

            <v-text-field
              v-model="confirmPassword"
              label="Confirmer le mot de passe"
              :type="showPassword ? 'text' : 'password'"
              prepend-inner-icon="mdi-lock-check"
              variant="outlined"
              :rules="[rules.required, rules.match]"
              class="mb-2"
              autocomplete="new-password"
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
              <v-icon start>mdi-account-plus</v-icon>
              S'inscrire
            </v-btn>

            <div class="text-center">
              <span class="text-body-2 text-medium-emphasis">Déjà un compte ?</span>
              <router-link to="/login" class="text-primary ml-1">Se connecter</router-link>
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
const firstName = ref('')
const lastName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref(null)

const rules = {
  required: v => !!v || 'Champ requis',
  email: v => /.+@.+\..+/.test(v) || 'Email invalide',
  minLength: v => v.length >= 6 || 'Minimum 6 caractères',
  match: v => v === password.value || 'Les mots de passe ne correspondent pas'
}

async function handleRegister() {
  const { valid } = await form.value.validate()
  if (!valid) return

  loading.value = true
  error.value = null

  const result = await authStore.register({
    first_name: firstName.value,
    last_name: lastName.value,
    email: email.value,
    password: password.value
  })
  
  loading.value = false
  
  if (result.success) {
    router.push('/')
  } else {
    error.value = result.error
  }
}
</script>

<style scoped lang="scss">
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgb(var(--v-theme-background));
  padding: 24px;
  position: relative;
  overflow: hidden;
}

.animated-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
  
  .floating-shapes {
    position: absolute;
    width: 100%;
    height: 100%;
    
    .shape {
      position: absolute;
      border-radius: 50%;
      filter: blur(60px);
      opacity: 0.6;
      animation: float 20s ease-in-out infinite;
      
      &.shape-1 {
        width: 400px;
        height: 400px;
        background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
        top: -100px;
        right: -100px;
        animation-delay: 0s;
      }
      
      &.shape-2 {
        width: 300px;
        height: 300px;
        background: linear-gradient(135deg, #00ff9d 0%, #00d4ff 100%);
        bottom: 20%;
        left: -80px;
        animation-delay: -5s;
      }
      
      &.shape-3 {
        width: 250px;
        height: 250px;
        background: linear-gradient(135deg, #ff6b6b 0%, #ffa502 100%);
        top: 40%;
        right: 10%;
        animation-delay: -10s;
      }
      
      &.shape-4 {
        width: 200px;
        height: 200px;
        background: linear-gradient(135deg, #22c55e 0%, #14b8a6 100%);
        bottom: -50px;
        left: 30%;
        animation-delay: -15s;
      }
      
      &.shape-5 {
        width: 350px;
        height: 350px;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        top: 10%;
        left: 20%;
        animation-delay: -7s;
      }
    }
  }
  
  .grid-overlay {
    position: absolute;
    width: 100%;
    height: 100%;
    background-image: 
      linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
    background-size: 50px 50px;
  }
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  25% {
    transform: translate(30px, -30px) scale(1.05);
  }
  50% {
    transform: translate(-20px, 20px) scale(0.95);
  }
  75% {
    transform: translate(20px, 10px) scale(1.02);
  }
}

.register-container {
  width: 100%;
  max-width: 480px;
  position: relative;
  z-index: 1;
}

.logo-avatar {
  box-shadow: 0 8px 32px rgba(var(--v-theme-primary), 0.3);
}

.pulse-glow {
  animation: pulse-glow 3s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% {
    box-shadow: 0 0 20px rgba(var(--v-theme-primary), 0.4);
  }
  50% {
    box-shadow: 0 0 40px rgba(var(--v-theme-primary), 0.7), 0 0 60px rgba(var(--v-theme-primary), 0.3);
  }
}

.title-gradient {
  background: linear-gradient(135deg, #a855f7 0%, #6366f1 50%, #00d4ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.glass-effect {
  background: rgba(var(--v-theme-surface), 0.7) !important;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.register-card {
  border-radius: 20px;
}
</style>
