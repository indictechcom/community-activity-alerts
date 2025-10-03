<template>
  <div class="glass-container rounded-2xl p-6 fade-in">
    <div v-if="hasData" ref="chartContainer" class="w-full h-[500px]"></div>

    <div v-else class="flex items-center justify-center w-full h-[500px]">
      <div class="text-center text-gray-500">
        <p class="font-semibold">No Activity to Display</p>
        <p class="text-sm">There is no edit data for the selected period.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, nextTick } from 'vue'
import Plotly from 'plotly.js-dist-min'

const props = defineProps({
  chartData: {
    type: Object,
    required: true
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

  const lineMarker = {
    color: '#6b7280',
    size: 8
  };

  const data = [
    {
      ...lineTrace,
      mode: lineMode,
      marker: lineMarker,
      line: { color: '#6b7280', width: 2 },
      hovertemplate: '<b>%{x}</b><br>Edits: %{y}<extra></extra>'
    },
    {
      ...peaksTrace,
      marker: {
        size: 12,
        color: '#ef4444',
        symbol: 'diamond',
        line: { color: '#dc2626', width: 2 }
      },
      text: peaksTrace.y.map(val => `${val}`),
      textposition: 'top center',
      textfont: { color: '#ef4444', size: 10 },
      hovertemplate: '<b>Peak Alert</b><br>Date: %{x}<br>Edits: %{y}<extra></extra>'
    }
  ]

  const layout = {
    autosize: true,
    margin: { l: 50, r: 30, t: 30, b: 50 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(255,255,255,0.1)',
    xaxis: {
      title: 'Time Period',
      gridcolor: 'rgba(200,200,200,0.3)',
      color: '#374151'
    },
    yaxis: {
      title: 'Edits',
      gridcolor: 'rgba(200,200,200,0.3)',
      color: '#374151',
      rangemode: 'tozero'
    },
    showlegend: true,
    legend: {
      x: 0,
      y: 1.1,
      orientation: 'h',
      bgcolor: 'rgba(255,255,255,0.5)',
      bordercolor: 'rgba(200,200,200,0.5)',
      borderwidth: 1
    },
    hovermode: 'closest'
  }

  const config = {
    responsive: true,
    displayModeBar: false
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