<template>
  <nav class="fixed top-0 left-0 right-0 z-50 px-4 sm:px-6 lg:px-8 py-4 ">
    <div class="glass-morphism rounded-2xl px-4 sm:px-6 py-3  ">
      <div class="flex items-center justify-between max-w-screen-2xl mx-auto ">
        <div class="flex items-center gap-2 sm:gap-3">
          <div class="glass-icon p-2 rounded-full ">
            <svg class="w-5 h-5 sm:w-6 sm:h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
            </svg>
          </div>
          <h1 class="text-base sm:text-lg lg:text-xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
            Community Activity Alerts
          </h1>
        </div>

        <!-- Desktop Navigation -->
        <div class="hidden md:flex items-center gap-4 lg:gap-6">
          <router-link
            v-for="link in navLinks"
            :key="link.path"
            :to="link.path"
            class="nav-link group relative px-4 py-2 text-sm lg:text-base font-medium text-gray-700 hover:text-blue-600 transition-all duration-300"
            active-class="text-blue-600"
          >
            <span class="relative z-10 flex items-center gap-2 text-lg hover:text-blue-600 hover:font-semibold">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path v-if="link.name === 'Edit Counts'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
              </svg>
              {{ link.name }}
            </span>
            <div class="absolute inset-0 glass-hover rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          </router-link>

          <!-- Auth Section -->
          <div v-if="auth.loading" class="glass-card px-4 py-2 rounded-xl">
            <div class="flex items-center gap-2">
              <div class="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
              <span class="text-md text-gray-600">Loading...</span>
            </div>
          </div>

          <div v-else>
            <!-- Logged In -->
            <div v-if="auth.isAuthenticated" class="flex items-center gap-3">
              

              <div class="glass-icon p-1 rounded-full">
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white font-semibold text-sm shadow-lg">
                  {{ userInitials }}
                </div>
              </div>

              <button @click="auth.logout" class="glass-button px-4 py-2 rounded-xl font-medium text-lg text-gray-700 hover:text-red-600 transition-colors duration-300 flex items-center gap-2 cursor-pointer">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
                </svg>
                Logout
              </button>
            </div>

            <!-- Not Logged In -->
            <div v-else>
              <button @click="auth.login" class="glass-button-primary px-6 py-2.5 rounded-xl font-semibold text-sm text-white flex items-center gap-2 shadow-lg hover:shadow-xl transition-all duration-300">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"/>
                </svg>
                Login
              </button>
            </div>
          </div>
        </div>

        <!-- Mobile Menu Button -->
        <button @click="toggleMobileMenu" class="md:hidden glass-icon p-2 rounded-full text-gray-700">
          <svg v-if="!mobileMenuOpen" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
          </svg>
          <svg v-else class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <!-- Mobile Menu -->
      <transition
        enter-active-class="transition ease-out duration-200"
        enter-from-class="opacity-0 transform -translate-y-2"
        enter-to-class="opacity-100 transform translate-y-0"
        leave-active-class="transition ease-in duration-150"
        leave-from-class="opacity-100 transform translate-y-0"
        leave-to-class="opacity-0 transform -translate-y-2"
      >
        <div v-if="mobileMenuOpen" class="md:hidden mt-4 pt-4 border-t border-white/30">
          <div class="flex flex-col gap-2">
            <router-link
              v-for="link in navLinks"
              :key="link.path"
              :to="link.path"
              @click="mobileMenuOpen = false"
              class="glass-card px-4 py-3 rounded-xl text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors duration-300 flex items-center gap-3"
              active-class="text-blue-600 bg-blue-50/30"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path v-if="link.name === 'Edit Counts'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
              </svg>
              {{ link.name }}
            </router-link>

            <!-- Mobile Auth Section -->
            <div v-if="auth.loading" class="glass-card px-4 py-3 rounded-xl">
              <div class="flex items-center gap-2">
                <div class="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
                <span class="text-sm text-gray-600">Loading...</span>
              </div>
            </div>

            <div v-else>
              <div v-if="auth.isAuthenticated" class="flex flex-col gap-2">
                <div class="glass-card px-4 py-3 rounded-xl flex items-center gap-3">
                  <div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white font-semibold shadow-lg">
                    {{ userInitials }}
                  </div>
                  <p class="text-sm text-gray-700 font-medium">{{ auth.user }}</p>
                </div>

                <button @click="auth.logout" class="glass-button px-4 py-3 rounded-xl font-medium text-sm text-gray-700 hover:text-red-600 transition-colors duration-300 flex items-center gap-3">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
                  </svg>
                  Logout
                </button>
              </div>

              <div v-else>
                <button @click="auth.login" class="glass-button-primary w-full px-4 py-3 rounded-xl font-semibold text-sm text-white flex items-center justify-center gap-3 shadow-lg">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"/>
                  </svg>
                  Login
                </button>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </div>
  </nav>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useAuthStore } from "../stores/auth"

const mobileMenuOpen = ref(false)

const auth = useAuthStore()

const userInitials = computed(() => {
  if (!auth.user) return 'U'

  const name = auth.user.trim()
  const words = name.split(' ')

  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase()
  }

  return name.substring(0, 2).toUpperCase()
})

const toggleMobileMenu = () => {
  mobileMenuOpen.value = !mobileMenuOpen.value
}

onMounted(async () => {
  await auth.fetchUser()
  console.log('Auth state:', auth)
  console.log('User:', auth.user)
})

const navLinks = [
  { name: 'Edit Counts', path: '/' },
  { name: 'Editor Counts', path: '/editor-counts' }
]
</script>

<style scoped>
.glass-morphism {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
  
}

.glass-card {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.glass-icon {
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  transition: all 0.3s ease;
  
}

.glass-icon:hover {
  background: rgba(255, 255, 255, 0.4);
}

.glass-hover {
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.4);
}

.glass-button {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
}

.glass-button:hover {
  background: rgba(255, 255, 255, 0.35);
  transform: translateY(-1px);
}

.glass-button:active {
  transform: translateY(0);
}

.glass-button-primary {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.8) 0%, rgba(6, 182, 212, 0.8) 100%);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
}

.glass-button-primary:hover {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.9) 0%, rgba(8, 145, 178, 0.9) 100%);
  transform: translateY(-2px);
}

.glass-button-primary:active {
  transform: translateY(0);
}

.nav-link {
  position: relative;
  overflow: hidden;
}
</style>
