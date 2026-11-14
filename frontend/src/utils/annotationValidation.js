
export const DESCRIPTION_MIN_CHARS = 10;
export const DESCRIPTION_MAX_WORDS = 50;

export const FORM_ERROR_MESSAGE = "Please fix the fields with errors.";

/**
 * Count whitespace-separated words in a string.
 * @param {string} text
 * @returns {number}
 */
export function countWords(text) {
  const value = (text ?? "").trim();
  return value ? value.split(/\s+/).length : 0;
}

/**
 * Validate a required annotation description.
 * @param {string} raw
 * @returns {{ valid: boolean, error: string | null }}
 */
export function validateDescription(raw) {
  const value = (raw ?? "").trim();

  if (!value) {
    return { valid: false, error: "Description is required." };
  }
  if (value.length < DESCRIPTION_MIN_CHARS) {
    return {
      valid: false,
      error: `Description must be at least ${DESCRIPTION_MIN_CHARS} characters.`,
    };
  }
  if (countWords(value) > DESCRIPTION_MAX_WORDS) {
    return {
      valid: false,
      error: `Description must be ${DESCRIPTION_MAX_WORDS} words or fewer.`,
    };
  }
  return { valid: true, error: null };
}


// Domains operated by the Wikimedia Foundation that host wikis.
// A link is accepted if its hostname is one of these or a subdomain of one
// (e.g. en.wikipedia.org, commons.wikimedia.org, fr.m.wiktionary.org).
export const WIKIMEDIA_DOMAINS = [
  "wikipedia.org",
  "wiktionary.org",
  "wikibooks.org",
  "wikinews.org",
  "wikiquote.org",
  "wikisource.org",
  "wikiversity.org",
  "wikivoyage.org",
  "wikimedia.org",
  "wikidata.org",
  "mediawiki.org",
  "wikifunctions.org",
];

export const INVALID_URL_MESSAGE =
  "Please enter a valid URL starting with https:// (e.g. https://en.wikipedia.org/wiki/Example).";
export const NON_WIKIMEDIA_MESSAGE =
  "Only links to Wikimedia wikis are allowed (e.g. Wikipedia, Meta-Wiki, Commons, Wikidata).";

/**
 * Validate an optional annotation link.
 * Empty input is valid (the field is optional).
 * @param {string} raw
 * @returns {{ valid: boolean, error: string | null }}
 */
export function validateWikimediaLink(raw) {
  const value = (raw ?? "").trim();
  if (!value) return { valid: true, error: null };

  let url;
  try {
    url = new URL(value);
  } catch {
    return { valid: false, error: INVALID_URL_MESSAGE };
  }

  if (url.protocol !== "https:") {
    return { valid: false, error: INVALID_URL_MESSAGE };
  }

  // Reject embedded credentials (https://user:pass@host) as a precaution.
  if (url.username || url.password) {
    return { valid: false, error: NON_WIKIMEDIA_MESSAGE };
  }

  const hostname = url.hostname.toLowerCase().replace(/\.$/, "");
  const isWikimedia = WIKIMEDIA_DOMAINS.some(
    (domain) => hostname === domain || hostname.endsWith(`.${domain}`),
  );

  return isWikimedia
    ? { valid: true, error: null }
    : { valid: false, error: NON_WIKIMEDIA_MESSAGE };
}
