<template>
  <div class="codex-table-card bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
    
    <!-- 1. Header Section -->
    <div class="flex items-center gap-3 mb-6">
      <div class="p-2 bg-red-50 text-red-600 rounded-lg">
        <cdx-icon :icon="cdxIconAlert" size="medium" />
      </div>
      <div>
        <h3 class="text-lg font-bold text-gray-900 leading-tight">
          Peak Activity Alerts
        </h3>
        <p class="text-sm text-gray-500 mt-1">
          Identified dates where edit volume exceeded the rolling mean.
        </p>
      </div>
    </div>

    <!-- Annotation Modal -->
    <AnnotationModal 
      :isOpen="showAnnotationModal"
      :peakData="selectedPeak"
      @close="showAnnotationModal = false"
      @success="handleAnnotationSuccess"
    />

    <!-- Report Modal -->
    <ReportModal
      :isOpen="showReportModal"
      :annotationData="selectedAnnotation"
      @close="showReportModal = false"
      @success="handleReportSuccess"
    />

    <!-- 2. Data Table -->
    <div v-if="peaks && peaks.length > 0" class="overflow-x-auto">
      <!-- 
        Using standard HTML table structure styled with Codex-like utilities 
        to ensure perfect control over the responsive layout and cell formatting.
      -->
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="border-b-2 border-gray-200">
            <th class="py-3 px-4 text-sm font-bold text-gray-900 bg-gray-50 first:rounded-tl-lg">Date</th>
            <th class="py-3 px-4 text-sm font-bold text-gray-900 bg-gray-50 text-right">{{ getCountLabel() }}</th>
            <th class="py-3 px-4 text-sm font-bold text-gray-900 bg-gray-50 text-right">Rolling Mean</th>
            <th class="py-3 px-4 text-sm font-bold text-gray-900 bg-gray-50 text-right">Threshold</th>
            <th class="py-3 px-4 text-sm font-bold text-gray-900 bg-gray-50 text-right">% Diff</th>
            <th class="py-3 px-4 text-sm font-bold text-gray-900 bg-gray-50 last:rounded-tr-lg">Annotation</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr
            v-for="(peak, index) in peaks"
            :key="peak.timestamp"
            class="group hover:bg-blue-50 transition-colors duration-150"
          >
            <!-- Date -->
            <td class="py-3 px-4 text-sm text-gray-900 font-medium">
              {{ formatDate(peak.timestamp) }}
            </td>
            
            <!-- Edits or Editors -->
            <td class="py-3 px-4 text-sm text-gray-900 text-right font-mono">
              {{ getCountValue(peak).toLocaleString() }}
            </td>
            
            <!-- Rolling Mean -->
            <td class="py-3 px-4 text-sm text-gray-500 text-right font-mono">
              {{ peak.rolling_mean.toFixed(1) }}
            </td>
            
            <!-- Threshold -->
            <td class="py-3 px-4 text-sm text-gray-500 text-right font-mono">
              {{ peak.threshold.toFixed(1) }}
            </td>
            
            <!-- Percentage Difference -->
            <td class="py-3 px-4 text-right">
              <span 
                class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold"
                :class="getBadgeStyles(peak.percentage_difference)"
              >
                +{{ peak.percentage_difference.toFixed(1) }}%
              </span>
            </td>

            <!-- Annotation -->
            <td class="py-3 px-4">
              <div v-if="peakAnnotations[peak.timestamp]" class="space-y-2">
                <div class="text-sm text-gray-700 bg-blue-50 p-2 rounded border border-blue-200">
                  <p class="mb-1">{{ peakAnnotations[peak.timestamp].description }}</p>
                  <a 
                    v-if="peakAnnotations[peak.timestamp].relevant_link"
                    :href="peakAnnotations[peak.timestamp].relevant_link"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="text-xs text-blue-600 hover:underline flex items-center gap-1"
                  >
                    <cdx-icon :icon="cdxIconLinkExternal" size="x-small" />
                    View source
                  </a>
                  <p class="text-xs text-gray-500 mt-1">
                    by {{ peakAnnotations[peak.timestamp].submitted_by }}
                  </p>
                </div>
                <button
                  @click="openReportModal(peak, peakAnnotations[peak.timestamp])"
                  class="text-xs text-red-600 hover:text-red-800 flex items-center gap-1"
                >
                  <cdx-icon :icon="cdxIconFlag" size="x-small" />
                  Report
                </button>
              </div>
              <button
                v-else
                @click="openAnnotationModal(peak)"
                class="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
              >
                <cdx-icon :icon="cdxIconAdd" size="small" />
                Add annotation
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 3. Empty State -->
    <div v-else class="flex flex-col items-center justify-center py-12 text-center bg-gray-50 rounded-lg border border-dashed border-gray-200">
      <cdx-icon :icon="cdxIconCheck" size="large" class="text-green-600 mb-2" />
      <p class="font-semibold text-gray-900">No anomalies detected</p>
      <p class="text-sm text-gray-500">Activity is within normal parameters for this period.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { CdxIcon } from '@wikimedia/codex'
import { cdxIconAlert, cdxIconCheck, cdxIconAdd, cdxIconLinkExternal, cdxIconFlag } from '@wikimedia/codex-icons'
import AnnotationModal from './AnnotationModal.vue'
import ReportModal from './ReportModal.vue'
import axios from 'axios'

const props = defineProps({
  peaks: {
    type: Array,
    required: true
  },
  project: {
    type: String,
    required: true
  }
})

const showAnnotationModal = ref(false)
const showReportModal = ref(false)
const selectedPeak = ref({})
const selectedAnnotation = ref({})
const peakAnnotations = ref({})

// Formats a timestamp like "2025-02-01" into "Feb 1, 2025"
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

// Get the appropriate count value (edits or editors)
const getCountValue = (peak) => {
  return peak.edits !== undefined ? peak.edits : peak.editors
}

// Get the appropriate label for the count column
const getCountLabel = () => {
  if (props.peaks && props.peaks.length > 0) {
    return props.peaks[0].edits !== undefined ? 'Edits' : 'Editors'
  }
  return 'Count'
}

// Codex Standard Status Colors
const getBadgeStyles = (percentage) => {
  if (percentage >= 50) {
    // Critical (Red)
    return 'bg-red-100 text-red-700 border border-red-200'
  }
  if (percentage >= 30) {
    // Warning (Orange/Yellow)
    return 'bg-yellow-100 text-yellow-800 border border-yellow-200'
  }
  // Notice (Blue/Gray)
  return 'bg-blue-100 text-blue-700 border border-blue-200'
}

// Fetch annotations for all peaks
const fetchAnnotations = async () => {
  if (!props.peaks || props.peaks.length === 0) return

  const apiUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000'
  const peakType = props.peaks[0].edits !== undefined ? 'edit' : 'editor'

  for (const peak of props.peaks) {
    try {
      const response = await axios.get(`${apiUrl}/api/annotations/get`, {
        params: {
          project: props.project,
          timestamp: peak.timestamp,
          peak_type: peakType
        }
      })

      if (response.data && response.data.id) {
        peakAnnotations.value[peak.timestamp] = response.data
      }
    } catch (error) {
      console.error(`Error fetching annotation for ${peak.timestamp}:`, error)
    }
  }
}

// Open annotation modal
const openAnnotationModal = (peak) => {
  const peakType = peak.edits !== undefined ? 'edit' : 'editor'
  selectedPeak.value = {
    project: props.project,
    timestamp: peak.timestamp,
    peak_type: peakType
  }
  showAnnotationModal.value = true
}

// Open report modal
const openReportModal = (peak, annotation) => {
  selectedAnnotation.value = {
    annotation_id: annotation.id,
    peak: peak,
    annotation: annotation
  }
  showReportModal.value = true
}

// Handle successful annotation submission
const handleAnnotationSuccess = () => {
  fetchAnnotations()
}

// Handle successful report submission
const handleReportSuccess = () => {
  // Optionally refresh or show a message
}

// Watch for changes in peaks and fetch annotations
watch(() => props.peaks, () => {
  if (props.peaks && props.peaks.length > 0) {
    fetchAnnotations()
  }
}, { immediate: true })

</script>

<style scoped>
/* Codex Token Mapping for strict compliance */

.text-gray-900 {
  color: var(--color-base, #202122);
}

.text-gray-500 {
  color: var(--color-subtle, #54595d);
}

.border-gray-200 {
  border-color: var(--border-color-subtle, #c8ccd1);
}

/* Table Header Background */
.bg-gray-50 {
  background-color: var(--background-color-interactive-subtle, #f8f9fa);
}

/* Hover State */
.hover\:bg-blue-50:hover {
  background-color: var(--background-color-interactive-subtle, #f8f9fa); /* Standard hover gray */
}

/* Destructive / Alert Colors */
.bg-red-50 {
  background-color: #fee7e6; /* Codex Red 50 (approx) */
}
.text-red-600 {
  color: var(--color-destructive, #d33);
}
</style>