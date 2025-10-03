<template>

  <aside
    :class="[
      'glass-card fixed left-0 top-20 h-[calc(100vh-6.5rem)] m-4 rounded-3xl p-6 transition-all duration-300 z-40 overflow-y-auto scrollbar-thin scrollbar-thumb-blue-200 scrollbar-track-transparent',
      isOpen ? 'w-80 translate-x-0' : 'w-80 -translate-x-[110%] lg:translate-x-0'
    ]"
  >
    <div class="flex flex-col gap-6">
      <!-- Header with Icon and Title -->
      <div class="flex items-center gap-4 mb-2">
        <div class="w-12 h-12 rounded-2xl glass-button flex items-center justify-center ">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-gray-800">Filters</h2>
      </div>

      <!-- Project Filter -->
      <div>
        <label class="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-3 ml-1">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" /></svg>
          Project
        </label>
        <div class="relative">
          <select v-model="filters.project" class="glass-input">
            <option value="" disabled>Select Project</option>
            <option v-for="project in availableProjects" :key="project" :value="project">{{ project }}</option>
          </select>
          <div class="chevron-icon"><svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg></div>
        </div>
      </div>

      <!-- Language Filter -->
      <div>
        <label class="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-3 ml-1">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" /></svg>
          Language
        </label>
        <div class="relative">
          <select v-model="filters.language" :disabled="!filters.project" :class="['glass-input', !filters.project ? 'cursor-not-allowed opacity-60' : '']">
            <option value="" disabled>Select Language</option>
            <option v-for="lang in availableLanguages" :key="lang" :value="lang">{{ lang }}</option>
          </select>
          <div class="chevron-icon"><svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg></div>
        </div>
      </div>

      <!-- Date Range Section -->
      <div class="pt-2">
        <div class="flex items-center gap-2 mb-3 ml-1">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
          <span class="text-sm font-semibold text-gray-700">Date Range</span>
        </div>
        <div class="space-y-4">
          <input v-model="filters.dateStart" type="month" class="glass-input" placeholder="Start Date" />
          <input v-model="filters.dateEnd" type="month" class="glass-input" placeholder="End Date" />
        </div>
        <div class="grid grid-cols-2 gap-2 mt-4">
          <button v-for="option in quickRanges" :key="option.label" @click="applyQuickRange(option.value)" class="glass-button text-sm">
            {{ option.label }}
          </button>
        </div>
      </div>

      <!-- Fetch Data Button -->
      <button @click="handleFetchData" class="w-full px-6 py-4 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 text-white font-bold text-lg hover:from-blue-600 hover:to-cyan-600 hover:scale-[1.03] active:scale-[0.98] transition-all duration-200 shadow-lg hover:shadow-blue-200 flex items-center justify-center gap-3 mt-4">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
        Fetch Data
      </button>
    </div>
  </aside>

  <!-- Mobile Toggle Button -->
  <button @click="isOpen = !isOpen" class="lg:hidden fixed left-4 top-24 z-50 w-14 h-14 rounded-2xl glass-button flex items-center justify-center hover:scale-110 active:scale-95 transition-all duration-200">
    <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 text-gray-800 transition-transform duration-300" :class="{ 'rotate-180': isOpen }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="isOpen ? 'M6 18L18 6M6 6l12 12' : 'M4 6h16M4 12h16M4 18h7'" />
    </svg>
  </button>

  <!-- Mobile Backdrop -->
  <Transition name="fade">
    <div v-if="isOpen" @click="isOpen = false" class="lg:hidden fixed inset-0 bg-black/20 backdrop-blur-sm z-30"></div>
  </Transition>
</template>

<script setup>
import axios from 'axios';
import { ref, reactive, onMounted, watch } from 'vue';

const isOpen = ref(false);
const emit = defineEmits(['fetchData']);

const projectNameMap = {
  wiki: 'Wikipedia', wiktionary: 'Wiktionary', wikibooks: 'Wikibooks',
  wikinews: 'Wikinews', wikiquote: 'Wikiquote', wikisource: 'Wikisource',
  wikiversity: 'Wikiversity', wikivoyage: 'Wikivoyage'
};

const filters = reactive({
  project: '', language: '', dateStart: '', dateEnd: ''
});

const knownProjects = Object.values(projectNameMap).sort()
const availableProjects = ref([...knownProjects]) 
const availableLanguages = ref([]);
let projectLanguageMap = {};
let languageProjectUrlMap = {};

onMounted(async () => {
try {
  const response = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/api/communities`);
  const data = response.data;
  processCommunityData(data);
} catch (error) {
  console.error('Failed to fetch communities:', error);
}
});

const processCommunityData = (data) => {
  const tempProjectLangs = {}
  const tempLangProjUrls = {}

  for (const languageName in data) {
    if (!tempLangProjUrls[languageName]) tempLangProjUrls[languageName] = {}

    for (const projectInfo of data[languageName]) {
      const fullProjectName = projectNameMap[projectInfo.sitename] || projectInfo.sitename
      if (!tempProjectLangs[fullProjectName]) tempProjectLangs[fullProjectName] = []
      tempProjectLangs[fullProjectName].push(languageName)
      tempLangProjUrls[languageName][fullProjectName] = projectInfo.url
    }
  }

  projectLanguageMap = tempProjectLangs
  languageProjectUrlMap = tempLangProjUrls

  const newProjects = Object.keys(projectLanguageMap).filter(p => !availableProjects.value.includes(p))
  availableProjects.value.push(...newProjects)
  availableProjects.value.sort()
}


watch(() => filters.project, (newProject) => {
  filters.language = '';
  availableLanguages.value = newProject ? (projectLanguageMap[newProject] || []).sort() : [];
});

const formatApiDate = (dateString) => {
  if (!dateString) return '';
  const [year, month] = dateString.split('-');
  return new Date(year, month - 1).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
};

const quickRanges = [
  { label: 'Last 3m', value: '3m' }, { label: 'Last 6m', value: '6m' },
  { label: 'YTD', value: 'ytd' }, { label: 'All', value: 'all' }
];

const applyQuickRange = (range) => {
    const now = new Date();
    let start, end = new Date(now.getFullYear(), now.getMonth() + 1, 0);

    if (range === 'all') {
        start = new Date(2014, 0, 1);
    } else if (range === 'ytd') {
        start = new Date(now.getFullYear(), 0, 1);
    } else {
        const months = parseInt(range.slice(0, -1), 10);
        start = new Date(now.getFullYear(), now.getMonth() - months + 1, 1);
    }
    
    filters.dateStart = `${start.getFullYear()}-${String(start.getMonth() + 1).padStart(2, '0')}`;
    filters.dateEnd = `${end.getFullYear()}-${String(end.getMonth() + 1).padStart(2, '0')}`;
};

const handleFetchData = () => {
  if (!filters.project || !filters.language || !filters.dateStart || !filters.dateEnd) {
    alert("Please fill in all filter options.");
    return;
  }
  const projectUrl = languageProjectUrlMap[filters.language]?.[filters.project];
  if (!projectUrl) {
    console.error("Could not find project URL.");
    return;
  }
  const projectIdentifier = projectUrl.replace(/^(https?:\/\/)/, '');
  const payload = {
    project_group: projectIdentifier,
    language: filters.language,
    datestart: formatApiDate(filters.dateStart),
    dateend: formatApiDate(filters.dateEnd)
  };
  emit('fetchData', payload);
  if (window.innerWidth < 1024) isOpen.value = false;
};
</script>

<style scoped>
.glass-input {
  width: 100%;
  padding-left: 1rem;
  padding-right: 1rem;
  padding-top: 0.75rem;
  padding-bottom: 0.75rem;
  border-radius: 1rem;
  color: #1f2937; 
  font-weight: 500;
  outline: none;
  transition: all 0.2s;
  appearance: none;
  cursor: pointer;
  background: rgba(255,255,255,0.4);
  border: 1px solid rgba(255,255,255,0.5);
  font-family: inherit;
}
.glass-input::placeholder {
  color: #6b7280; 
}
.glass-input:focus {
  background: rgba(255,255,255,0.8);
  box-shadow: 0 0 0 2px #93c5fd;
}
.glass-button {
  flex: 1 1 0%;
  padding-left: 0.75rem;
  padding-right: 0.75rem;
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
  border-radius: 0.75rem;
  background: rgba(255,255,255,0.4);
  border: 1px solid rgba(255,255,255,0.5);
  color: #374151; 
  font-weight: 600;
  transition: all 0.2s;
  font-family: inherit;
}
.glass-button:hover {
  background: rgba(255,255,255,0.8);
}
.glass-button:active {
  transform: scale(0.95);
}
.chevron-icon {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
input[type="month"]::-webkit-calendar-picker-indicator {
  cursor: pointer;
  filter: invert(0.5) brightness(0.8);
}
.scrollbar-thin {
  scrollbar-width: thin;
}
.scrollbar-thumb-blue-200::-webkit-scrollbar-thumb {
  background-color: #bfdbfe;
  border-radius: 10px;
}
.scrollbar-track-transparent::-webkit-scrollbar-track {
  background: transparent;
}
</style>
