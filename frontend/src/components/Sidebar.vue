<template>
  <!-- 
    Sidebar Container 
    Using Codex tokens for background and borders to ensure it matches standard Wiki tools.
    z-40 ensures it sits below the Navbar (usually z-50).
  -->
  <aside
    class="codex-sidebar fixed left-0 top-16 h-[calc(100vh-4rem)] w-80 bg-white border-r border-gray-200 transition-transform duration-300 z-40 overflow-y-auto"
    :class="isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'"
  >
    <div class="p-4 space-y-6">
      
      <!-- Header -->
      <div class="flex items-center gap-3 pb-4 border-b border-gray-100">
        <div class="p-2 bg-blue-50 text-blue-600 rounded-lg">
          <cdx-icon :icon="cdxIconFunnel" size="medium" />
        </div>
        <h2 class="text-xl font-bold text-gray-900">Filters</h2>
      </div>

      <!-- Project Filter -->
      <cdx-field>
        <template #label>
          <div class="flex items-center gap-2 mb-1">
            <cdx-icon :icon="cdxIconBook" size="small" class="text-gray-500" />
            <span>Project</span>
          </div>
        </template>
        
        <cdx-select
          v-model:selected="filters.project"
          :menu-items="projectOptions"
          default-label="Select Project"
          placeholder="Choose a project..."
        />
      </cdx-field>

      <!-- Language Filter -->
      <cdx-field :disabled="!filters.project">
        <template #label>
          <div class="flex items-center gap-2 mb-1">
            <cdx-icon :icon="cdxIconLanguage" size="small" class="text-gray-500" />
            <span>Language</span>
          </div>
        </template>
        <template #help-text>
          <span v-if="!filters.project">Please select a project first</span>
        </template>

        <cdx-select
          v-model:selected="filters.language"
          :menu-items="languageOptions"
          default-label="Select Language"
          placeholder="Choose a language..."
          :disabled="!filters.project"
        />
      </cdx-field>

      <!-- Date Range Section -->
      <div class="space-y-4 pt-2">
        <div class="flex items-center gap-2 text-gray-900 font-medium">
          <cdx-icon :icon="cdxIconCalendar" size="small" class="text-gray-500" />
          <span>Date Range</span>
        </div>
        
        <div class="grid gap-4">
          <cdx-field label="Start Date">
            <cdx-text-input
              v-model="filters.dateStart"
              input-type="month"
            />
          </cdx-field>

          <cdx-field label="End Date">
            <cdx-text-input
              v-model="filters.dateEnd"
              input-type="month"
            />
          </cdx-field>
        </div>

        <!-- Quick Ranges -->
        <div class="grid grid-cols-2 gap-2">
          <cdx-button
            v-for="option in quickRanges"
            :key="option.value"
            @click="applyQuickRange(option.value)"
            size="medium"
            class="quick-range-btn"
            :class="{ 'is-active': option.value === activeRange }"
            :title="getFullLabel(option.value)"
          >
            {{ option.label }}
          </cdx-button>
        </div>

      </div>

      <!-- Fetch Data Button -->
      <div class="pt-4">
        <cdx-button 
          @click="handleFetchData" 
          action="progressive" 
          weight="primary" 
          class="w-full justify-center"
          size="large"
        >
          <template #icon>
            <cdx-icon :icon="cdxIconSearch" />
          </template>
          Fetch Data
        </cdx-button>
      </div>
    </div>
  </aside>

  <!-- Mobile Toggle Button -->
  <div class="lg:hidden fixed left-4 top-20 z-50">
    <cdx-button
      @click="isOpen = !isOpen"
      weight="primary"
      :aria-label="isOpen ? 'Close filters' : 'Open filters'"
      class="shadow-lg"
    >
      <cdx-icon :icon="isOpen ? cdxIconClose : cdxIconMenu" />
    </cdx-button>
  </div>

  <!-- Mobile Backdrop -->
  <transition
    enter-active-class="transition-opacity duration-300"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition-opacity duration-300"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div 
      v-if="isOpen" 
      @click="isOpen = false" 
      class="lg:hidden fixed inset-0 bg-black/50 backdrop-blur-sm z-30"
    ></div>
  </transition>
</template>

<script setup>
import axios from 'axios';
import { ref, reactive, onMounted, watch, computed } from 'vue';

// 1. Codex Component Imports
import { 
  CdxButton, 
  CdxIcon, 
  CdxField, 
  CdxSelect, 
  CdxTextInput ,
} from '@wikimedia/codex';

// 2. Codex Icon Imports
import { 
  cdxIconFunnel, 
  cdxIconBook, 
  cdxIconLanguage, 
  cdxIconCalendar, 
  cdxIconSearch,
  cdxIconMenu,
  cdxIconClose
} from '@wikimedia/codex-icons';

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

const availableProjects = ref([]);
const availableLanguages = ref([]);
let projectLanguageMap = {};
let languageProjectUrlMap = {};

// CODEX ADAPTER: CdxSelect requires items in { value, label } format
const projectOptions = computed(() => {
  return availableProjects.value.map(p => ({ value: p, label: p }));
});

const languageOptions = computed(() => {
  return availableLanguages.value.map(l => ({ value: l, label: l }));
});

const getFullLabel = (value) => {
  switch (value) {
    case '3m': return 'Last 3 Months';
    case '6m': return 'Last 6 Months';
    case 'ytd': return 'Year to Date';
    case 'all': return 'All Time';
    default: return '';
  }
};

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

  const newProjects = Object.keys(projectLanguageMap)
  availableProjects.value = newProjects.sort()
}

watch(() => filters.project, (newProject) => {
  // Clear language when project changes
  filters.language = null; // CdxSelect expects null or value, empty string might behave differently
  availableLanguages.value = newProject ? (projectLanguageMap[newProject] || []).sort() : [];
});

const formatApiDate = (dateString) => {
  if (!dateString) return '';
  const [year, month] = dateString.split('-');
  return new Date(year, month - 1).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
};

const quickRanges = [
  { label: 'Last 3m', value: '4m' }, { label: 'Last 6m', value: '7m' },
  { label: 'YTD', value: 'ytd' }, { label: 'All', value: 'all' }
];

const applyQuickRange = (range) => {
    const now = new Date();
    let start, end = new Date(now.getFullYear(), now.getMonth() + 1, 0);

    if (range === 'all') {
        start = new Date(2020, 1, 1);
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
    // You might want to use a CdxMessage or Dialog here instead of alert in the future
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
/* Codex Sidebar Styling 
   Using CSS Variables for strict compliance with Wikimedia themes.
*/
.codex-sidebar {
  background-color: var(--background-color-base, #ffffff);
  border-right-color: var(--border-color-subtle, #c8ccd1);
}

/* Typography Overrides to ensure Codex font stack */
.text-gray-900 {
  color: var(--color-base, #202122);
}

.text-gray-500 {
  color: var(--color-subtle, #54595d);
}

.bg-blue-50 {
  background-color: var(--background-color-progressive-subtle, #eaf3ff);
}

.text-blue-600 {
  color: var(--color-progressive, #36c);
}
</style>