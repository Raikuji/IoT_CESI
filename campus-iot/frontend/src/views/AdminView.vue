<template>
  <div class="admin-view">
    <!-- Hero Header -->
    <div class="admin-hero mb-8">
      <div class="hero-content">
        <div class="hero-icon">
          <v-icon size="48" color="white">mdi-shield-crown</v-icon>
        </div>
        <div class="hero-text">
          <h1 class="text-h3 font-weight-black mb-2">Administration</h1>
          <p class="text-body-1 opacity-80">
            Gestion des utilisateurs et des accès au système IoT
          </p>
        </div>
      </div>
      <div class="hero-decoration"></div>
    </div>

    <!-- Stats Cards -->
    <v-row class="mb-8">
      <v-col cols="12" sm="6" md="3">
        <v-card class="stat-card stat-total">
          <v-card-text class="pa-6">
            <div class="d-flex align-center justify-space-between">
              <div>
                <div class="stat-value">{{ stats.total_users }}</div>
                <div class="stat-label">Utilisateurs</div>
              </div>
              <div class="stat-icon">
                <v-icon size="32">mdi-account-group</v-icon>
              </div>
            </div>
            <div class="stat-trend mt-3">
              <v-icon size="14" color="success">mdi-trending-up</v-icon>
              <span class="text-caption ml-1">+{{ recentLoginsCount }} actifs aujourd'hui</span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="stat-card stat-active">
          <v-card-text class="pa-6">
            <div class="d-flex align-center justify-space-between">
              <div>
                <div class="stat-value">{{ stats.active_users }}</div>
                <div class="stat-label">Actifs</div>
              </div>
              <div class="stat-icon">
                <v-icon size="32">mdi-account-check</v-icon>
              </div>
            </div>
            <v-progress-linear
              :model-value="activePercentage"
              color="success"
              height="6"
              rounded
              class="mt-3"
            ></v-progress-linear>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="stat-card stat-admins">
          <v-card-text class="pa-6">
            <div class="d-flex align-center justify-space-between">
              <div>
                <div class="stat-value">{{ stats.role_distribution?.admin || 0 }}</div>
                <div class="stat-label">Admins</div>
              </div>
              <div class="stat-icon">
                <v-icon size="32">mdi-shield-crown</v-icon>
              </div>
            </div>
            <div class="stat-badges mt-3">
              <v-chip size="x-small" color="warning" variant="flat" class="mr-1">
                {{ stats.role_distribution?.technician || 0 }} Tech
              </v-chip>
              <v-chip size="x-small" color="purple" variant="flat">
                {{ stats.role_distribution?.manager || 0 }} Resp
              </v-chip>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="stat-card stat-inactive">
          <v-card-text class="pa-6">
            <div class="d-flex align-center justify-space-between">
              <div>
                <div class="stat-value">{{ stats.inactive_users }}</div>
                <div class="stat-label">Désactivés</div>
              </div>
              <div class="stat-icon">
                <v-icon size="32">mdi-account-off</v-icon>
              </div>
            </div>
            <div class="stat-trend mt-3" v-if="stats.inactive_users > 0">
              <v-icon size="14" color="warning">mdi-alert</v-icon>
              <span class="text-caption ml-1">Comptes à vérifier</span>
            </div>
            <div class="stat-trend mt-3" v-else>
              <v-icon size="14" color="success">mdi-check-circle</v-icon>
              <span class="text-caption ml-1">Tout est OK</span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Main Content -->
    <v-row>
      <!-- Users Table -->
      <v-col cols="12" lg="8">
        <v-card class="users-card">
          <v-card-title class="d-flex align-center pa-6 pb-4">
            <v-icon start color="primary" size="28">mdi-account-multiple</v-icon>
            <span class="text-h5 font-weight-bold">Utilisateurs</span>
            <v-spacer />
            <v-text-field
              v-model="search"
              prepend-inner-icon="mdi-magnify"
              placeholder="Rechercher..."
              single-line
              hide-details
              density="compact"
              variant="outlined"
              class="search-field"
              style="max-width: 280px"
            ></v-text-field>
          </v-card-title>

          <v-divider />

          <v-data-table
            :headers="headers"
            :items="filteredUsers"
            :loading="loading"
            :items-per-page="10"
            class="users-table"
            hover
          >
            <template v-slot:item.user="{ item }">
              <div class="d-flex align-center ga-3 py-2">
                <v-avatar :color="item.avatar_color" size="42">
                  <span class="text-body-2 font-weight-bold text-white">
                    {{ getInitials(item) }}
                  </span>
                </v-avatar>
                <div>
                  <div class="font-weight-semibold">{{ item.first_name }} {{ item.last_name }}</div>
                  <div class="text-caption text-medium-emphasis">{{ item.email }}</div>
                </div>
              </div>
            </template>

            <template v-slot:item.role="{ item }">
              <v-chip
                :color="item.role_info.color"
                size="small"
                variant="flat"
                class="font-weight-medium"
              >
                <v-icon start size="14">{{ item.role_info.icon }}</v-icon>
                {{ item.role_info.name }}
              </v-chip>
            </template>

            <template v-slot:item.department="{ item }">
              <span class="text-body-2">{{ item.department }}</span>
            </template>

            <template v-slot:item.status="{ item }">
              <v-chip
                :color="item.is_active ? 'success' : 'error'"
                size="small"
                variant="tonal"
              >
                <v-icon start size="12">
                  {{ item.is_active ? 'mdi-check-circle' : 'mdi-close-circle' }}
                </v-icon>
                {{ item.is_active ? 'Actif' : 'Inactif' }}
              </v-chip>
            </template>

            <template v-slot:item.last_login="{ item }">
              <div class="text-body-2">
                <v-icon size="14" class="mr-1" color="grey">mdi-clock-outline</v-icon>
                {{ formatDate(item.last_login) }}
              </div>
            </template>

            <template v-slot:item.actions="{ item }">
              <div class="d-flex ga-1">
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  @click="openEditDialog(item)"
                >
                  <v-icon size="18">mdi-pencil</v-icon>
                  <v-tooltip activator="parent" location="top">Modifier</v-tooltip>
                </v-btn>
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  @click="openRoleDialog(item)"
                  :disabled="item.email === currentUser?.email"
                >
                  <v-icon size="18">mdi-shield-edit</v-icon>
                  <v-tooltip activator="parent" location="top">Changer le rôle</v-tooltip>
                </v-btn>
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  :color="item.is_active ? 'warning' : 'success'"
                  @click="toggleUserStatus(item)"
                  :disabled="item.email === currentUser?.email"
                >
                  <v-icon size="18">
                    {{ item.is_active ? 'mdi-account-off' : 'mdi-account-check' }}
                  </v-icon>
                  <v-tooltip activator="parent" location="top">
                    {{ item.is_active ? 'Désactiver' : 'Activer' }}
                  </v-tooltip>
                </v-btn>
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  color="error"
                  @click="confirmDelete(item)"
                  :disabled="item.email === currentUser?.email"
                >
                  <v-icon size="18">mdi-delete</v-icon>
                  <v-tooltip activator="parent" location="top">Supprimer</v-tooltip>
                </v-btn>
              </div>
            </template>
          </v-data-table>
        </v-card>
      </v-col>

      <!-- Sidebar -->
      <v-col cols="12" lg="4">
        <!-- Roles Legend -->
        <v-card class="roles-card mb-6">
          <v-card-title class="d-flex align-center pa-5 pb-3">
            <v-icon start color="primary">mdi-shield-star</v-icon>
            <span class="font-weight-bold">Rôles & Permissions</span>
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-0">
            <v-list density="comfortable" class="roles-list">
              <v-list-item
                v-for="(role, key) in roles"
                :key="key"
                class="role-item"
              >
                <template v-slot:prepend>
                  <v-avatar :color="role.color" size="36">
                    <v-icon size="18" color="white">{{ role.icon }}</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title class="font-weight-semibold">
                  {{ role.name }}
                </v-list-item-title>
                <v-list-item-subtitle class="text-wrap">
                  {{ role.description }}
                </v-list-item-subtitle>
                <template v-slot:append>
                  <v-chip size="x-small" color="grey" variant="tonal">
                    {{ stats.role_distribution?.[key] || 0 }}
                  </v-chip>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>

        <!-- Backups -->
        <v-card class="backup-card mb-6">
          <v-card-title class="d-flex align-center pa-5 pb-3">
            <v-icon start color="primary">mdi-database</v-icon>
            <span class="font-weight-bold">Backups DB</span>
            <v-spacer />
            <v-btn
              size="small"
              color="primary"
              variant="tonal"
              :loading="backupRunning"
              @click="runBackup"
            >
              <v-icon start size="16">mdi-content-save</v-icon>
              Créer
            </v-btn>
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-0">
            <div class="px-5 pt-4 pb-2 text-caption text-medium-emphasis">
              Rétention auto: {{ backupRetentionDays }} jours
            </div>
            <v-list v-if="backups.length" density="compact" class="backup-list">
              <v-list-item v-for="item in backups" :key="item.name" class="backup-item">
                <template v-slot:prepend>
                  <v-avatar color="primary" size="32" variant="tonal">
                    <v-icon size="16">mdi-archive</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title class="text-body-2">
                  {{ item.name }}
                </v-list-item-title>
                <v-list-item-subtitle class="text-caption">
                  {{ formatDate(item.created_at) }} • {{ formatSize(item.size) }}
                </v-list-item-subtitle>
                <template v-slot:append>
                  <v-btn
                    size="x-small"
                    color="warning"
                    variant="tonal"
                    @click="openRestoreDialog(item)"
                  >
                    Restaurer
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>
            <div v-else class="text-center py-8 text-medium-emphasis">
              <v-icon size="48" class="mb-2">mdi-database-off</v-icon>
              <p class="text-body-2">Aucun backup disponible</p>
            </div>
          </v-card-text>
        </v-card>

        <!-- Webhooks -->
        <v-card class="webhook-card mb-6">
          <v-card-title class="d-flex align-center pa-5 pb-3">
            <v-icon start color="primary">mdi-webhook</v-icon>
            <span class="font-weight-bold">Webhooks</span>
            <v-spacer />
            <v-btn size="small" color="primary" variant="tonal" @click="openWebhookDialog">
              <v-icon start size="16">mdi-plus</v-icon>
              Ajouter
            </v-btn>
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-0">
            <v-list v-if="webhooks.length" density="compact">
              <v-list-item v-for="hook in webhooks" :key="hook.id" class="webhook-item">
                <template v-slot:prepend>
                  <v-avatar color="primary" size="32" variant="tonal">
                    <v-icon size="16">mdi-link-variant</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title class="text-body-2">
                  {{ hook.name }}
                </v-list-item-title>
                <v-list-item-subtitle class="text-caption">
                  {{ hook.url }}
                </v-list-item-subtitle>
                <template v-slot:append>
                  <v-btn size="x-small" variant="text" @click="testWebhook(hook)">
                    Tester
                  </v-btn>
                  <v-btn size="x-small" color="error" variant="text" @click="deleteWebhook(hook)">
                    Supprimer
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>
            <div v-else class="text-center py-6 text-medium-emphasis">
              <v-icon size="40" class="mb-2">mdi-webhook</v-icon>
              <p class="text-body-2">Aucun webhook configuré</p>
            </div>
          </v-card-text>
        </v-card>

        <!-- Exports -->
        <v-card class="export-card mb-6">
          <v-card-title class="d-flex align-center pa-5 pb-3">
            <v-icon start color="primary">mdi-file-export</v-icon>
            <span class="font-weight-bold">Exports automatiques</span>
            <v-spacer />
            <v-btn size="small" color="primary" variant="tonal" @click="openExportDialog">
              <v-icon start size="16">mdi-plus</v-icon>
              Ajouter
            </v-btn>
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-0">
            <v-list v-if="exports.length" density="compact">
              <v-list-item v-for="exp in exports" :key="exp.id" class="export-item">
                <template v-slot:prepend>
                  <v-avatar color="primary" size="32" variant="tonal">
                    <v-icon size="16">mdi-database-export</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title class="text-body-2">
                  {{ exp.name }}
                </v-list-item-title>
                <v-list-item-subtitle class="text-caption">
                  {{ exp.resource }} • {{ exp.format }} • {{ exp.interval_minutes }} min
                </v-list-item-subtitle>
                <template v-slot:append>
                  <v-btn size="x-small" variant="text" @click="runExport(exp)">Lancer</v-btn>
                  <v-btn size="x-small" color="error" variant="text" @click="deleteExport(exp)">
                    Supprimer
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>
            <div v-else class="text-center py-6 text-medium-emphasis">
              <v-icon size="40" class="mb-2">mdi-file-export</v-icon>
              <p class="text-body-2">Aucun export configuré</p>
            </div>
          </v-card-text>
        </v-card>

        <!-- Recent Activity -->
        <v-card class="activity-card">
          <v-card-title class="d-flex align-center pa-5 pb-3">
            <v-icon start color="success">mdi-history</v-icon>
            <span class="font-weight-bold">Activité récente</span>
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-0">
            <v-list v-if="stats.recent_logins?.length" density="compact" class="activity-list">
              <v-list-item
                v-for="user in stats.recent_logins?.slice(0, 5)"
                :key="user.id"
                class="activity-item"
              >
                <template v-slot:prepend>
                  <v-avatar :color="user.avatar_color" size="32">
                    <span class="text-caption font-weight-bold text-white">
                      {{ getInitials(user) }}
                    </span>
                  </v-avatar>
                </template>
                <v-list-item-title class="text-body-2">
                  {{ user.first_name }} {{ user.last_name }}
                </v-list-item-title>
                <v-list-item-subtitle class="text-caption">
                  Connecté {{ formatRelativeTime(user.last_login) }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
            <div v-else class="text-center py-8 text-medium-emphasis">
              <v-icon size="48" class="mb-2">mdi-account-clock</v-icon>
              <p class="text-body-2">Aucune activité récente</p>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Edit User Dialog -->
    <v-dialog v-model="editDialog.show" max-width="500">
      <v-card class="edit-dialog">
        <v-card-title class="d-flex align-center pa-6 pb-4">
          <v-avatar :color="editDialog.user?.avatar_color" size="40" class="mr-3">
            <span class="text-body-2 font-weight-bold text-white">
              {{ getInitials(editDialog.user) }}
            </span>
          </v-avatar>
          <div>
            <div class="text-h6">Modifier l'utilisateur</div>
            <div class="text-caption text-medium-emphasis">{{ editDialog.user?.email }}</div>
          </div>
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-6">
          <v-text-field
            v-model="editDialog.first_name"
            label="Prénom"
            variant="outlined"
            class="mb-4"
          ></v-text-field>
          <v-text-field
            v-model="editDialog.last_name"
            label="Nom"
            variant="outlined"
            class="mb-4"
          ></v-text-field>
          <v-text-field
            v-model="editDialog.department"
            label="Département"
            variant="outlined"
          ></v-text-field>
        </v-card-text>
        <v-divider />
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="editDialog.show = false">Annuler</v-btn>
          <v-btn color="primary" variant="flat" @click="saveUser" :loading="editDialog.loading">
            <v-icon start>mdi-check</v-icon>
            Enregistrer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Role Change Dialog -->
    <v-dialog v-model="roleDialog.show" max-width="450">
      <v-card class="role-dialog">
        <v-card-title class="d-flex align-center pa-6 pb-4">
          <v-icon start color="primary" size="28">mdi-shield-edit</v-icon>
          <span class="text-h6">Changer le rôle</span>
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-6">
          <div class="text-center mb-6">
            <v-avatar :color="roleDialog.user?.avatar_color" size="64" class="mb-3">
              <span class="text-h6 font-weight-bold text-white">
                {{ getInitials(roleDialog.user) }}
              </span>
            </v-avatar>
            <div class="text-h6">{{ roleDialog.user?.first_name }} {{ roleDialog.user?.last_name }}</div>
            <div class="text-caption text-medium-emphasis">{{ roleDialog.user?.email }}</div>
          </div>

          <v-item-group v-model="roleDialog.selectedRole" mandatory>
            <v-row dense>
              <v-col cols="12" v-for="(role, key) in roles" :key="key">
                <v-item :value="key" v-slot="{ isSelected, toggle }">
                  <v-card
                    :color="isSelected ? role.color : 'surface'"
                    :variant="isSelected ? 'flat' : 'outlined'"
                    class="role-option pa-3"
                    @click="toggle"
                  >
                    <div class="d-flex align-center">
                      <v-avatar :color="isSelected ? 'white' : role.color" size="36" class="mr-3">
                        <v-icon :color="isSelected ? role.color : 'white'" size="18">
                          {{ role.icon }}
                        </v-icon>
                      </v-avatar>
                      <div class="flex-grow-1">
                        <div class="font-weight-semibold" :class="isSelected ? 'text-white' : ''">
                          {{ role.name }}
                        </div>
                        <div class="text-caption" :class="isSelected ? 'text-white opacity-80' : 'text-medium-emphasis'">
                          {{ role.description }}
                        </div>
                      </div>
                      <v-icon v-if="isSelected" color="white">mdi-check-circle</v-icon>
                    </div>
                  </v-card>
                </v-item>
              </v-col>
            </v-row>
          </v-item-group>
        </v-card-text>
        <v-divider />
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="roleDialog.show = false">Annuler</v-btn>
          <v-btn color="primary" variant="flat" @click="saveRole" :loading="roleDialog.loading">
            <v-icon start>mdi-shield-check</v-icon>
            Appliquer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog.show" max-width="400">
      <v-card class="delete-dialog">
        <v-card-text class="text-center pa-8">
          <v-avatar color="error" size="80" class="mb-4">
            <v-icon size="48" color="white">mdi-alert</v-icon>
          </v-avatar>
          <h3 class="text-h5 font-weight-bold mb-2">Supprimer l'utilisateur ?</h3>
          <p class="text-body-2 text-medium-emphasis mb-4">
            Êtes-vous sûr de vouloir supprimer 
            <strong>{{ deleteDialog.user?.first_name }} {{ deleteDialog.user?.last_name }}</strong> ?
            <br>Cette action est irréversible.
          </p>
          <div class="d-flex ga-3 justify-center">
            <v-btn variant="outlined" @click="deleteDialog.show = false" size="large">
              Annuler
            </v-btn>
            <v-btn color="error" variant="flat" @click="deleteUser" :loading="deleteDialog.loading" size="large">
              <v-icon start>mdi-delete</v-icon>
              Supprimer
            </v-btn>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000" location="top">
      <div class="d-flex align-center">
        <v-icon start>{{ snackbar.icon }}</v-icon>
        {{ snackbar.text }}
      </div>
    </v-snackbar>

    <!-- Restore Backup Dialog -->
    <v-dialog v-model="restoreDialog.show" max-width="520">
      <v-card>
        <v-card-title class="d-flex align-center pa-6 pb-4">
          <v-icon start color="warning">mdi-alert</v-icon>
          <span class="text-h6">Restaurer un backup</span>
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-6">
          <p class="text-body-2 mb-4">
            Cette action remplace la base de données par le contenu du backup sélectionné.
          </p>
          <v-alert type="warning" variant="tonal">
            Backup ciblé : <strong>{{ restoreDialog.backup?.name }}</strong>
          </v-alert>
        </v-card-text>
        <v-divider />
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="restoreDialog.show = false">Annuler</v-btn>
          <v-btn color="warning" :loading="restoreDialog.loading" @click="confirmRestore">
            Restaurer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Webhook Dialog -->
    <v-dialog v-model="webhookDialog.show" max-width="520">
      <v-card>
        <v-card-title class="d-flex align-center pa-6 pb-4">
          <v-icon start color="primary">mdi-webhook</v-icon>
          <span class="text-h6">Nouveau webhook</span>
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-6">
          <v-text-field v-model="webhookDialog.name" label="Nom" variant="outlined" class="mb-4" />
          <v-text-field v-model="webhookDialog.url" label="URL" variant="outlined" class="mb-4" />
          <v-text-field v-model="webhookDialog.secret" label="Secret (optionnel)" variant="outlined" class="mb-4" />
          <v-select
            v-model="webhookDialog.event_types"
            :items="webhookEventOptions"
            label="Événements"
            multiple
            chips
            variant="outlined"
            class="mb-4"
          />
          <v-switch v-model="webhookDialog.is_active" label="Actif" color="primary" inset />
        </v-card-text>
        <v-divider />
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="webhookDialog.show = false">Annuler</v-btn>
          <v-btn color="primary" :loading="webhookDialog.loading" @click="saveWebhook">Créer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Export Dialog -->
    <v-dialog v-model="exportDialog.show" max-width="560">
      <v-card>
        <v-card-title class="d-flex align-center pa-6 pb-4">
          <v-icon start color="primary">mdi-file-export</v-icon>
          <span class="text-h6">Nouvel export</span>
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-6">
          <v-text-field v-model="exportDialog.name" label="Nom" variant="outlined" class="mb-4" />
          <v-row>
            <v-col cols="12" sm="6">
              <v-select v-model="exportDialog.resource" :items="exportResourceOptions" label="Ressource" variant="outlined" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-select v-model="exportDialog.format" :items="exportFormatOptions" label="Format" variant="outlined" />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="12" sm="6">
              <v-text-field v-model.number="exportDialog.interval_minutes" type="number" label="Intervalle (min)" variant="outlined" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model.number="exportDialog.time_window_hours" type="number" label="Fenêtre (h)" variant="outlined" />
            </v-col>
          </v-row>
          <v-select v-model="exportDialog.target" :items="exportTargetOptions" label="Cible" variant="outlined" class="mb-4" />
          <v-select
            v-if="exportDialog.target === 'webhook'"
            v-model="exportDialog.webhook_id"
            :items="webhookOptions"
            label="Webhook cible"
            variant="outlined"
          />
          <v-switch v-model="exportDialog.is_active" label="Actif" color="primary" inset class="mt-4" />
        </v-card-text>
        <v-divider />
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="exportDialog.show = false">Annuler</v-btn>
          <v-btn color="primary" :loading="exportDialog.loading" @click="saveExport">Créer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import axios from 'axios'

const authStore = useAuthStore()
const { user: currentUser } = storeToRefs(authStore)

const users = ref([])
const roles = ref({})
const stats = ref({})
const loading = ref(false)
const search = ref('')

const headers = [
  { title: 'Utilisateur', key: 'user', sortable: true },
  { title: 'Rôle', key: 'role', sortable: true },
  { title: 'Département', key: 'department', sortable: true },
  { title: 'Statut', key: 'status', sortable: true },
  { title: 'Dernière connexion', key: 'last_login', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false, align: 'end', width: '180px' }
]

// Dialogs
const editDialog = ref({
  show: false,
  user: null,
  first_name: '',
  last_name: '',
  department: '',
  loading: false
})

const roleDialog = ref({
  show: false,
  user: null,
  selectedRole: '',
  loading: false
})

const deleteDialog = ref({
  show: false,
  user: null,
  loading: false
})

const snackbar = ref({
  show: false,
  text: '',
  color: 'success',
  icon: 'mdi-check-circle'
})

const backups = ref([])
const backupRunning = ref(false)
const backupRetentionDays = ref(7)

const webhooks = ref([])
const exports = ref([])

const webhookDialog = ref({
  show: false,
  name: '',
  url: '',
  secret: '',
  event_types: [],
  is_active: true,
  loading: false
})

const exportDialog = ref({
  show: false,
  name: '',
  resource: 'alerts',
  format: 'csv',
  interval_minutes: 1440,
  time_window_hours: 24,
  target: 'file',
  webhook_id: null,
  is_active: true,
  loading: false
})

const restoreDialog = ref({
  show: false,
  backup: null,
  loading: false
})

const webhookEventOptions = [
  { title: 'Alerte déclenchée', value: 'alert.triggered' },
  { title: 'Alerte escaladée', value: 'alert.escalated' },
  { title: 'Anomalie détectée', value: 'anomaly.detected' },
  { title: 'Export prêt', value: 'export.ready' }
]

const exportResourceOptions = [
  { title: 'Alertes', value: 'alerts' },
  { title: 'Capteurs', value: 'sensors' },
  { title: 'Anomalies', value: 'anomalies' }
]

const exportFormatOptions = [
  { title: 'CSV', value: 'csv' },
  { title: 'JSON', value: 'json' }
]

const exportTargetOptions = [
  { title: 'Fichier', value: 'file' },
  { title: 'Webhook', value: 'webhook' }
]

const webhookOptions = computed(() =>
  webhooks.value.map(w => ({ title: w.name, value: w.id }))
)

// Computed
const filteredUsers = computed(() => {
  if (!search.value) return users.value
  const s = search.value.toLowerCase()
  return users.value.filter(u => 
    u.first_name?.toLowerCase().includes(s) ||
    u.last_name?.toLowerCase().includes(s) ||
    u.email?.toLowerCase().includes(s) ||
    u.department?.toLowerCase().includes(s)
  )
})

const activePercentage = computed(() => {
  if (!stats.value.total_users) return 0
  return (stats.value.active_users / stats.value.total_users) * 100
})

const recentLoginsCount = computed(() => stats.value.recent_logins?.length || 0)

// Methods
function getInitials(user) {
  if (!user) return ''
  return `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase()
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatSize(bytes) {
  if (!bytes && bytes !== 0) return '—'
  const sizes = ['o', 'Ko', 'Mo', 'Go']
  if (bytes === 0) return '0 o'
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`
}

function formatRelativeTime(dateStr) {
  if (!dateStr) return ''
  const now = new Date()
  const date = new Date(dateStr)
  const diff = Math.floor((now - date) / 1000)
  
  if (diff < 60) return "à l'instant"
  if (diff < 3600) return `il y a ${Math.floor(diff / 60)} min`
  if (diff < 86400) return `il y a ${Math.floor(diff / 3600)}h`
  return formatDate(dateStr)
}

function showNotification(text, type = 'success') {
  snackbar.value = {
    show: true,
    text,
    color: type,
    icon: type === 'success' ? 'mdi-check-circle' : type === 'error' ? 'mdi-alert-circle' : 'mdi-information'
  }
}

async function fetchData() {
  loading.value = true
  try {
    const [usersRes, statsRes, rolesRes] = await Promise.all([
      axios.get('/api/auth/users'),
      axios.get('/api/auth/stats'),
      axios.get('/api/auth/roles')
    ])
    users.value = usersRes.data
    stats.value = statsRes.data
    roles.value = rolesRes.data
    await fetchIntegrations()
    await fetchBackups()
  } catch (e) {
    console.error('Failed to fetch data:', e)
    showNotification('Erreur lors du chargement', 'error')
  } finally {
    loading.value = false
  }
}

async function fetchIntegrations() {
  try {
    const [hooksRes, exportsRes] = await Promise.all([
      axios.get('/api/integrations/webhooks'),
      axios.get('/api/integrations/exports')
    ])
    webhooks.value = hooksRes.data
    exports.value = exportsRes.data
  } catch (e) {
    console.error('Failed to fetch integrations:', e)
  }
}

function openWebhookDialog() {
  webhookDialog.value = {
    show: true,
    name: '',
    url: '',
    secret: '',
    event_types: [],
    is_active: true,
    loading: false
  }
}

async function saveWebhook() {
  webhookDialog.value.loading = true
  try {
    await axios.post('/api/integrations/webhooks', {
      name: webhookDialog.value.name,
      url: webhookDialog.value.url,
      secret: webhookDialog.value.secret || null,
      event_types: webhookDialog.value.event_types || [],
      is_active: webhookDialog.value.is_active
    })
    await fetchIntegrations()
    webhookDialog.value.show = false
    showNotification('Webhook créé')
  } catch (e) {
    showNotification(e.response?.data?.detail || 'Erreur webhook', 'error')
  } finally {
    webhookDialog.value.loading = false
  }
}

async function deleteWebhook(hook) {
  try {
    await axios.delete(`/api/integrations/webhooks/${hook.id}`)
    await fetchIntegrations()
    showNotification('Webhook supprimé')
  } catch (e) {
    showNotification(e.response?.data?.detail || 'Erreur webhook', 'error')
  }
}

async function testWebhook(hook) {
  try {
    await axios.post(`/api/integrations/webhooks/${hook.id}/test`)
    showNotification('Webhook testé')
  } catch (e) {
    showNotification(e.response?.data?.detail || 'Erreur test', 'error')
  }
}

function openExportDialog() {
  exportDialog.value = {
    show: true,
    name: '',
    resource: 'alerts',
    format: 'csv',
    interval_minutes: 1440,
    time_window_hours: 24,
    target: 'file',
    webhook_id: null,
    is_active: true,
    loading: false
  }
}

async function saveExport() {
  exportDialog.value.loading = true
  try {
    await axios.post('/api/integrations/exports', {
      name: exportDialog.value.name,
      resource: exportDialog.value.resource,
      format: exportDialog.value.format,
      interval_minutes: exportDialog.value.interval_minutes,
      time_window_hours: exportDialog.value.time_window_hours,
      target: exportDialog.value.target,
      webhook_id: exportDialog.value.target === 'webhook' ? exportDialog.value.webhook_id : null,
      is_active: exportDialog.value.is_active
    })
    await fetchIntegrations()
    exportDialog.value.show = false
    showNotification('Export créé')
  } catch (e) {
    showNotification(e.response?.data?.detail || 'Erreur export', 'error')
  } finally {
    exportDialog.value.loading = false
  }
}

async function deleteExport(exp) {
  try {
    await axios.delete(`/api/integrations/exports/${exp.id}`)
    await fetchIntegrations()
    showNotification('Export supprimé')
  } catch (e) {
    showNotification(e.response?.data?.detail || 'Erreur export', 'error')
  }
}

async function runExport(exp) {
  try {
    await axios.post(`/api/integrations/exports/${exp.id}/run`)
    showNotification('Export lancé')
  } catch (e) {
    showNotification(e.response?.data?.detail || 'Erreur export', 'error')
  }
}

async function fetchBackups() {
  try {
    const res = await axios.get('/api/backups')
    backups.value = res.data
  } catch (e) {
    console.error('Failed to fetch backups:', e)
  }
}

async function runBackup() {
  backupRunning.value = true
  try {
    await axios.post('/api/backups/run')
    await fetchBackups()
    showNotification('Backup créé avec succès')
  } catch (e) {
    showNotification(e.response?.data?.detail || 'Erreur lors du backup', 'error')
  } finally {
    backupRunning.value = false
  }
}

function openRestoreDialog(backup) {
  restoreDialog.value = { show: true, backup, loading: false }
}

async function confirmRestore() {
  if (!restoreDialog.value.backup?.name) return
  restoreDialog.value.loading = true
  try {
    await axios.post(`/api/backups/restore/${restoreDialog.value.backup.name}`, null, {
      params: { confirm: true }
    })
    restoreDialog.value.show = false
    showNotification('Restauration terminée')
  } catch (e) {
    showNotification(e.response?.data?.detail || 'Erreur restauration', 'error')
  } finally {
    restoreDialog.value.loading = false
  }
}

function openEditDialog(user) {
  editDialog.value = {
    show: true,
    user,
    first_name: user.first_name,
    last_name: user.last_name,
    department: user.department,
    loading: false
  }
}

async function saveUser() {
  editDialog.value.loading = true
  try {
    await axios.put(`/api/auth/users/${editDialog.value.user.id}`, {
      first_name: editDialog.value.first_name,
      last_name: editDialog.value.last_name,
      department: editDialog.value.department
    })
    await fetchData()
    editDialog.value.show = false
    showNotification('Utilisateur modifié avec succès')
  } catch (e) {
    showNotification(e.response?.data?.detail || 'Erreur', 'error')
  } finally {
    editDialog.value.loading = false
  }
}

function openRoleDialog(user) {
  roleDialog.value = {
    show: true,
    user,
    selectedRole: user.role,
    loading: false
  }
}

async function saveRole() {
  roleDialog.value.loading = true
  try {
    await axios.put(`/api/auth/users/${roleDialog.value.user.id}/role`, {
      role: roleDialog.value.selectedRole
    })
    await fetchData()
    roleDialog.value.show = false
    showNotification('Rôle modifié avec succès')
  } catch (e) {
    showNotification(e.response?.data?.detail || 'Erreur', 'error')
  } finally {
    roleDialog.value.loading = false
  }
}

async function toggleUserStatus(user) {
  try {
    await axios.put(`/api/auth/users/${user.id}`, {
      is_active: !user.is_active
    })
    await fetchData()
    showNotification(user.is_active ? 'Utilisateur désactivé' : 'Utilisateur activé')
  } catch (e) {
    showNotification(e.response?.data?.detail || 'Erreur', 'error')
  }
}

function confirmDelete(user) {
  deleteDialog.value = {
    show: true,
    user,
    loading: false
  }
}

async function deleteUser() {
  deleteDialog.value.loading = true
  try {
    await axios.delete(`/api/auth/users/${deleteDialog.value.user.id}`)
    await fetchData()
    deleteDialog.value.show = false
    showNotification('Utilisateur supprimé')
  } catch (e) {
    showNotification(e.response?.data?.detail || 'Erreur', 'error')
  } finally {
    deleteDialog.value.loading = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped lang="scss">
.admin-view {
  max-width: 1600px;
  margin: 0 auto;
}

// Hero Header
.admin-hero {
  position: relative;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 50%, #b91c1c 100%);
  border-radius: 24px;
  padding: 48px;
  overflow: hidden;
}

.hero-content {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 24px;
}

.hero-icon {
  width: 96px;
  height: 96px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.hero-text {
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

// Stat Cards
.stat-card {
  border-radius: 16px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  }
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 800;
  line-height: 1;
}

.stat-label {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-top: 4px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-total .stat-icon { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
.stat-active .stat-icon { background: rgba(16, 185, 129, 0.15); color: #10b981; }
.stat-admins .stat-icon { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
.stat-inactive .stat-icon { background: rgba(107, 114, 128, 0.15); color: #6b7280; }

.stat-trend {
  display: flex;
  align-items: center;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

// Users Card
.users-card {
  border-radius: 16px;
}

.search-field {
  :deep(.v-field) {
    border-radius: 12px;
  }
}

.users-table {
  :deep(th) {
    font-weight: 600 !important;
    text-transform: uppercase;
    font-size: 0.75rem !important;
    letter-spacing: 0.5px;
  }
}

// Roles Card
.roles-card {
  border-radius: 16px;
}

// Backup Card
.backup-card {
  border-radius: 16px;
}

.backup-item {
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.05);
  &:last-child {
    border-bottom: none;
  }
}

.webhook-card,
.export-card {
  border-radius: 16px;
}

.webhook-item,
.export-item {
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.05);
  &:last-child {
    border-bottom: none;
  }
}

.roles-list {
  .role-item {
    border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.05);
    
    &:last-child {
      border-bottom: none;
    }
  }
}

// Activity Card
.activity-card {
  border-radius: 16px;
}

.activity-list {
  .activity-item {
    border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.05);
    
    &:last-child {
      border-bottom: none;
    }
  }
}

// Dialogs
.edit-dialog,
.role-dialog,
.delete-dialog {
  border-radius: 20px;
  overflow: hidden;
}

.role-option {
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 12px !important;
  
  &:hover {
    transform: scale(1.02);
  }
}
</style>
