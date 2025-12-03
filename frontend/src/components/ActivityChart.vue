<template>
  <!-- 
    Using standard Codex styling variables for the container 
    Instead of 'glass', we use a clean white card with standard borders.
  -->
  <div class="codex-chart-card bg-white border border-gray-200 rounded-lg p-6 shadow-sm transition-all duration-200 hover:shadow-md">
    
    <!-- 1. HEADER SECTION (Labels & Context) -->
    <!-- This addresses your request to let users know *what* they are looking at -->
    <div class="mb-6 border-b border-gray-100 pb-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-blue-50 text-blue-600 rounded-lg">
            <cdx-icon :icon="cdxIconArrowUp" size="medium" />
          </div>
          <div>
            <h3 class="text-lg font-bold text-gray-900 leading-tight">
              {{ title || 'Activity Overview' }}
            </h3>
            <p class="text-sm text-gray-500 mt-1">
              {{ subtitle || 'Edit counts and activity peaks over the selected period.' }}
            </p>
          </div>
        </div>
        
        <!-- Optional Legend/Badge area -->
        <div v-if="hasData" class="flex gap-4 text-xs font-medium">
          <div class="flex items-center gap-2">
            <span class="w-3 h-1 bg-[#36c] rounded-full"></span>
            <span class="text-gray-600">Edits</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="w-2 h-2 bg-[#d33] transform rotate-45"></span>
            <span class="text-gray-600">Alerts</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 2. CHART AREA -->
    <div v-if="hasData" class="relative">
      <div ref="chartContainer" class="w-full h-[500px]"></div>
    </div>

    <!-- 3. EMPTY STATE -->
    <div v-else class="flex flex-col items-center justify-center w-full h-[400px] bg-gray-50 rounded-lg border border-dashed border-gray-200">
      <cdx-icon :icon="cdxIconArticle" size="large" class="text-gray-300 mb-3" />
      <p class="font-semibold text-gray-700">No Activity to Display</p>
      <p class="text-sm text-gray-500">Select a project and date range to view statistics.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, nextTick } from 'vue'
import Plotly from 'plotly.js-dist-min'
import { CdxIcon } from '@wikimedia/codex'
import { cdxIconArrowUp, cdxIconArticle } from '@wikimedia/codex-icons'

const props = defineProps({
  chartData: {
    type: Object,
    required: true
  },
  // Added props for context labels
  title: {
    type: String,
    default: ''
  },
  subtitle: {
    type: String,
    default: ''
  }
})

const chartContainer = ref(null)

const hasData = computed(() => {
  return props.chartData &&
         props.chartData.lineTrace &&
         props.chartData.lineTrace.x &&
         props.chartData.lineTrace.x.length > 0
})

const renderChart = () => {
  if (!hasData.value || !chartContainer.value) return

  const { lineTrace, peaksTrace } = props.chartData
  const lineMode = lineTrace.x.length === 1 ? 'lines+markers' : lineTrace.mode;

  // CODEX COLORS (Hardcoded hex values matching standard Wiki tokens)
  const COLOR_BASE = '#202122';
  const COLOR_SUBTLE = '#54595d';
  const COLOR_PROGRESSIVE = '#36c'; // Wiki Blue
  const COLOR_DESTRUCTIVE = '#d33'; // Wiki Red (for alerts)
  const COLOR_GRID = '#eaecf0';

  const data = [
    {
      ...lineTrace,
      mode: lineMode,
      name: 'Edits',
      // Standard Wiki Blue Line
      line: { color: COLOR_PROGRESSIVE, width: 2, shape: 'spline' },
      marker: { color: COLOR_PROGRESSIVE, size: 6 },
      hovertemplate: '<b>%{x}</b><br>Edits: %{y}<extra></extra>'
    },
    {
      ...peaksTrace,
      name: 'High Activity Alert',
      marker: {
        size: 10,
        color: COLOR_DESTRUCTIVE, // Red for peaks
        symbol: 'diamond',
        line: { color: '#fff', width: 1 }
      },
      text: peaksTrace.y.map(val => `${val}`),
      textposition: 'top center',
      textfont: { color: COLOR_DESTRUCTIVE, size: 11, family: 'sans-serif' },
      hovertemplate: '<b>Peak Alert</b><br>Date: %{x}<br>Edits: %{y}<extra></extra>'
    }
  ]

  const layout = {
    autosize: true,
    margin: { l: 60, r: 20, t: 20, b: 60 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: {
      family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Lato, Helvetica, Arial, sans-serif',
      color: COLOR_BASE
    },
    xaxis: {
      title: 'Time Period',
      gridcolor: COLOR_GRID,
      linecolor: COLOR_GRID,
      tickfont: { color: COLOR_SUBTLE },
      zeroline: false
    },
    yaxis: {
      title: 'Edit Count',
      gridcolor: COLOR_GRID,
      linecolor: COLOR_GRID,
      tickfont: { color: COLOR_SUBTLE },
      rangemode: 'tozero',
      zeroline: false
    },
    showlegend: false, // Custom legend in HTML is cleaner
    hovermode: 'x unified', // Modern hover interaction
    hoverlabel: {
      bgcolor: '#fff',
      bordercolor: COLOR_GRID,
      font: { color: COLOR_BASE }
    }
  }

  const config = {
    responsive: true,
    displayModeBar: false,
    displaylogo: false
  }

  Plotly.newPlot(chartContainer.value, data, layout, config)
}

watch(() => props.chartData, () => {
  if (hasData.value) {
    nextTick(() => {
      renderChart()
    })
  }
}, { deep: true, immediate: true })

</script>

<style scoped>
/* Codex Tokens Mapping */
.text-gray-900 {
  color: var(--color-base, #202122);
}

.text-gray-500 {
  color: var(--color-subtle, #54595d);
}

.border-gray-200 {
  border-color: var(--border-color-subtle, #c8ccd1);
}

.bg-blue-50 {
  background-color: var(--background-color-progressive-subtle, #eaf3ff);
}

.text-blue-600 {
  color: var(--color-progressive, #36c);
}
</style>