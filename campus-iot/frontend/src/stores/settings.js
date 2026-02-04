import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useSettingsStore = defineStore('settings', () => {
  // System settings (loaded from Supabase)
  const settings = ref({})
  const loading = ref(false)
  const error = ref(null)

  // Computed getters for common settings
  const tempMin = computed(() => settings.value.temp_min ?? 18)
  const tempMax = computed(() => settings.value.temp_max ?? 26)
  const humidityMin = computed(() => settings.value.humidity_min ?? 30)
  const humidityMax = computed(() => settings.value.humidity_max ?? 70)
  const co2Max = computed(() => settings.value.co2_max ?? 1000)
  const presenceTimeout = computed(() => settings.value.presence_timeout ?? 300)
  const emailNotifications = computed(() => settings.value.email_notifications ?? true)
  const pushNotifications = computed(() => settings.value.push_notifications ?? true)
  const defaultTheme = computed(() => settings.value.default_theme ?? 'dark')
  const defaultFloor = computed(() => settings.value.default_floor ?? 'RDC')
  const autoRefreshInterval = computed(() => settings.value.auto_refresh_interval ?? 30)
  const dataRetentionDays = computed(() => settings.value.data_retention_days ?? 90)
  const energySavingEnabled = computed(() => settings.value.energy_saving_enabled ?? false)
  const energySavingRefreshInterval = computed(() => settings.value.energy_saving_refresh_interval ?? 120)
  const energySavingRefreshIntervalNight = computed(() => settings.value.energy_saving_refresh_interval_night ?? 300)
  const energySavingDisableLive = computed(() => settings.value.energy_saving_disable_live ?? true)
  const energyProfile = computed(() => settings.value.energy_profile ?? 'normal')
  const energyScheduleEnabled = computed(() => settings.value.energy_schedule_enabled ?? false)
  const energyScheduleProfile = computed(() => settings.value.energy_schedule_profile ?? 'eco')
  const energyScheduleDays = computed(() => settings.value.energy_schedule_days ?? [])
  const energyScheduleStart = computed(() => settings.value.energy_schedule_start ?? '22:00')
  const energyScheduleEnd = computed(() => settings.value.energy_schedule_end ?? '06:00')

  // Fetch all settings from API
  async function fetchSettings() {
    loading.value = true
    error.value = null
    try {
      const response = await axios.get('/api/settings/system/dict')
      settings.value = response.data
    } catch (e) {
      error.value = e.message
      console.error('Failed to fetch settings:', e)
    } finally {
      loading.value = false
    }
  }

  // Get a specific setting
  async function getSetting(key) {
    try {
      const response = await axios.get(`/api/settings/system/${key}`)
      return response.data.value
    } catch (e) {
      console.error(`Failed to get setting ${key}:`, e)
      return null
    }
  }

  // Update a setting (admin only)
  async function updateSetting(key, value) {
    try {
      await axios.put(`/api/settings/system/${key}`, { value: String(value) })
      settings.value[key] = value
      return { success: true }
    } catch (e) {
      console.error(`Failed to update setting ${key}:`, e)
      return { success: false, error: e.response?.data?.detail || e.message }
    }
  }

  // Update multiple settings (admin only)
  async function updateSettings(newSettings) {
    try {
      const stringSettings = {}
      for (const [key, value] of Object.entries(newSettings)) {
        stringSettings[key] = String(value)
      }
      
      await axios.put('/api/settings/system/bulk', stringSettings)
      
      // Update local
      for (const [key, value] of Object.entries(newSettings)) {
        settings.value[key] = value
      }
      
      return { success: true }
    } catch (e) {
      console.error('Failed to update settings:', e)
      return { success: false, error: e.response?.data?.detail || e.message }
    }
  }

  // Handle WebSocket setting changes
  function handleSettingChanged(data) {
    settings.value[data.key] = data.value
  }

  // Check if value is within alert thresholds
  function checkTemperature(value) {
    if (value < tempMin.value) return { status: 'cold', severity: 'warning' }
    if (value > tempMax.value) return { status: 'hot', severity: 'danger' }
    return { status: 'ok', severity: 'success' }
  }

  function checkHumidity(value) {
    if (value < humidityMin.value) return { status: 'dry', severity: 'warning' }
    if (value > humidityMax.value) return { status: 'humid', severity: 'warning' }
    return { status: 'ok', severity: 'success' }
  }

  function checkCO2(value) {
    if (value > co2Max.value) return { status: 'high', severity: 'danger' }
    if (value > co2Max.value * 0.8) return { status: 'elevated', severity: 'warning' }
    return { status: 'ok', severity: 'success' }
  }

  return {
    settings,
    loading,
    error,
    tempMin,
    tempMax,
    humidityMin,
    humidityMax,
    co2Max,
    presenceTimeout,
    emailNotifications,
    pushNotifications,
    defaultTheme,
    defaultFloor,
    autoRefreshInterval,
    dataRetentionDays,
    energySavingEnabled,
    energySavingRefreshInterval,
    energySavingRefreshIntervalNight,
    energySavingDisableLive,
    energyProfile,
    energyScheduleEnabled,
    energyScheduleProfile,
    energyScheduleDays,
    energyScheduleStart,
    energyScheduleEnd,
    fetchSettings,
    getSetting,
    updateSetting,
    updateSettings,
    handleSettingChanged,
    checkTemperature,
    checkHumidity,
    checkCO2
  }
})
