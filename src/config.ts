// Centralized configuration values
const DEFAULT_PROMPT_MAX_LENGTH = 5000;

export const PROMPT_MAX_LENGTH = (() => {
  const envVal = process.env.PROMPT_MAX_LENGTH;
  if (!envVal) return DEFAULT_PROMPT_MAX_LENGTH;
  const parsed = parseInt(envVal, 10);
  if (isNaN(parsed) || parsed <= 0) return DEFAULT_PROMPT_MAX_LENGTH;
  return parsed;
})();

export default {
  PROMPT_MAX_LENGTH
};
