<template>
  <div class="p-4 border rounded bg-white shadow">
    <label class="block mb-2 font-medium">Step 1: Select Language</label>
    <select v-model="selectedLanguage" class="border p-2 rounded w-full mb-4">
      <option value="" disabled>Select a language</option>
      <option v-for="lang in languages" :key="lang" :value="lang">{{ lang }}</option>
    </select>

    <label class="block mb-2 font-medium">Step 2: Select Project</label>
    <select v-model="selectedProject" class="border p-2 rounded w-full mb-4" :disabled="!selectedLanguage">
      <option value="" disabled>Select a project</option>
      <option v-for="proj in projects" :key="proj" :value="proj">{{ proj }}</option>
    </select>

    <button
      class="bg-blue-600 text-white px-4 py-2 rounded disabled:bg-gray-400"
      :disabled="!selectedProject"
      @click="$emit('projectSelected', `${selectedLanguage}.${selectedProject}`)"
    >
      Confirm Selection
    </button>
  </div>
</template>

<script>
export default {
  data() {
    return {
      languages: ['en', 'fr', 'de', 'es'],
      projects: ['wikipedia', 'wiktionary', 'wikibooks'],
      selectedLanguage: '',
      selectedProject: ''
    }
  }
}
</script>