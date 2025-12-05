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
            <th class="py-3 px-4 text-sm font-bold text-gray-900 bg-gray-50 text-right">Edits</th>
            <th class="py-3 px-4 text-sm font-bold text-gray-900 bg-gray-50 text-right">Rolling Mean</th>
            <th class="py-3 px-4 text-sm font-bold text-gray-900 bg-gray-50 text-right">Threshold</th>
            <th class="py-3 px-4 text-sm font-bold text-gray-900 bg-gray-50 text-right last:rounded-tr-lg">% Diff</th>
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
            
            <!-- Edits -->
            <td class="py-3 px-4 text-sm text-gray-900 text-right font-mono">
              {{ peak.edits.toLocaleString() }}
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
import { CdxIcon } from '@wikimedia/codex'
import { cdxIconAlert, cdxIconCheck } from '@wikimedia/codex-icons'

const props = defineProps({
  peaks: {
    type: Array,
    required: true
  }
})

// Formats a timestamp like "2025-02-01" into "Feb 1, 2025"
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
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