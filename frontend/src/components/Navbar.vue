<template>
  <header class="codex-navbar fixed top-0 left-0 right-0 z-50 border-b">
    <div class="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        
        <!-- Logo & Title Area -->
        <div class="flex items-center gap-3">
          <div class="logo-container text-blue-600">
             <cdx-icon :icon="cdxIconLogo" size="medium" />
          </div>
          <h1 class="text-lg font-bold text-gray-900 tracking-tight">
            Community Activity Alerts
          </h1>
        </div>

        <!-- Desktop Navigation -->
        <div class="hidden md:flex items-center gap-2">
          <template v-for="link in navLinks" :key="link.path">
            <router-link :to="link.path" custom v-slot="{ navigate, href, isActive }">
              <cdx-button
                :href="href"
                @click="navigate"
                :action="isActive ? 'progressive' : 'default'"
                weight="quiet"
                class="nav-item"
              >
                <template #icon>
                   <cdx-icon :icon="link.name === 'Edit Counts' ? cdxIconEdit : cdxIconUserGroup" />
                </template>
                {{ link.name }}
              </cdx-button>
            </router-link>
          </template>

          <div class="w-px h-6 bg-gray-200 mx-2"></div>

          <!-- Auth Section -->
          <div v-if="auth.loading" class="flex items-center gap-2 px-3">
            <span class="animate-pulse w-4 h-4 bg-gray-200 rounded-full"></span>
            <span class="text-sm text-gray-500">Loading...</span>
          </div>

          <div v-else class="flex items-center gap-2">
            <!-- Logged In -->
            <template v-if="auth.isAuthenticated">
              <div class="flex items-center gap-2 px-2 py-1 bg-gray-100 rounded-md border border-gray-200">
                <cdx-icon :icon="cdxIconUserAvatar" class="text-gray-500" />
                <span class="text-sm font-medium text-gray-700">{{ userInitials }}</span>
              </div>

              <cdx-button 
                @click="auth.logout" 
                weight="quiet" 
                action="destructive"
              >
                <template #icon>
                  <cdx-icon :icon="cdxIconLogOut" />
                </template>
                Logout
              </cdx-button>
            </template>

            <!-- Not Logged In -->
            <template v-else>
              <cdx-button 
                @click="auth.login" 
                action="progressive" 
                weight="primary"
              >
                <template #icon>
                  <cdx-icon :icon="cdxIconLogIn" />
                </template>
                Login
              </cdx-button>
            </template>
          </div>
        </div>

        <!-- Mobile Menu Button -->
        <div class="md:hidden">
          <cdx-button
            weight="quiet"
            @click="toggleMobileMenu"
            :aria-label="mobileMenuOpen ? 'Close menu' : 'Open menu'"
          >
            <template #icon>
              <cdx-icon :icon="mobileMenuOpen ? cdxIconClose : cdxIconMenu" />
            </template>
          </cdx-button>
        </div>
      </div>
    </div>

    <!-- Mobile Menu Dropdown -->
    <transition
      enter-active-class="transition duration-100 ease-out"
      enter-from-class="transform scale-95 opacity-0"
      enter-to-class="transform scale-100 opacity-100"
      leave-active-class="transition duration-75 ease-in"
      leave-from-class="transform scale-100 opacity-100"
      leave-to-class="transform scale-95 opacity-0"
    >
      <div v-if="mobileMenuOpen" class="md:hidden border-t bg-white shadow-lg">
        <div class="px-4 pt-2 pb-4 space-y-1">
          <router-link
            v-for="link in navLinks"
            :key="link.path"
            :to="link.path"
            @click="mobileMenuOpen = false"
            class="block"
            custom
            v-slot="{ navigate, href, isActive }"
          >
             <cdx-button
                :href="href"
                @click="navigate"
                :action="isActive ? 'progressive' : 'default'"
                weight="quiet"
                class="w-full justify-start mb-1"
              >
                <template #icon>
                   <cdx-icon :icon="link.name === 'Edit Counts' ? cdxIconEdit : cdxIconUserGroup" />
                </template>
                {{ link.name }}
              </cdx-button>
          </router-link>

          <div class="border-t border-gray-100 my-2 pt-2">
            <!-- Mobile Auth -->
            <div v-if="auth.loading" class="px-4 py-2 text-sm text-gray-500">
              Loading...
            </div>
            <div v-else>
              <div v-if="auth.isAuthenticated" class="space-y-2">
                <div class="flex items-center gap-2 px-4 py-2">
                  <cdx-icon :icon="cdxIconUserAvatar" />
                  <span class="font-medium">{{ auth.user }}</span>
                </div>
                <cdx-button 
                  class="w-full justify-start" 
                  weight="quiet" 
                  action="destructive"
                  @click="auth.logout"
                >
                  <template #icon><cdx-icon :icon="cdxIconLogOut" /></template>
                  Logout
                </cdx-button>
              </div>
              <div v-else class="px-2">
                <cdx-button 
                  class="w-full" 
                  action="progressive" 
                  weight="primary"
                  @click="auth.login"
                >
                  <template #icon><cdx-icon :icon="cdxIconLogIn" /></template>
                  Login
                </cdx-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </header>
  <!-- Spacer to prevent content overlap since header is fixed -->
  <div class="h-16"></div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useAuthStore } from "../stores/auth"

// 1. COMPONENT-WISE IMPORTS
import { CdxButton, CdxIcon } from '@wikimedia/codex'

// 2. ICON IMPORTS
import { 
  cdxIconEdit, 
  cdxIconUserGroup, 
  cdxIconLogIn, 
  cdxIconLogOut,
  cdxIconMenu,
  cdxIconClose,
  cdxIconUserAvatar,
  cdxIconWikitext // Using this as a generic logo placeholder
} from '@wikimedia/codex-icons'

// Renaming the logo icon for clarity in template
const cdxIconLogo = cdxIconWikitext

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
})

const navLinks = [
  { name: 'Edit Counts', path: '/' },
  { name: 'Editor Counts', path: '/editor-counts' }
]
</script>

<style scoped>
/* CODEX AUTHENTICITY 
   We use CSS variables provided by Codex to ensure the colors 
   automatically match standard Wikimedia themes (and Dark Mode if enabled).
*/

.codex-navbar {
  background-color: var(--background-color-base);
  border-bottom-color: var(--border-color-subtle);
  /* Fallback for safety if CSS tokens aren't loaded yet */
  background-color: #ffffff; 
}

/* Override specific Tailwind utilities with Codex tokens 
   where exact Wiki-compliance is needed 
*/

.text-gray-900 {
  color: var(--color-base, #202122);
}

.text-gray-500 {
  color: var(--color-subtle, #54595d);
}

.bg-gray-100 {
  background-color: var(--background-color-interactive-subtle, #f8f9fa);
}

.border-gray-200 {
  border-color: var(--border-color-subtle, #c8ccd1);
}
</style>