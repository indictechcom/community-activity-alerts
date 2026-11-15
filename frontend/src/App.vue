<template>
  <router-view />
</template>

<script setup>
import { watch } from 'vue'
import './style.css'
import { useI18n } from './i18n'
import { useLocaleStore } from './stores/locale'

// Banana and the page follow the language chosen in the navbar.
const banana = useI18n()
const localeStore = useLocaleStore()
watch(
  () => localeStore.locale,
  (locale) => {
    banana.setLocale(locale)
    document.documentElement.lang = locale
  },
  { immediate: true }
)
</script>
