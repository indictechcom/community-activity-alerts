<template>
  <cdx-menu-button
    v-model:selected="selected"
    :menu-items="menuItems"
    :aria-label="`Language: ${currentName}`"
    class="language-selector"
  >
    <cdx-icon :icon="cdxIconLanguage" />
    <span v-if="showName" :lang="localeStore.locale">{{ currentName }}</span>
  </cdx-menu-button>
</template>

<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { CdxMenuButton, CdxIcon } from '@wikimedia/codex'
import { cdxIconLanguage } from '@wikimedia/codex-icons'
import { useLocaleStore, nativeLanguageName } from '../stores/locale'

const props = defineProps({
  // Icon-only below Tailwind's lg breakpoint, where the desktop navbar is tight.
  // The name is left out of the slot (not just hidden) so Codex renders a
  // proper icon-only button.
  compact: { type: Boolean, default: false }
})

const wideQuery = window.matchMedia('(min-width: 1024px)')
const isWide = ref(wideQuery.matches)
const onWidthChange = (e) => { isWide.value = e.matches }
onMounted(() => wideQuery.addEventListener('change', onWidthChange))
onBeforeUnmount(() => wideQuery.removeEventListener('change', onWidthChange))

const showName = computed(() => !props.compact || isWide.value)

const localeStore = useLocaleStore()

const selected = computed({
  get: () => localeStore.locale,
  set: (code) => localeStore.setLocale(code)
})

const currentName = computed(() => nativeLanguageName(localeStore.locale))

const menuItems = computed(() =>
  localeStore.languages.map(({ code, name }) => ({
    value: code,
    label: name,
    language: { label: code }
  }))
)
</script>
