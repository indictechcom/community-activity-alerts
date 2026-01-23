<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">Reviewer Dashboard</h1>
        <p class="mt-2 text-sm text-gray-600">
          Review and manage peak annotations and reports
        </p>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">Pending Annotations</p>
              <p class="text-3xl font-bold text-gray-900 mt-2">{{ stats.pending_annotations }}</p>
            </div>
            <cdx-icon :icon="cdxIconArticle" size="large" class="text-blue-500" />
          </div>
        </div>

        <div class="bg-white rounded-lg shadow p-6 border-l-4 border-yellow-500">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">Pending Reports</p>
              <p class="text-3xl font-bold text-gray-900 mt-2">{{ stats.pending_reports }}</p>
            </div>
            <cdx-icon :icon="cdxIconFlag" size="large" class="text-yellow-500" />
          </div>
        </div>

        <div class="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">Total Pending</p>
              <p class="text-3xl font-bold text-gray-900 mt-2">{{ stats.total_pending }}</p>
            </div>
            <cdx-icon :icon="cdxIconCheck" size="large" class="text-green-500" />
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="bg-white rounded-lg shadow mb-6">
        <div class="border-b border-gray-200">
          <nav class="flex -mb-px">
            <button
              @click="activeTab = 'annotations'"
              :class="[
                'px-6 py-4 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'annotations'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              Pending Annotations ({{ stats.pending_annotations }})
            </button>
            <button
              @click="activeTab = 'reports'"
              :class="[
                'px-6 py-4 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'reports'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              Pending Reports ({{ stats.pending_reports }})
            </button>
          </nav>
        </div>
      </div>

      <!-- Pending Annotations Tab -->
      <div v-if="activeTab === 'annotations'" class="space-y-4">
        <div v-if="loading" class="text-center py-12">
          <p class="text-gray-500">Loading annotations...</p>
        </div>

        <div v-else-if="pendingAnnotations.length === 0" class="bg-white rounded-lg shadow p-12 text-center">
          <cdx-icon :icon="cdxIconCheck" size="large" class="text-green-600 mx-auto mb-4" />
          <p class="text-lg font-semibold text-gray-900">All caught up!</p>
          <p class="text-sm text-gray-500 mt-2">No pending annotations to review.</p>
        </div>

        <div v-else v-for="annotation in pendingAnnotations" :key="annotation.id" class="bg-white rounded-lg shadow p-6">
          <div class="flex items-start justify-between mb-4">
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-2">
                <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded">
                  {{ annotation.peak_type === 'edit' ? 'Edit Count' : 'Editor Count' }}
                </span>
                <span class="text-sm text-gray-500">{{ annotation.project }}</span>
              </div>
              <p class="text-sm text-gray-600">
                <strong>Date:</strong> {{ formatDate(annotation.timestamp) }}
              </p>
              <p class="text-sm text-gray-600">
                <strong>Submitted by:</strong> {{ annotation.submitted_by }}
              </p>
              <p class="text-sm text-gray-600">
                <strong>Submitted:</strong> {{ formatDate(annotation.submitted_at) }}
              </p>
            </div>
          </div>

          <div class="mb-4 p-4 bg-gray-50 rounded-lg">
            <p class="text-sm font-semibold text-gray-900 mb-2">Description:</p>
            <p class="text-sm text-gray-700">{{ annotation.description }}</p>
            <div v-if="annotation.relevant_link" class="mt-2">
              <p class="text-sm font-semibold text-gray-900 mb-1">Link:</p>
              <a :href="annotation.relevant_link" target="_blank" rel="noopener noreferrer" 
                 class="text-sm text-blue-600 hover:underline break-all">
                {{ annotation.relevant_link }}
              </a>
            </div>
          </div>

          <!-- Review Actions -->
          <div class="flex items-center gap-3">
            <button
              @click="openReviewModal(annotation, 'approve')"
              class="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700"
            >
              <cdx-icon :icon="cdxIconCheck" size="small" class="inline mr-1" />
              Approve
            </button>
            <button
              @click="openReviewModal(annotation, 'edit')"
              class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700"
            >
              <cdx-icon :icon="cdxIconEdit" size="small" class="inline mr-1" />
              Edit & Approve
            </button>
            <button
              @click="openReviewModal(annotation, 'reject')"
              class="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700"
            >
              <cdx-icon :icon="cdxIconClose" size="small" class="inline mr-1" />
              Reject
            </button>
          </div>
        </div>
      </div>

      <!-- Pending Reports Tab -->
      <div v-if="activeTab === 'reports'" class="space-y-4">
        <div v-if="loading" class="text-center py-12">
          <p class="text-gray-500">Loading reports...</p>
        </div>

        <div v-else-if="pendingReports.length === 0" class="bg-white rounded-lg shadow p-12 text-center">
          <cdx-icon :icon="cdxIconCheck" size="large" class="text-green-600 mx-auto mb-4" />
          <p class="text-lg font-semibold text-gray-900">All caught up!</p>
          <p class="text-sm text-gray-500 mt-2">No pending reports to review.</p>
        </div>

        <div v-else v-for="report in pendingReports" :key="report.report_id" class="bg-white rounded-lg shadow p-6">
          <div class="flex items-start justify-between mb-4">
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-2">
                <span class="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded">
                  REPORTED
                </span>
                <span class="text-sm text-gray-500">{{ report.annotation.project }}</span>
              </div>
              <p class="text-sm text-gray-600">
                <strong>Reported by:</strong> {{ report.reported_by }}
              </p>
              <p class="text-sm text-gray-600">
                <strong>Reported:</strong> {{ formatDate(report.reported_at) }}
              </p>
            </div>
          </div>

          <div class="mb-4 p-4 bg-red-50 rounded-lg border border-red-200">
            <p class="text-sm font-semibold text-gray-900 mb-2">Report Reason:</p>
            <p class="text-sm text-gray-700">{{ report.report_reason }}</p>
          </div>

          <div class="mb-4 p-4 bg-gray-50 rounded-lg">
            <p class="text-sm font-semibold text-gray-900 mb-2">Current Annotation:</p>
            <p class="text-sm text-gray-700">{{ report.annotation.description }}</p>
            <div v-if="report.annotation.relevant_link" class="mt-2">
              <a :href="report.annotation.relevant_link" target="_blank" rel="noopener noreferrer" 
                 class="text-sm text-blue-600 hover:underline break-all">
                {{ report.annotation.relevant_link }}
              </a>
            </div>
          </div>

          <!-- Report Review Actions -->
          <div class="flex items-center gap-3">
            <button
              @click="openReportReviewModal(report, 'dismiss')"
              class="px-4 py-2 bg-gray-600 text-white text-sm font-medium rounded-lg hover:bg-gray-700"
            >
              Dismiss Report
            </button>
            <button
              @click="openReportReviewModal(report, 'edit')"
              class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700"
            >
              Edit Annotation
            </button>
            <button
              @click="openReportReviewModal(report, 'remove')"
              class="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700"
            >
              Remove Annotation
            </button>
          </div>
        </div>
      </div>

      <!-- Review Modal -->
      <ReviewAnnotationModal
        :isOpen="showReviewModal"
        :annotation="selectedAnnotation"
        :action="reviewAction"
        @close="showReviewModal = false"
        @success="handleReviewSuccess"
      />

      <!-- Report Review Modal -->
      <ReviewReportModal
        :isOpen="showReportReviewModal"
        :report="selectedReport"
        :action="reportReviewAction"
        @close="showReportReviewModal = false"
        @success="handleReportReviewSuccess"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { CdxIcon } from '@wikimedia/codex'
import { cdxIconArticle, cdxIconFlag, cdxIconCheck, cdxIconEdit, cdxIconClose } from '@wikimedia/codex-icons'
import ReviewAnnotationModal from '../components/ReviewAnnotationModal.vue'
import ReviewReportModal from '../components/ReviewReportModal.vue'
import axios from 'axios'

const activeTab = ref('annotations')
const loading = ref(false)
const stats = ref({
  pending_annotations: 0,
  pending_reports: 0,
  total_pending: 0
})
const pendingAnnotations = ref([])
const pendingReports = ref([])
const showReviewModal = ref(false)
const showReportReviewModal = ref(false)
const selectedAnnotation = ref(null)
const selectedReport = ref(null)
const reviewAction = ref('')
const reportReviewAction = ref('')

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const fetchStats = async () => {
  try {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000'
    const response = await axios.get(`${apiUrl}/api/annotations/stats`, {
      withCredentials: true
    })
    stats.value = response.data
  } catch (error) {
    console.error('Error fetching stats:', error)
  }
}

const fetchPendingAnnotations = async () => {
  loading.value = true
  try {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000'
    const response = await axios.get(`${apiUrl}/api/annotations/pending`, {
      withCredentials: true
    })
    pendingAnnotations.value = response.data.annotations || []
  } catch (error) {
    console.error('Error fetching pending annotations:', error)
  } finally {
    loading.value = false
  }
}

const fetchPendingReports = async () => {
  loading.value = true
  try {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000'
    const response = await axios.get(`${apiUrl}/api/annotations/reports/pending`, {
      withCredentials: true
    })
    pendingReports.value = response.data.reports || []
  } catch (error) {
    console.error('Error fetching pending reports:', error)
  } finally {
    loading.value = false
  }
}

const openReviewModal = (annotation, action) => {
  selectedAnnotation.value = annotation
  reviewAction.value = action
  showReviewModal.value = true
}

const openReportReviewModal = (report, action) => {
  selectedReport.value = report
  reportReviewAction.value = action
  showReportReviewModal.value = true
}

const handleReviewSuccess = () => {
  fetchStats()
  fetchPendingAnnotations()
}

const handleReportReviewSuccess = () => {
  fetchStats()
  fetchPendingReports()
}

onMounted(() => {
  fetchStats()
  fetchPendingAnnotations()
  fetchPendingReports()
})
</script>

<style scoped>
/* Additional styles if needed */
</style>
