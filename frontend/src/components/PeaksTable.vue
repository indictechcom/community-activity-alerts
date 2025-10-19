<template>
  <div class="glass-container rounded-2xl p-6 fade-in">
    <h2 class="text-xl font-semibold text-gray-800 mb-4">Peak Activity Alerts</h2>

    <div v-if="peaks && peaks.length > 0" class="overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-300">
            <th class="text-left py-3 px-4 text-sm font-semibold text-gray-700">Date</th>
            <th class="text-right py-3 px-4 text-sm font-semibold text-gray-700">Edits</th>
            <th class="text-right py-3 px-4 text-sm font-semibold text-gray-700">Rolling Mean</th>
            <th class="text-right py-3 px-4 text-sm font-semibold text-gray-700">Threshold</th>
            <th class="text-right py-3 px-4 text-sm font-semibold text-gray-700">% Difference</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(peak, index) in peaks"
            :key="peak.timestamp"
            class="border-b border-gray-200 hover:bg-white/30 transition-colors duration-200"
            :class="{ 'animate-fade-in': true }"
            :style="{ animationDelay: `${index * 0.1}s` }"
          >
            <td class="py-3 px-4 text-sm text-gray-700">{{ formatDate(peak.timestamp) }}</td>
            <td class="py-3 px-4 text-sm text-gray-800 font-medium text-right">{{ peak.edits }}</td>
            <td class="py-3 px-4 text-sm text-gray-600 text-right">{{ peak.rolling_mean.toFixed(1) }}</td>
            <td class="py-3 px-4 text-sm text-gray-600 text-right">{{ peak.threshold.toFixed(1) }}</td>
            <td class="py-3 px-4 text-sm font-semibold text-right" :class="getPercentageColor(peak.percentage_difference)">
              +{{ peak.percentage_difference.toFixed(2) }}%
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="text-center py-8 text-gray-500">
      No peak activity detected
    </div>
  </div>
</template>

<script setup>
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

//change the color according for percentage change
const getPercentageColor = (percentage) => {
  if (percentage >= 50) return 'text-red-600'
  if (percentage >= 30) return 'text-orange-600'
  return 'text-yellow-600'
}
</script>

<style scoped>
@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.animate-fade-in {
  animation: fade-in 0.4s ease-out forwards;
  opacity: 0;
}
</style>
