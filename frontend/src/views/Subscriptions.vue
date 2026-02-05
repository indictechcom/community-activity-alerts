<template>
  <div class="min-h-screen bg-gray-50 font-sans text-[#202122]">
    <Navbar />

    <div class="pt-20 px-4 sm:px-6 lg:px-8">
      <div class="max-w-5xl mx-auto">
        <!-- Header -->
        <div class="mb-8">
          <h1 class="text-3xl font-bold text-gray-900 mb-2">Notification Subscriptions</h1>
          <p class="text-gray-600">
            Subscribe to projects to receive email notifications when activity peaks are detected.
          </p>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="flex justify-center items-center py-12">
          <div class="w-12 h-12 border-4 border-[#eaf3ff] border-t-[#36c] rounded-full animate-spin"></div>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="codex-card p-6 border-t-4 border-t-[#d33] mb-6">
          <div class="flex items-start gap-3">
            <cdx-icon :icon="cdxIconError" class="text-[#d33] mt-1" />
            <div>
              <h3 class="font-bold text-gray-900 mb-1">Error Loading Subscriptions</h3>
              <p class="text-gray-600">{{ error }}</p>
            </div>
          </div>
        </div>

        <!-- Not Authenticated -->
        <div v-else-if="!auth.isAuthenticated" class="codex-card p-8 text-center">
          <div class="inline-flex p-4 rounded-full bg-[#eaf3ff] text-[#36c] mb-4">
            <cdx-icon :icon="cdxIconUserAvatar" class="w-12 h-12" />
          </div>
          <h2 class="text-xl font-bold text-gray-900 mb-2">Authentication Required</h2>
          <p class="text-gray-600 mb-6">
            Please log in to manage your notification subscriptions.
          </p>
          <cdx-button action="progressive" weight="primary" @click="auth.login">
            <template #icon>
              <cdx-icon :icon="cdxIconLogIn" />
            </template>
            Login with Wikimedia
          </cdx-button>
        </div>

        <!-- Subscriptions List -->
        <div v-else class="space-y-6">
          <!-- Add New Subscription -->
          <div class="codex-card p-6">
            <h2 class="text-xl font-bold text-gray-900 mb-4">Add New Subscription</h2>
            
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Project URL
                </label>
                <cdx-text-input
                  v-model="newSubscription.project"
                  placeholder="e.g., hi.wikibooks.org"
                  :disabled="subscribing"
                />
                <p class="text-xs text-gray-500 mt-1">
                  Enter the project URL (e.g., en.wikipedia.org, hi.wikibooks.org)
                </p>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Notification Type
                </label>
                <cdx-radio
                  v-model="newSubscription.notificationType"
                  name="notification-type"
                  input-value="both"
                  :disabled="subscribing"
                >
                  Both (Edit & Editor peaks)
                </cdx-radio>
                <cdx-radio
                  v-model="newSubscription.notificationType"
                  name="notification-type"
                  input-value="edit"
                  :disabled="subscribing"
                >
                  Edit peaks only
                </cdx-radio>
                <cdx-radio
                  v-model="newSubscription.notificationType"
                  name="notification-type"
                  input-value="editor"
                  :disabled="subscribing"
                >
                  Editor peaks only
                </cdx-radio>
              </div>

              <cdx-button
                action="progressive"
                weight="primary"
                @click="addSubscription"
                :disabled="!newSubscription.project || subscribing"
              >
                <template #icon>
                  <cdx-icon :icon="cdxIconAdd" />
                </template>
                {{ subscribing ? 'Subscribing...' : 'Subscribe' }}
              </cdx-button>
            </div>
          </div>

          <!-- Success Message -->
          <cdx-message
            v-if="successMessage"
            type="success"
            :fade-in="true"
            @user-dismissed="successMessage = ''"
          >
            {{ successMessage }}
          </cdx-message>

          <!-- Current Subscriptions -->
          <div class="codex-card p-6">
            <h2 class="text-xl font-bold text-gray-900 mb-4">Your Subscriptions</h2>

            <div v-if="subscriptions.length === 0" class="text-center py-8 text-gray-500">
              <cdx-icon :icon="cdxIconBell" class="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>You don't have any subscriptions yet.</p>
              <p class="text-sm mt-1">Subscribe to projects above to get started.</p>
            </div>

            <div v-else class="space-y-3">
              <div
                v-for="sub in subscriptions"
                :key="sub.project"
                class="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-1">
                    <cdx-icon :icon="cdxIconArticle" class="text-gray-500" />
                    <h3 class="font-semibold text-gray-900">{{ sub.project }}</h3>
                    <span
                      v-if="!sub.is_active"
                      class="px-2 py-0.5 text-xs bg-gray-200 text-gray-600 rounded"
                    >
                      Inactive
                    </span>
                  </div>
                  <p class="text-sm text-gray-600">
                    Notification type: 
                    <span class="font-medium">{{ formatNotificationType(sub.notification_type) }}</span>
                  </p>
                  <p class="text-xs text-gray-500 mt-1">
                    Subscribed on {{ formatDate(sub.created_at) }}
                  </p>
                </div>

                <div class="flex items-center gap-2">
                  <cdx-button
                    v-if="sub.is_active"
                    action="destructive"
                    weight="quiet"
                    @click="unsubscribe(sub.project)"
                    :disabled="unsubscribing === sub.project"
                  >
                    <template #icon>
                      <cdx-icon :icon="cdxIconTrash" />
                    </template>
                    {{ unsubscribing === sub.project ? 'Removing...' : 'Unsubscribe' }}
                  </cdx-button>
                </div>
              </div>
            </div>
          </div>

          <!-- Information Box -->
          <div class="codex-card p-6 bg-blue-50 border-l-4 border-l-[#36c]">
            <div class="flex gap-3">
              <cdx-icon :icon="cdxIconInfo" class="text-[#36c] mt-1" />
              <div class="text-sm text-gray-700">
                <h3 class="font-bold mb-2">How Notifications Work</h3>
                <ul class="space-y-1 list-disc list-inside">
                  <li>You'll receive email notifications when significant activity peaks are detected</li>
                  <li>Notifications are sent monthly for peaks detected in the last 31 days</li>
                  <li>Emails are sent via MediaWiki's email system to your registered email address</li>
                  <li>You can unsubscribe from any project at any time</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { CdxButton, CdxIcon, CdxTextInput, CdxRadio, CdxMessage } from '@wikimedia/codex'
import {
  cdxIconError,
  cdxIconUserAvatar,
  cdxIconLogIn,
  cdxIconAdd,
  cdxIconBell,
  cdxIconArticle,
  cdxIconTrash,
  cdxIconInfo
} from '@wikimedia/codex-icons'
import Navbar from '../components/Navbar.vue'

const auth = useAuthStore()

const loading = ref(false)
const error = ref(null)
const subscriptions = ref([])
const subscribing = ref(false)
const unsubscribing = ref(null)
const successMessage = ref('')

const newSubscription = ref({
  project: '',
  notificationType: 'both'
})

const fetchSubscriptions = async () => {
  if (!auth.isAuthenticated) return

  loading.value = true
  error.value = null

  try {
    const response = await axios.get(
      `${import.meta.env.VITE_BACKEND_URL}/api/subscriptions/my-subscriptions`,
      { withCredentials: true }
    )

    if (response.data.success) {
      subscriptions.value = response.data.subscriptions
    }
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to load subscriptions'
    console.error('Error fetching subscriptions:', err)
  } finally {
    loading.value = false
  }
}

const addSubscription = async () => {
  if (!newSubscription.value.project) return

  subscribing.value = true
  error.value = null

  try {
    const response = await axios.post(
      `${import.meta.env.VITE_BACKEND_URL}/api/subscriptions/subscribe`,
      {
        project: newSubscription.value.project,
        notification_type: newSubscription.value.notificationType
      },
      { withCredentials: true }
    )

    if (response.data.success) {
      successMessage.value = `Successfully subscribed to ${newSubscription.value.project}`
      newSubscription.value.project = ''
      newSubscription.value.notificationType = 'both'
      await fetchSubscriptions()
      
      setTimeout(() => {
        successMessage.value = ''
      }, 5000)
    }
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to add subscription'
    console.error('Error adding subscription:', err)
  } finally {
    subscribing.value = false
  }
}

const unsubscribe = async (project) => {
  if (!confirm(`Are you sure you want to unsubscribe from ${project}?`)) return

  unsubscribing.value = project
  error.value = null

  try {
    const response = await axios.post(
      `${import.meta.env.VITE_BACKEND_URL}/api/subscriptions/unsubscribe`,
      { project },
      { withCredentials: true }
    )

    if (response.data.success) {
      successMessage.value = `Successfully unsubscribed from ${project}`
      await fetchSubscriptions()
      
      setTimeout(() => {
        successMessage.value = ''
      }, 5000)
    }
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to unsubscribe'
    console.error('Error unsubscribing:', err)
  } finally {
    unsubscribing.value = null
  }
}

const formatNotificationType = (type) => {
  const types = {
    both: 'Edit & Editor peaks',
    edit: 'Edit peaks only',
    editor: 'Editor peaks only'
  }
  return types[type] || type
}

const formatDate = (dateString) => {
  if (!dateString) return 'Unknown'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

onMounted(async () => {
  await auth.fetchUser()
  if (auth.isAuthenticated) {
    await fetchSubscriptions()
  }
})
</script>

<style scoped>
.codex-card {
  background-color: var(--background-color-base, #ffffff);
  border: 1px solid var(--border-color-subtle, #c8ccd1);
  border-radius: 2px;
}

.animate-fade-in {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
