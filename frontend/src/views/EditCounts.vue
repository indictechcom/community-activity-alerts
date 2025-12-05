<template>
  <!-- 
    Standard Wikimedia Page Background 
    Using standard background-color-interactive-subtle (#f8f9fa) via utility class
  -->
  <div class="min-h-screen bg-gray-50 font-sans text-[#202122]">
    <Navbar />

    <div class="flex pt-16">
      <!-- 
        Using the SidebarFilters component we created earlier.
        The @fetchData event matches the emit from that component.
      -->
      <SidebarFilters @fetch-data="fetchActivityData" />

      <!-- Main Content Area -->
      <main 
        class="flex-1 transition-all duration-300 ease-in-out p-6 lg:p-8" 
        :class="isSidebarOpen ? 'lg:ml-80' : 'lg:ml-0'"
      >
        <div class="max-w-7xl mx-auto min-h-[calc(100vh-20rem)]">
          
          <!-- 1. LOADING STATE -->
          <div v-if="loading" class="flex flex-col items-center justify-center h-[60vh] animate-fade-in">
            <!-- Standard Wiki Spinner (Blue/Progressive) -->
            <div class="w-12 h-12 border-4 border-[#eaf3ff] border-t-[#36c] rounded-full animate-spin mb-4"></div>
            <h3 class="text-lg font-bold text-gray-900">Fetching Data</h3>
            <p class="text-gray-500">Retrieving edit history and statistics...</p>
          </div>

          <!-- 2. ERROR STATE -->
          <div v-else-if="error" class="flex flex-col items-center justify-center h-[60vh] animate-fade-in">
            <div class="codex-card max-w-lg w-full p-8 text-center border-t-4 border-t-[#d33]">
              <div class="inline-flex p-3 rounded-full bg-[#fee7e6] text-[#d33] mb-4">
                <cdx-icon :icon="cdxIconError" size="large" />
              </div>
              <h3 class="text-xl font-bold text-gray-900 mb-2">Unable to load data</h3>
              <p class="text-gray-600 mb-6">{{ error }}</p>
              
              <!-- Retry Hint -->
              <p class="text-sm text-gray-500 bg-gray-50 py-2 px-4 rounded">
                Please check your network connection or try a different date range.
              </p>
            </div>
          </div>

          <!-- 3. DATA DISPLAY STATE -->
          <div v-else-if="activityData" class="space-y-6 animate-fade-in">
            <!-- 
              Passing context to the chart 
              This ensures the chart title says "English Wikipedia" instead of just "Activity"
            -->
            <ActivityChart 
              :chart-data="activityData.chartData" 
              :title="currentContext.title"
              :subtitle="currentContext.subtitle"
            />
            
            <PeaksTable :peaks="activityData.peaks" />
          </div>

          <!-- 4. INITIAL / EMPTY STATE -->
          <div v-else class="flex flex-col items-center justify-center h-[60vh] text-center">
            <div class="codex-card p-12 max-w-2xl border-dashed">
              <div class="inline-flex p-4 rounded-full bg-[#eaf3ff] text-[#36c] mb-6">
                 <!-- Using 'Article' icon as a generic 'Content' placeholder -->
                <cdx-icon :icon="cdxIconArticle" class="w-12 h-12" />
              </div>
              <h2 class="text-2xl font-bold text-gray-900 mb-3">Community Activity Alerts</h2>
              <p class="text-lg text-gray-500 max-w-md mx-auto leading-relaxed">
                Select a project (e.g., Wikipedia) and a language from the sidebar to visualize edit trends and anomalies.
              </p>
            </div>
          </div>

        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from 'axios'
import { CdxIcon } from '@wikimedia/codex'
import { cdxIconError, cdxIconArticle } from '@wikimedia/codex-icons'

// Import the standardized components we created previously
import Navbar from '../components/Navbar.vue'
import SidebarFilters from '../components/Sidebar.vue' // Renamed from Sidebar to match previous step
import ActivityChart from '../components/ActivityChart.vue'  // Using the new Chart component name
import PeaksTable from '../components/PeaksTable.vue'  // Using the new Table component name

const loading = ref(false)
const error = ref(null)
const activityData = ref(null)
const isSidebarOpen = ref(true)

// Store current filter context for display labels
const currentContext = reactive({
  title: '',
  subtitle: ''
})

const fetchActivityData = async (filters) => {
  if (!filters.language || !filters.project_group || !filters.datestart || !filters.dateend) {
    error.value = 'Please select all filter fields.'
    return
  }

  loading.value = true
  error.value = null
  activityData.value = null

  // Update Context for the UI
  const langName = filters.language.toUpperCase()
  const projName = filters.project_group.charAt(0).toUpperCase() + filters.project_group.slice(1)
  currentContext.title = `${langName} ${projName}`
  currentContext.subtitle = `Activity from ${filters.datestart} to ${filters.dateend}`

  try {
    const params = {
      language: filters.language,
      project_group: filters.project_group,
      datestart: filters.datestart,
      dateend: filters.dateend
    };

    const response = await axios.get(
      `${import.meta.env.VITE_BACKEND_URL}/api/activity-data`,
      { params }
    );

    activityData.value = response.data;
  } catch (err) {
    if (axios.isAxiosError(err)) {
      error.value = err.response?.data?.message || err.message;
    } else {
      error.value = 'An unknown error occurred.';
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>

.codex-card {
  background-color: var(--background-color-base, #ffffff);
  border: 1px solid var(--border-color-subtle, #c8ccd1);
  border-radius: 8px; /* Standard Codex Border Radius */
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.codex-card.border-dashed {
  border-style: dashed;
}

/* Animations */
@keyframes fade-in {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-fade-in {
  animation: fade-in 0.3s ease-out forwards;
}

/* Scrollbar refinement for main area if needed */
main::-webkit-scrollbar {
  width: 4px;
}
main::-webkit-scrollbar-track {
  background: transparent;
}
main::-webkit-scrollbar-thumb {
  background-color: #c8ccd1;
  border-radius: 4px;
}
</style>