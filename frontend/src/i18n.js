import { createI18n } from 'vue-banana-i18n'
import en from './locales/en.json'
import fr from './locales/fr.json'

const i18n = createI18n({
  locale: 'en',
  fallbackLocale: 'en',
  messages: { en , fr}
})

export default i18n
