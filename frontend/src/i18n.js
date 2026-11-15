import { createI18n, useI18n } from 'vue-banana-i18n'

export const DEFAULT_LOCALE = 'en'

// One catalogue per language in ./locales, named after its language code.
// qqq.json is left out: it documents the messages for translators.
const catalogues = import.meta.glob('./locales/!(qqq).json', {
  eager: true,
  import: 'default'
})

const messages = {}
for (const [path, catalogue] of Object.entries(catalogues)) {
  const code = path.slice(path.lastIndexOf('/') + 1, -'.json'.length)
  messages[code] = catalogue
}

// The languages the interface can be shown in: the ones that have a catalogue.
export const SUPPORTED_LOCALES = Object.keys(messages)

const i18n = createI18n({
  locale: DEFAULT_LOCALE,
  finalFallback: DEFAULT_LOCALE,
  messages
})

export { useI18n }
export default i18n
