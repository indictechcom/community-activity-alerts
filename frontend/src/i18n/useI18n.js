import { getCurrentInstance } from 'vue'

export function useI18n() {
  const instance = getCurrentInstance()
  const $i18n = instance.appContext.config.globalProperties.$i18n

  return {
    t: (key, ...params) => $i18n(key, ...params)
  }
}
