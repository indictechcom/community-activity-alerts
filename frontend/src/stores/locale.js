import { defineStore } from "pinia";
import { ref } from "vue";

export const DEFAULT_LOCALE = "en";
export const LOCALE_STORAGE_KEY = "community-alerts:locale";

// Interface languages the user can pick from, as BCP 47 codes. The i18n setup
// owns this list: add a code here when its message catalogue is added.
export const SUPPORTED_LOCALES = ["en"];

export function isSupportedLocale(code) {
    return SUPPORTED_LOCALES.includes(code);
}

// The language's name in that language ("Français", "हिन्दी"), from the
// browser's CLDR data, so no list of names has to be maintained by hand.
export function nativeLanguageName(code) {
    try {
        const name = new Intl.DisplayNames([code], { type: "language" }).of(code);
        return name.replace(/^\p{Ll}/u, (first) => first.toLocaleUpperCase(code));
    } catch {
        return code;
    }
}

function readSavedLocale() {
    try {
        const saved = window.localStorage.getItem(LOCALE_STORAGE_KEY);
        return isSupportedLocale(saved) ? saved : DEFAULT_LOCALE;
    } catch {
        return DEFAULT_LOCALE;
    }
}

function saveLocale(code) {
    try {
        window.localStorage.setItem(LOCALE_STORAGE_KEY, code);
    } catch {
        // The choice still applies for this visit; it just won't be remembered.
    }
}

// Single source of truth for the active interface locale. The i18n library
// should follow `locale` (e.g. watch it and set its own active locale).
export const useLocaleStore = defineStore("locale", () => {
    const locale = ref(readSavedLocale());

    const languages = SUPPORTED_LOCALES.map((code) => ({
        code,
        name: nativeLanguageName(code),
    }));

    function setLocale(code) {
        if (!isSupportedLocale(code)) return;
        locale.value = code;
        saveLocale(code);
    }

    return { locale, languages, setLocale };
});
