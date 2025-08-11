<template>
  <div class="flex">
    <!-- Sidebar -->
    <aside class="w-64 bg-gray-800 text-white p-4">
      <h2 class="text-lg font-bold mb-4">Menu</h2>
      <ul>
        <li class="mb-2"><a href="#" class="hover:underline">Dashboard</a></li>
        <li><a href="#" class="hover:underline">Reports</a></li>
      </ul>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 p-6">
      <h1 class="text-2xl font-bold mb-4">Wikimedia Data</h1>
      <TwoStepProjectSelector @projectSelected="handleProjectSelect" />

      <div class="mt-6">
        <h2 class="text-xl mb-2">Selected Project: {{ selectedProject }}</h2>
        <p v-if="selectedProject">You can now fetch and display project data here.</p>
      </div>
    </main>
  </div>
</template>

<script>
import TwoStepProjectSelector from './components/TwoStepProjectSelector.vue'

export default {
  components: { TwoStepProjectSelector },
  data() {
    return {
      selectedProject: ''
    }
  },
  methods: {
    handleProjectSelect(project) {
      this.selectedProject = project
    }
  }
}
</script>

