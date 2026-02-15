<template>
  <div class="min-h-screen bg-gray-50 font-sans text-[#202122]">
    <Navbar />

    <div class="pt-20 px-4 sm:px-6 lg:px-8">
      <div class="max-w-5xl mx-auto">
        <!-- Header -->
        <div class="mb-8">
          <h1 class="text-3xl font-bold text-gray-900 mb-2">Project & Language Watchlist</h1>
          <p class="text-gray-600">
            Add projects or languages to your watchlist to receive email notifications when activity peaks are detected.
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
            Please log in to manage your watchlist.
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
          <!-- Add Project to Watchlist -->
          <div class="codex-card p-6">
            <h2 class="text-xl font-bold text-gray-900 mb-4">Add Project to Watchlist</h2>
            
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Project URL
                </label>
                <cdx-text-input
                  v-model="newWatch.project"
                  placeholder="e.g., hi.wikibooks.org"
                  :disabled="watching"
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
                  v-model="newWatch.notificationType"
                  name="notification-type"
                  input-value="both"
                  :disabled="watching"
                >
                  Both (Edit & Editor peaks)
                </cdx-radio>
                <cdx-radio
                  v-model="newWatch.notificationType"
                  name="notification-type"
                  input-value="edit"
                  :disabled="watching"
                >
                  Edit peaks only
                </cdx-radio>
                <cdx-radio
                  v-model="newWatch.notificationType"
                  name="notification-type"
                  input-value="editor"
                  :disabled="watching"
                >
                  Editor peaks only
                </cdx-radio>
              </div>

              <cdx-button
                action="progressive"
                weight="primary"
                @click="addWatch"
                :disabled="!newWatch.project || watching"
              >
                <template #icon>
                  <cdx-icon :icon="cdxIconAdd" />
                </template>
                {{ watching ? 'Adding...' : 'Add to Watchlist' }}
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

          <!-- Add Language to Watchlist -->
          <div class="codex-card p-6">
            <h2 class="text-xl font-bold text-gray-900 mb-4">Add Language to Watchlist</h2>
            
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Language Code
                </label>
                <cdx-text-input
                  v-model="newLanguageWatch.languageCode"
                  placeholder="e.g., en, hi, fr"
                  :disabled="watchingLanguage"
                />
                <p class="text-xs text-gray-500 mt-1">
                  Enter a language code to add all projects in that language to your watchlist (e.g., en for English, hi for Hindi)
                </p>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Notification Type
                </label>
                <cdx-radio
                  v-model="newLanguageWatch.notificationType"
                  name="language-notification-type"
                  input-value="both"
                  :disabled="watchingLanguage"
                >
                  Both (Edit & Editor peaks)
                </cdx-radio>
                <cdx-radio
                  v-model="newLanguageWatch.notificationType"
                  name="language-notification-type"
                  input-value="edit"
                  :disabled="watchingLanguage"
                >
                  Edit peaks only
                </cdx-radio>
                <cdx-radio
                  v-model="newLanguageWatch.notificationType"
                  name="language-notification-type"
                  input-value="editor"
                  :disabled="watchingLanguage"
                >
                  Editor peaks only
                </cdx-radio>
              </div>

              <cdx-button
                action="progressive"
                weight="primary"
                @click="addLanguageWatch"
                :disabled="!newLanguageWatch.languageCode || watchingLanguage"
              >
                <template #icon>
                  <cdx-icon :icon="cdxIconAdd" />
                </template>
                {{ watchingLanguage ? 'Adding...' : 'Add to Watchlist' }}
              </cdx-button>
            </div>
          </div>

          <!-- Project Watchlist -->
          <div class="codex-card p-6">
            <h2 class="text-xl font-bold text-gray-900 mb-4">Your Project Watchlist</h2>

            <div v-if="projectWatchlist.length === 0" class="text-center py-8 text-gray-500">
              <cdx-icon :icon="cdxIconBell" class="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>You don't have any projects in your watchlist yet.</p>
              <p class="text-sm mt-1">Add projects above to get started.</p>
            </div>

            <div v-else class="space-y-3">
              <div
                v-for="item in projectWatchlist"
                :key="item.project"
                class="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-1">
                    <cdx-icon :icon="cdxIconArticle" class="text-gray-500" />
                    <h3 class="font-semibold text-gray-900">{{ item.project }}</h3>
                    <span
                      v-if="!item.is_active"
                      class="px-2 py-0.5 text-xs bg-gray-200 text-gray-600 rounded"
                    >
                      Inactive
                    </span>
                  </div>
                  <p class="text-sm text-gray-600">
                    Notification type: 
                    <span class="font-medium">{{ formatNotificationType(item.notification_type) }}</span>
                  </p>
                  <p class="text-xs text-gray-500 mt-1">
                    Added {{ formatDate(item.created_at) }}
                  </p>
                </div>

                <div class="flex items-center gap-2">
                  <cdx-button
                    v-if="item.is_active"
                    action="destructive"
                    weight="quiet"
                    @click="removeProject(item.project)"
                    :disabled="removingProject === item.project"
                  >
                    <template #icon>
                      <cdx-icon :icon="cdxIconTrash" />
                    </template>
                    {{ removingProject === item.project ? 'Removing...' : 'Remove' }}
                  </cdx-button>
                </div>
              </div>
            </div>
          </div>

          <!-- Language Watchlist -->
          <div class="codex-card p-6">
            <h2 class="text-xl font-bold text-gray-900 mb-4">Your Language Watchlist</h2>

            <div v-if="languageWatchlist.length === 0" class="text-center py-8 text-gray-500">
              <cdx-icon :icon="cdxIconBell" class="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>You don't have any languages in your watchlist yet.</p>
              <p class="text-sm mt-1">Add a language to receive notifications for all projects in that language.</p>
            </div>

            <div v-else class="space-y-3">
              <div
                v-for="item in languageWatchlist"
                :key="item.language_code"
                class="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-1">
                    <cdx-icon :icon="cdxIconLanguage" class="text-gray-500" />
                    <h3 class="font-semibold text-gray-900" style="text-transform: none;">{{ getLanguageName(item.language_code) }} (All Projects)</h3>
                    <span
                      v-if="!item.is_active"
                      class="px-2 py-0.5 text-xs bg-gray-200 text-gray-600 rounded"
                    >
                      Inactive
                    </span>
                  </div>
                  <p class="text-sm text-gray-600">
                    Notification type: 
                    <span class="font-medium">{{ formatNotificationType(item.notification_type) }}</span>
                  </p>
                  <p class="text-xs text-gray-500 mt-1">
                    Added {{ formatDate(item.created_at) }}
                  </p>
                </div>

                <div class="flex items-center gap-2">
                  <cdx-button
                    v-if="item.is_active"
                    action="destructive"
                    weight="quiet"
                    @click="removeLanguage(item.language_code)"
                    :disabled="removingLanguage === item.language_code"
                  >
                    <template #icon>
                      <cdx-icon :icon="cdxIconTrash" />
                    </template>
                    {{ removingLanguage === item.language_code ? 'Removing...' : 'Remove' }}
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
  cdxIconInfo,
  cdxIconLanguage
} from '@wikimedia/codex-icons'
import Navbar from '../components/Navbar.vue'

const auth = useAuthStore()

const loading = ref(false)
const error = ref(null)
const projectWatchlist = ref([])
const languageWatchlist = ref([])
const watching = ref(false)
const watchingLanguage = ref(false)
const removingProject = ref(null)
const removingLanguage = ref(null)
const successMessage = ref('')

const newWatch = ref({
  project: '',
  notificationType: 'both'
})

const newLanguageWatch = ref({
  languageCode: '',
  notificationType: 'both'
})

// Language code to name mapping
const languageNames = {
  'en': 'English',
  'hi': 'Hindi',
  'es': 'Spanish',
  'fr': 'French',
  'de': 'German',
  'it': 'Italian',
  'pt': 'Portuguese',
  'ru': 'Russian',
  'ja': 'Japanese',
  'zh': 'Chinese',
  'ar': 'Arabic',
  'bn': 'Bengali',
  'pa': 'Punjabi',
  'te': 'Telugu',
  'mr': 'Marathi',
  'ta': 'Tamil',
  'ur': 'Urdu',
  'gu': 'Gujarati',
  'kn': 'Kannada',
  'ml': 'Malayalam',
  'or': 'Odia',
  'as': 'Assamese',
  'ne': 'Nepali',
  'si': 'Sinhala',
  'sa': 'Sanskrit',
  'ko': 'Korean',
  'vi': 'Vietnamese',
  'th': 'Thai',
  'id': 'Indonesian',
  'ms': 'Malay',
  'nl': 'Dutch',
  'pl': 'Polish',
  'tr': 'Turkish',
  'uk': 'Ukrainian',
  'sv': 'Swedish',
  'no': 'Norwegian',
  'da': 'Danish',
  'fi': 'Finnish',
  'cs': 'Czech',
  'hu': 'Hungarian',
  'ro': 'Romanian',
  'el': 'Greek',
  'he': 'Hebrew',
  'fa': 'Persian',
  'ca': 'Catalan',
  'sr': 'Serbian',
  'hr': 'Croatian',
  'bg': 'Bulgarian',
  'sk': 'Slovak',
  'lt': 'Lithuanian',
  'lv': 'Latvian',
  'et': 'Estonian',
  'sl': 'Slovenian',
  'mk': 'Macedonian',
  'sq': 'Albanian',
  'az': 'Azerbaijani',
  'hy': 'Armenian',
  'ka': 'Georgian',
  'eu': 'Basque',
  'gl': 'Galician',
  'cy': 'Welsh',
  'ga': 'Irish',
  'is': 'Icelandic',
  'af': 'Afrikaans',
  'sw': 'Swahili',
  'zu': 'Zulu',
  'xh': 'Xhosa'
}

const getLanguageName = (code) => {
  const normalizedCode = code.toLowerCase()
  return languageNames[normalizedCode] || code.charAt(0).toUpperCase() + code.slice(1).toLowerCase()
}

const fetchWatchlist = async () => {
  if (!auth.isAuthenticated) return

  loading.value = true
  error.value = null

  try {
    const [projectResponse, languageResponse] = await Promise.all([
      axios.get(
        `${import.meta.env.VITE_BACKEND_URL}/api/watchlist/project-watchlist`,
        { withCredentials: true }
      ),
      axios.get(
        `${import.meta.env.VITE_BACKEND_URL}/api/watchlist/language-watchlist`,
        { withCredentials: true }
      )
    ])

    if (projectResponse.data.success) {
      projectWatchlist.value = projectResponse.data.watchlist
    }
    if (languageResponse.data.success) {
      languageWatchlist.value = languageResponse.data.language_watchlist
    }
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to load watchlist'
    console.error('Error fetching watchlist:', err)
  } finally {
    loading.value = false
  }
}

const addWatch = async () => {
  if (!newWatch.value.project) return

  watching.value = true
  error.value = null

  try {
    const response = await axios.post(
      `${import.meta.env.VITE_BACKEND_URL}/api/watchlist/add-project`,
      {
        project: newWatch.value.project,
        notification_type: newWatch.value.notificationType
      },
      { withCredentials: true }
    )

    if (response.data.success) {
      successMessage.value = `Successfully added ${newWatch.value.project} to watchlist`
      newWatch.value.project = ''
      newWatch.value.notificationType = 'both'
      await fetchWatchlist()
      
      setTimeout(() => {
        successMessage.value = ''
      }, 5000)
    }
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to add project to watchlist'
    console.error('Error adding project to watchlist:', err)
  } finally {
    watching.value = false
  }
}

const addLanguageWatch = async () => {
  if (!newLanguageWatch.value.languageCode) return

  watchingLanguage.value = true
  error.value = null

  try {
    const response = await axios.post(
      `${import.meta.env.VITE_BACKEND_URL}/api/watchlist/add-language`,
      {
        language_code: newLanguageWatch.value.languageCode.toLowerCase(),
        notification_type: newLanguageWatch.value.notificationType
      },
      { withCredentials: true }
    )

    if (response.data.success) {
      successMessage.value = `Successfully added ${getLanguageName(newLanguageWatch.value.languageCode)} to language watchlist`
      newLanguageWatch.value.languageCode = ''
      newLanguageWatch.value.notificationType = 'both'
      await fetchWatchlist()
      
      setTimeout(() => {
        successMessage.value = ''
      }, 5000)
    }
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to add language to watchlist'
    console.error('Error adding language to watchlist:', err)
  } finally {
    watchingLanguage.value = false
  }
}

const removeProject = async (project) => {
  if (!confirm(`Are you sure you want to remove ${project} from your watchlist?`)) return

  removingProject.value = project
  error.value = null

  try {
    const response = await axios.post(
      `${import.meta.env.VITE_BACKEND_URL}/api/watchlist/remove-project`,
      { project },
      { withCredentials: true }
    )

    if (response.data.success) {
      successMessage.value = `Successfully removed ${project} from watchlist`
      await fetchWatchlist()
      
      setTimeout(() => {
        successMessage.value = ''
      }, 5000)
    }
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to remove project from watchlist'
    console.error('Error removing project from watchlist:', err)
  } finally {
    removingProject.value = null
  }
}

const removeLanguage = async (languageCode) => {
  if (!confirm(`Are you sure you want to remove ${getLanguageName(languageCode)} from your language watchlist?`)) return

  removingLanguage.value = languageCode
  error.value = null

  try {
    const response = await axios.post(
      `${import.meta.env.VITE_BACKEND_URL}/api/watchlist/remove-language`,
      { language_code: languageCode },
      { withCredentials: true }
    )

    if (response.data.success) {
      successMessage.value = `Successfully removed ${getLanguageName(languageCode)} from language watchlist`
      await fetchWatchlist()
      
      setTimeout(() => {
        successMessage.value = ''
      }, 5000)
    }
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to remove language from watchlist'
    console.error('Error removing language from watchlist:', err)
  } finally {
    removingLanguage.value = null
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
    await fetchWatchlist()
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
