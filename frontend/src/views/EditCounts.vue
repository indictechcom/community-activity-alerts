<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-cyan-100 font-sans">
    <Navbar />

    <div class="flex pt-20">
      <Sidebar @fetch-data="fetchActivityData" />

      <!-- Main content area -->
      <main 
        class="flex-1 transition-all duration-300 ease-in-out p-4 sm:p-6 lg:p-8 " 
        :class="isSidebarOpen ? 'lg:ml-80' : 'lg:ml-0'"
      >
        <!-- Loading State -->
        <div v-if="loading" class="flex items-center justify-center h-full pt-16 sm:pt-24">
          <div class="glass-card text-center p-8 sm:p-12 rounded-3xl ">
            <div class="flex flex-col items-center gap-6 ">
              <svg class="w-16 h-16 animate-spin text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <div class="space-y-1">
                <p class="text-xl font-semibold text-gray-800">Fetching Data</p>
                <p class="text-gray-600">Please wait while we gather the activity data...</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="flex items-center justify-center h-[calc(100vh-9rem)]  ">
           <div class="glass-card text-center p-8 sm:p-12 rounded-3xl w-full h-full  ">
            <div class="flex justify-center items-center gap-6 h-full">
              <!-- Error Icon -->
              <div class="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center">
                <svg class="w-10 h-10 text-red-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div class="space-y-1">
                <p class="lg:text-3xl text-xl font-semibold text-gray-800">An Error Occurred</p>
                <p class="text-gray-600">{{ error }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Data Display State -->
        <div v-else-if="activityData" class="space-y-6 sm:space-y-8 max-w-7xl mx-auto animate-fade-in">
          <ActivityChart :chart-data="activityData.chartData" />
          <PeaksTable :peaks="activityData.peaks" />
        </div>

        <!-- Initial State -->
        <div v-else class="flex items-center justify-center h-[calc(100vh-9rem)]  ">
          <div class="glass-card flex items-center justify-center text-center  rounded-3xl w-full h-full ">
            <div class=" flex flex-col items-center gap-6">

              <div class=" w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center ">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" stroke="rgb(59 130 246)" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3m.08 4h.01"/></g></svg>
              </div>
              <div class="space-y-2">
                <h2 class="text-lg md:text-3xl px-4 md:px-0   font-bold text-gray-800">Welcome to Activity Alerts</h2>
                <p class="text-lg md:text-xl px-4 md:px-0 text-gray-600">
                  Please use the filters on the left to select <br> a project and date range, then click "Fetch Data" to visualize community activity.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Navbar from '../components/Navbar.vue'
import Sidebar from '../components/Sidebar.vue'
import ActivityChart from '../components/ActivityChart.vue'
import PeaksTable from '../components/PeaksTable.vue'
import axios from 'axios'

const loading = ref(false)
const error = ref(null)
const activityData = ref(null)


const isSidebarOpen = ref(true); 

const fetchActivityData = async (filters) => {
  if (!filters.language || !filters.project_group || !filters.datestart || !filters.dateend) {
    error.value = 'Please make sure all filter fields are selected.'
    return
  }

  loading.value = true
  error.value = null
  activityData.value = null

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

<style>
.glass-card {
  background: rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fade-in 0.5s ease-out forwards;
}
</style>
