<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-gray-200">
        <h2 class="text-xl font-bold text-gray-900">Report Annotation</h2>
        <button @click="close" class="text-gray-400 hover:text-gray-600">
          <cdx-icon :icon="cdxIconClose" size="medium" />
        </button>
      </div>

      <!-- Body -->
      <div class="p-6">
        <!-- Annotation Info -->
        <div class="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div class="flex items-center gap-2 mb-2">
            <cdx-icon :icon="cdxIconInfoFilled" size="small" class="text-gray-600" />
            <span class="font-semibold text-gray-900">Current Annotation</span>
          </div>
          <div class="text-sm text-gray-700">
            <p class="mb-2">{{ annotationData.annotation?.description }}</p>
            <p class="text-xs text-gray-500">by {{ annotationData.annotation?.submitted_by }}</p>
          </div>
        </div>

        <!-- Report Reason Field -->
        <div class="mb-4">
          <label class="block text-sm font-semibold text-gray-900 mb-2">
            Reason for Report <span class="text-red-600">*</span>
          </label>
          <textarea
            v-model="reportReason"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            rows="4"
            placeholder="Explain why this annotation should be reviewed (minimum 10 characters)"
          ></textarea>
          <p class="text-xs text-gray-500 mt-1">
            Describe the issue with this annotation (e.g., inaccurate, spam, inappropriate).
          </p>
        </div>

        <!-- Info Notice -->
        <div class="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div class="flex items-start gap-2">
            <cdx-icon :icon="cdxIconInfoFilled" size="small" class="text-blue-600 mt-0.5" />
            <div class="text-sm text-gray-700">
              <p class="font-semibold mb-1">What happens next:</p>
              <ul class="list-disc list-inside space-y-1">
                <li>Reviewers will be notified of your report</li>
                <li>They will review the annotation and take appropriate action</li>
                <li>The annotation may be edited or removed if necessary</li>
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
          @click="submitReport"
          class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="!canSubmit || isSubmitting"
        >
          {{ isSubmitting ? 'Submitting...' : 'Submit Report' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { CdxIcon } from '@wikimedia/codex'
import { cdxIconClose, cdxIconInfoFilled, cdxIconError, cdxIconCheck } from '@wikimedia/codex-icons'
import axios from 'axios'

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  },
  annotationData: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'success'])

const reportReason = ref('')
const errorMessage = ref('')
const successMessage = ref('')
const isSubmitting = ref(false)

const canSubmit = computed(() => {
  return reportReason.value.trim().length >= 10 && !isSubmitting.value
})

const submitReport = async () => {
  errorMessage.value = ''
  successMessage.value = ''
  
  if (!canSubmit.value) {
    errorMessage.value = 'Please provide a reason for the report (minimum 10 characters).'
    return
  }

  isSubmitting.value = true

  try {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000'
    
    const response = await axios.post(
      `${apiUrl}/api/annotations/report`,
      {
        annotation_id: props.annotationData.annotation_id,
        report_reason: reportReason.value.trim()
      },
      {
        withCredentials: true
      }
    )

    if (response.data.success) {
      successMessage.value = 'Report submitted successfully! Reviewers will be notified.'
      
      reportReason.value = ''
      
      emit('success')
      
      setTimeout(() => {
        close()
      }, 2000)
    }
  } catch (error) {
    if (error.response) {
      errorMessage.value = error.response.data.error || 'Failed to submit report.'
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
    reportReason.value = ''
    errorMessage.value = ''
    successMessage.value = ''
    emit('close')
  }
}

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    reportReason.value = ''
    errorMessage.value = ''
    successMessage.value = ''
  }
})
</script>

<style scoped>
.fixed {
  position: fixed;
}
</style>
