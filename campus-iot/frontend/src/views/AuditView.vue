<template>
  <div class="audit-view">
    <!-- Hero Header -->
    <div class="audit-hero mb-8">
      <div class="hero-content">
        <div class="hero-icon">
          <v-icon size="48" color="white">mdi-clipboard-text-clock</v-icon>
        </div>
        <div class="hero-text">
          <h1 class="text-h3 font-weight-black mb-2">Journal d’audit</h1>
          <p class="text-body-1 opacity-80">
            Qui a modifié quoi, quand, et comment
          </p>
        </div>
      </div>
      <div class="hero-actions">
        <v-btn variant="flat" color="white" class="text-primary" @click="refresh" :loading="loading">
          <v-icon start>mdi-refresh</v-icon>
          Actualiser
        </v-btn>
      </div>
      <div class="hero-decoration"></div>
    </div>

    <v-row>
      <!-- Filters -->
      <v-col cols="12" lg="3">
        <v-card class="filters-card mb-6">
          <v-card-title class="d-flex align-center pa-5 pb-3">
            <v-icon start color="primary">mdi-filter</v-icon>
            <span class="font-weight-bold">Filtres</span>
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-5">
            <v-text-field
              v-model="search"
              prepend-inner-icon="mdi-magnify"
              label="Recherche libre"
              variant="outlined"
              density="compact"
              hide-details
              class="mb-4"
            />

            <v-select
              v-model="filterAction"
              :items="actionOptions"
              label="Action"
              variant="outlined"
              density="compact"
              hide-details
              clearable
              class="mb-4"
            />

            <v-select
              v-model="filterEntity"
              :items="entityOptions"
              label="Objet"
              variant="outlined"
              density="compact"
              hide-details
              clearable
            />
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Audit Table -->
      <v-col cols="12" lg="9">
        <v-card class="audit-card">
          <v-card-title class="d-flex align-center pa-6 pb-4">
            <v-icon start color="primary">mdi-shield-search</v-icon>
            <span class="text-h5 font-weight-bold">Événements</span>
            <v-spacer />
            <v-chip variant="tonal" color="primary">
              {{ filteredLogs.length }} entrées
            </v-chip>
          </v-card-title>
          <v-divider />

          <v-card-text class="pa-0">
            <div v-if="loading" class="text-center py-12">
              <v-progress-circular indeterminate color="primary" size="48" />
              <p class="text-body-2 text-medium-emphasis mt-4">Chargement...</p>
            </div>

            <div v-else-if="filteredLogs.length === 0" class="text-center py-12 text-medium-emphasis">
              <v-icon size="64" class="mb-4">mdi-clipboard-text-off</v-icon>
              <p class="text-body-1">Aucun événement d’audit</p>
            </div>

            <v-data-table
              v-else
              :headers="headers"
              :items="filteredLogs"
              :items-per-page="10"
              class="audit-table"
              show-expand
              density="comfortable"
            >
              <template v-slot:item.action="{ item }">
                <v-chip :color="actionMeta(item.action).color" size="small" variant="flat">
                  <v-icon start size="14">{{ actionMeta(item.action).icon }}</v-icon>
                  {{ actionMeta(item.action).label }}
                </v-chip>
              </template>

              <template v-slot:item.entity_type="{ item }">
                <span class="text-body-2 text-capitalize">{{ formatEntity(item.entity_type) }}</span>
              </template>

              <template v-slot:item.user_email="{ item }">
                <div class="text-body-2">
                  <v-icon size="14" class="mr-1" color="grey">mdi-account</v-icon>
                  {{ item.user_email || 'Système' }}
                </div>
              </template>

              <template v-slot:item.timestamp="{ item }">
                <div class="text-body-2">
                  <v-icon size="14" class="mr-1" color="grey">mdi-clock-outline</v-icon>
                  {{ formatDateTime(item.timestamp) }}
                </div>
              </template>

              <template v-slot:expanded-row="{ columns, item }">
                <tr>
                  <td :colspan="columns.length" class="expanded-cell">
                    <v-row class="py-4 px-2" dense>
                      <v-col cols="12" md="6">
                        <div class="diff-card">
                          <div class="diff-title">
                            <v-icon size="16" class="mr-1">mdi-minus-circle-outline</v-icon>
                            Avant
                          </div>
                          <pre class="diff-content">{{ formatJson(item.before_data) }}</pre>
                        </div>
                      </v-col>
                      <v-col cols="12" md="6">
                        <div class="diff-card success">
                          <div class="diff-title">
                            <v-icon size="16" class="mr-1">mdi-plus-circle-outline</v-icon>
                            Après
                          </div>
                          <pre class="diff-content">{{ formatJson(item.after_data) }}</pre>
                        </div>
                      </v-col>
                    </v-row>
                  </td>
                </tr>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAuditStore } from '@/stores/audit'
import { storeToRefs } from 'pinia'

const auditStore = useAuditStore()
const { logs, loading } = storeToRefs(auditStore)

const search = ref('')
const filterAction = ref(null)
const filterEntity = ref(null)

const headers = [
  { title: 'Action', key: 'action', sortable: true },
  { title: 'Objet', key: 'entity_type', sortable: true },
  { title: 'ID', key: 'entity_id', sortable: true },
  { title: 'Utilisateur', key: 'user_email', sortable: true },
  { title: 'Date', key: 'timestamp', sortable: true }
]

const actionOptions = [
  { title: 'Création', value: 'create' },
  { title: 'Modification', value: 'update' },
  { title: 'Suppression', value: 'delete' },
  { title: 'Acquittement', value: 'acknowledge' }
]

const entityOptions = computed(() => {
  const types = new Set(logs.value.map(l => l.entity_type).filter(Boolean))
  return Array.from(types).sort().map(t => ({ title: formatEntity(t), value: t }))
})

const filteredLogs = computed(() => {
  return logs.value.filter(l => {
    if (filterAction.value && l.action !== filterAction.value) return false
    if (filterEntity.value && l.entity_type !== filterEntity.value) return false
    if (search.value) {
      const hay = `${l.entity_type} ${l.entity_id} ${l.user_email}`.toLowerCase()
      if (!hay.includes(search.value.toLowerCase())) return false
    }
    return true
  })
})

function actionMeta(action) {
  const map = {
    create: { label: 'Création', color: 'success', icon: 'mdi-plus-circle' },
    update: { label: 'Modification', color: 'info', icon: 'mdi-pencil' },
    delete: { label: 'Suppression', color: 'error', icon: 'mdi-delete' },
    acknowledge: { label: 'Acquittement', color: 'warning', icon: 'mdi-check-circle' }
  }
  return map[action] || { label: action, color: 'grey', icon: 'mdi-information' }
}

function formatEntity(entity) {
  if (!entity) return '—'
  return entity.replace(/_/g, ' ')
}

function formatDateTime(dateStr) {
  if (!dateStr) return '—'
  const date = new Date(dateStr)
  return date.toLocaleString('fr-FR')
}

function formatJson(value) {
  if (!value) return '—'
  try {
    return JSON.stringify(value, null, 2)
  } catch (e) {
    return String(value)
  }
}

async function refresh() {
  await auditStore.fetchLogs({ limit: 200 })
}

onMounted(() => {
  refresh()
})
</script>

<style scoped>
.audit-hero {
  position: relative;
  padding: 32px;
  border-radius: 24px;
  background: linear-gradient(135deg, #1f2937 0%, #0f172a 100%);
  color: #fff;
  overflow: hidden;
}

.hero-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.hero-icon {
  width: 72px;
  height: 72px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
}

.hero-actions {
  position: absolute;
  right: 24px;
  top: 24px;
}

.hero-decoration {
  position: absolute;
  right: -40px;
  bottom: -40px;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0) 70%);
}

.filters-card,
.audit-card {
  border-radius: 20px;
}

.audit-table :deep(thead th) {
  font-weight: 700;
}

.expanded-cell {
  background: rgba(148, 163, 184, 0.08);
}

.diff-card {
  background: rgba(15, 23, 42, 0.04);
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 14px;
  padding: 12px;
}

.diff-card.success {
  border-color: rgba(34, 197, 94, 0.4);
  background: rgba(34, 197, 94, 0.08);
}

.diff-title {
  display: flex;
  align-items: center;
  font-weight: 600;
  margin-bottom: 8px;
}

.diff-content {
  margin: 0;
  font-size: 12px;
  max-height: 240px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
