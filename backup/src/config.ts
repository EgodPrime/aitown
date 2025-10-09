// Centralized configuration values
const DEFAULT_PROMPT_MAX_LENGTH = 5000;

export const PROMPT_MAX_LENGTH = (() => {
  const envVal = process.env.PROMPT_MAX_LENGTH;
  if (!envVal) return DEFAULT_PROMPT_MAX_LENGTH;
  const parsed = parseInt(envVal, 10);
  if (isNaN(parsed) || parsed <= 0) return DEFAULT_PROMPT_MAX_LENGTH;
  return parsed;
})();

// Simulation clock configuration
export const SIM_CONFIG = {
  // default: 36 minutes in milliseconds
  simDayDurationMs: (() => {
    const env = process.env.SIM_DAY_DURATION_MS;
    if (!env) return 36 * 60 * 1000;
    const parsed = parseInt(env, 10);
    return isNaN(parsed) || parsed <= 0 ? 36 * 60 * 1000 : parsed;
  })(),
  dayRolloverToleranceMs: (() => {
    const env = process.env.SIM_DAY_ROLLOVER_TOLERANCE_MS;
    if (!env) return 1000; // 1s tolerance by default
    const parsed = parseInt(env, 10);
    return isNaN(parsed) || parsed < 0 ? 1000 : parsed;
  })(),
  dayEndHandlerTimeoutMs: (() => {
    const env = process.env.SIM_DAY_END_HANDLER_TIMEOUT_MS;
    if (!env) return 1000; // 1s default handler window
    const parsed = parseInt(env, 10);
    return isNaN(parsed) || parsed < 0 ? 1000 : parsed;
  })(),
  // feature flag for guarantee credit transaction
  enable_guarantee_credit: (() => {
    const env = process.env.SIM_ENABLE_GUARANTEE_CREDIT;
    if (!env) return false;
    return env === '1' || env.toLowerCase() === 'true';
  })(),
  // decision generation interval
  decisionIntervalMs: (() => {
    const env = process.env.SIM_DECISION_INTERVAL_MS;
    if (!env) return 90 * 1000; // 90s default
    const parsed = parseInt(env, 10);
    return isNaN(parsed) || parsed <= 0 ? 90 * 1000 : parsed;
  })()
};

// LLM adapter timeout (ms) default 5000
export const LLM_CONFIG = {
  llmTimeoutMs: (() => {
    const env = process.env.LLM_TIMEOUT_MS;
    if (!env) return 5000;
    const parsed = parseInt(env, 10);
    return isNaN(parsed) || parsed <= 0 ? 5000 : parsed;
  })()
};

export default {
  PROMPT_MAX_LENGTH,
  SIM_CONFIG
};
