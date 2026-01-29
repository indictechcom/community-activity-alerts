<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center">
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-gray-200">
        <h2 class="text-xl font-bold text-gray-900">Add Annotation</h2>
        <button @click="close" class="text-gray-400 hover:text-gray-600">
          <cdx-icon :icon="cdxIconClose" size="medium" />
        </button>
      </div>

      <!-- Body -->
      <div class="p-6">
        <!-- Peak Info -->
        <div class="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div class="flex items-center gap-2 mb-2">
            <cdx-icon :icon="cdxIconInfoFilled" size="small" class="text-blue-600" />
            <span class="font-semibold text-gray-900">Peak Information</span>
          </div>
          <div class="text-sm text-gray-700">
            <p><strong>Project:</strong> {{ peakData.project }}</p>
            <p><strong>Date:</strong> {{ formatDate(peakData.timestamp) }}</p>
            <p><strong>Type:</strong> {{ peakData.peak_type === 'edit' ? 'Edit Count' : 'Editor Count' }}</p>
          </div>
        </div>

        <!-- Description Field -->
        <div class="mb-4">
          <label class="block text-sm font-semibold text-gray-900 mb-2">
            Description <span class="text-red-600">*</span>
          </label>
          <textarea
            v-model="description"
            @input="updateWordCount"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            rows="4"
            maxlength="500"
            placeholder="Provide context about this spike (max 50 words)"
          ></textarea>
          <div class="flex justify-between items-center mt-1">
            <p class="text-xs text-gray-500">
              Briefly explain what caused this spike or provide relevant context.
            </p>
            <span 
              class="text-xs font-medium"
              :class="wordCount > 50 ? 'text-red-600' : 'text-gray-500'"
            >
              {{ wordCount }} / 50 words
            </span>
          </div>
        </div>

        <!-- Link Field -->
        <div class="mb-4">
          <label class="block text-sm font-semibold text-gray-900 mb-2">
            Relevant Link (Optional)
          </label>
          <input
            v-model="relevantLink"
            type="url"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="https://example.com/relevant-page"
          />
          <p class="text-xs text-gray-500 mt-1">
            Add a link to a relevant discussion, event page, or documentation.
          </p>
        </div>

        <!-- Requirements Notice -->
        <div class="mb-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
          <div class="flex items-start gap-2">
            <cdx-icon :icon="cdxIconAlert" size="small" class="text-yellow-600 mt-0.5" />
            <div class="text-sm text-gray-700">
              <p class="font-semibold mb-1">Requirements:</p>
              <ul class="list-disc list-inside space-y-1">
                <li>You must be logged in with your Wikimedia account</li>
                <li>Minimum 1,000 global edits required</li>
                <li>Annotations will be reviewed before being displayed</li>
              </ul>
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
          @click="submitAnnotation"
          class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="!canSubmit || isSubmitting"
        >
          {{ isSubmitting ? 'Submitting...' : 'Submit for Review' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { CdxIcon } from '@wikimedia/codex'
import { cdxIconClose, cdxIconInfoFilled, cdxIconAlert, cdxIconError, cdxIconCheck } from '@wikimedia/codex-icons'
import axios from 'axios'

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  },
  peakData: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'success'])

const description = ref('')
const relevantLink = ref('')
const wordCount = ref(0)
const errorMessage = ref('')
const successMessage = ref('')
const isSubmitting = ref(false)

const updateWordCount = () => {
  const text = description.value.trim()
  wordCount.value = text ? text.split(/\s+/).length : 0
}

const canSubmit = computed(() => {
  return description.value.trim().length >= 10 && 
         wordCount.value > 0 && 
         wordCount.value <= 50 &&
         !isSubmitting.value
})

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const submitAnnotation = async () => {
  errorMessage.value = ''
  successMessage.value = ''
  
  if (!canSubmit.value) {
    errorMessage.value = 'Please check all requirements before submitting.'
    return
  }

  isSubmitting.value = true

  try {
    const apiUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000'
    
    const response = await axios.post(
      `${apiUrl}/api/annotations/submit`,
      {
        project: props.peakData.project,
        timestamp: props.peakData.timestamp,
        peak_type: props.peakData.peak_type,
        description: description.value.trim(),
        relevant_link: relevantLink.value.trim() || null
      },
      {
        withCredentials: true
      }
    )

    if (response.data.success) {
      successMessage.value = 'Annotation submitted successfully! It will be reviewed shortly.'
      
      // Clear form
      description.value = ''
      relevantLink.value = ''
      wordCount.value = 0
      
      // Emit success event
      emit('success')
      
      // Close modal after 2 seconds
      setTimeout(() => {
        close()
      }, 2000)
    }
  } catch (error) {
    if (error.response) {
      errorMessage.value = error.response.data.error || 'Failed to submit annotation.'
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
    description.value = ''
    relevantLink.value = ''
    wordCount.value = 0
    errorMessage.value = ''
    successMessage.value = ''
    emit('close')
  }
}

// Reset form when modal opens
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    description.value = ''
    relevantLink.value = ''
    wordCount.value = 0
    errorMessage.value = ''
    successMessage.value = ''
  }
})
</script>

<style scoped>
/* Ensure modal appears above other content */
.fixed {
  position: fixed;
}
</style>
