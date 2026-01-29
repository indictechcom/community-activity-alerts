<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-md">
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-gray-200">
        <h2 class="text-xl font-bold text-gray-900">
          {{ action === 'dismiss' ? 'Dismiss Report' : action === 'edit' ? 'Edit Annotation' : 'Remove Annotation' }}
        </h2>
        <button @click="close" class="text-gray-400 hover:text-gray-600">
          <cdx-icon :icon="cdxIconClose" size="medium" />
        </button>
      </div>

      <!-- Body -->
      <div class="p-6">
        <!-- Report Info -->
        <div class="mb-6 p-4 bg-red-50 rounded-lg border border-red-200">
          <p class="text-sm font-semibold text-gray-900 mb-2">Report Reason:</p>
          <p class="text-sm text-gray-700">{{ report?.report_reason }}</p>
          <p class="text-xs text-gray-500 mt-2">
            Reported by {{ report?.reported_by }}
          </p>
        </div>

        <!-- Current Annotation -->
        <div class="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <p class="text-sm font-semibold text-gray-900 mb-2">Current Annotation:</p>
          <p class="text-sm text-gray-700 mb-2">{{ report?.annotation?.description }}</p>
          <p v-if="report?.annotation?.relevant_link" class="text-sm text-gray-700">
            <strong>Link:</strong> <a :href="report.annotation.relevant_link" target="_blank" class="text-blue-600 hover:underline">{{ report.annotation.relevant_link }}</a>
          </p>
        </div>

        <!-- Edit Fields (only for edit action) -->
        <div v-if="action === 'edit'" class="space-y-4 mb-6">
          <div>
            <label class="block text-sm font-semibold text-gray-900 mb-2">
              Edited Description <span class="text-red-600">*</span>
            </label>
            <textarea
              v-model="editedDescription"
              @input="updateWordCount"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows="4"
              maxlength="500"
            ></textarea>
            <div class="flex justify-between items-center mt-1">
              <p class="text-xs text-gray-500">Edit the description to address the report</p>
              <span 
                class="text-xs font-medium"
                :class="wordCount > 50 ? 'text-red-600' : 'text-gray-500'"
              >
                {{ wordCount }} / 50 words
              </span>
            </div>
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-900 mb-2">
              Edited Link (Optional)
            </label>
            <input
              v-model="editedLink"
              type="url"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        <!-- Action Confirmation -->
        <div v-if="action === 'remove'" class="mb-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
          <div class="flex items-start gap-2">
            <cdx-icon :icon="cdxIconAlert" size="small" class="text-yellow-600 mt-0.5" />
            <div class="text-sm text-gray-700">
              <p class="font-semibold mb-1">Warning:</p>
              <p>This will hide the annotation from public view. This action can be reversed later if needed.</p>
            </div>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="errorMessage" class="mb-4 p-4 bg-red-50 rounded-lg border border-red-200">
          <div class="flex items-start gap-2">
            <cdx-icon :icon="cdxIconError" size="small" class="text-red-600 mt-0.5" />
            <p class="text-sm text-red-700">{{ errorMessage }}</p>
          </div>
        </div>

        <!-- Success Message -->
        <div v-if="successMessage" class="mb-4 p-4 bg-green-50 rounded-lg border border-green-200">
          <div class="flex items-start gap-2">
            <cdx-icon :icon="cdxIconCheck" size="small" class="text-green-600 mt-0.5" />
            <p class="text-sm text-green-700">{{ successMessage }}</p>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50">
        <button
          @click="close"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          :disabled="isSubmitting"
        >
          Cancel
        </button>
        <button
          @click="submitReview"
          :class="[
            'px-4 py-2 text-sm font-medium text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed',
            action === 'dismiss' ? 'bg-gray-600 hover:bg-gray-700' :
            action === 'edit' ? 'bg-blue-600 hover:bg-blue-700' :
            'bg-red-600 hover:bg-red-700'
          ]"
          :disabled="!canSubmit || isSubmitting"
        >
          {{ isSubmitting ? 'Processing...' : action === 'dismiss' ? 'Dismiss Report' : action === 'edit' ? 'Save Changes' : 'Remove Annotation' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { CdxIcon } from '@wikimedia/codex'
import { cdxIconClose, cdxIconAlert, cdxIconError, cdxIconCheck } from '@wikimedia/codex-icons'
import axios from 'axios'

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  },
  report: {
    type: Object,
    default: null
  },
  action: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['close', 'success'])

const editedDescription = ref('')
const editedLink = ref('')
const wordCount = ref(0)
const errorMessage = ref('')
const successMessage = ref('')
const isSubmitting = ref(false)

const updateWordCount = () => {
  const text = editedDescription.value.trim()
  wordCount.value = text ? text.split(/\s+/).length : 0
}

const canSubmit = computed(() => {
  if (isSubmitting.value) return false
  if (props.action === 'edit') {
    return editedDescription.value.trim().length >= 10 && 
           wordCount.value > 0 && 
           wordCount.value <= 50
  }
  return true
})

const submitReview = async () => {
  errorMessage.value = ''
  successMessage.value = ''

  if (!canSubmit.value) {
    errorMessage.value = 'Please check all requirements before submitting.'
    return
  }

  isSubmitting.value = true

  try {
    const apiUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000'
    
    const payload = {
      report_id: props.report.report_id,
      action: props.action
    }

    if (props.action === 'edit') {
      payload.edited_description = editedDescription.value.trim()
      payload.edited_link = editedLink.value.trim() || null
    }

    const response = await axios.post(
      `${apiUrl}/api/annotations/reports/review`,
      payload,
      {
        withCredentials: true
      }
    )

    if (response.data.success) {
      successMessage.value = response.data.message
      emit('success')
      
      setTimeout(() => {
        close()
      }, 1500)
    }
  } catch (error) {
    if (error.response) {
      errorMessage.value = error.response.data.error || 'Failed to submit review.'
    } else if (error.request) {
      errorMessage.value = 'Network error. Please check your connection.'
    } else {
      errorMessage.value = 'An unexpected error occurred.'
    }
  } finally {
    isSubmitting.value = false
  }
}

const close = () => {
  if (!isSubmitting.value) {
    editedDescription.value = ''
    editedLink.value = ''
    wordCount.value = 0
    errorMessage.value = ''
    successMessage.value = ''
    emit('close')
  }
}

watch(() => props.isOpen, (newVal) => {
  if (newVal && props.report) {
    editedDescription.value = props.report.annotation?.description || ''
    editedLink.value = props.report.annotation?.relevant_link || ''
    errorMessage.value = ''
    successMessage.value = ''
    updateWordCount()
  }
})
</script>

<style scoped>
.fixed {
  position: fixed;
}
</style>
