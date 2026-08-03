// Shared Web Speech helpers.
//
// Chrome can block speech started only from timers or async callbacks. Prime speech
// during a user gesture, then reuse the same queue for countdown and pose callbacks.
//
// Fix, layered:
//   1. `primeSpeechSynthesis()` on the FIRST user interaction anywhere in the app
//      (a one-shot pointerdown/keydown listener installed at module load) -- speaks
//      a silent utterance inside that gesture to establish activation app-wide,
//      regardless of which page reaches a cue first.
//   2. `pickVoice()` -- select a CONCRETE SpeechSynthesisVoice matching the language
//      rather than relying on `utterance.lang` alone, which silently produces no
//      sound on some setups. Voices load async, so the list is warmed + refreshed on
//      the `voiceschanged` event.
//   3. `speakOnce()` -- a one-off speak used by the audio toggle to say a confirmation
//      when the user switches cues ON: audible self-test + in-gesture activation.

const LANG_BCP47: Record<string, string> = {
  en: "en-US",
  zh: "zh-CN",
  ms: "ms-MY",
};

/** Maps an i18next language code (e.g. "en", "zh-CN") to a BCP-47 tag for TTS. */
export function toBcp47(i18nLang: string): string {
  return LANG_BCP47[i18nLang.split("-")[0]] ?? "en-US";
}

function getSynth(): SpeechSynthesis | undefined {
  return typeof window !== "undefined" ? window.speechSynthesis : undefined;
}

let cachedVoices: SpeechSynthesisVoice[] = [];
function refreshVoices(): void {
  const synth = getSynth();
  if (synth) cachedVoices = synth.getVoices();
}

const synthAtLoad = getSynth();
if (synthAtLoad) {
  refreshVoices();
  synthAtLoad.addEventListener?.("voiceschanged", refreshVoices);
}

/** Best concrete voice for a BCP-47 tag: exact lang match, else same base language. */
export function pickVoice(langBcp47: string): SpeechSynthesisVoice | null {
  if (!cachedVoices.length) refreshVoices();
  const target = langBcp47.toLowerCase();
  const base = target.split("-")[0];
  return (
    cachedVoices.find((v) => v.lang?.toLowerCase() === target) ??
    cachedVoices.find((v) => v.lang?.toLowerCase().startsWith(base)) ??
    null
  );
}

let primed = false;
/** Unlocks speechSynthesis by speaking a silent utterance. MUST be reachable from a
 * user gesture (a click/keypress handler) the first time to satisfy Chrome's
 * user-activation gate; harmless (and a no-op after the first success) otherwise. */
export function primeSpeechSynthesis(): void {
  const synth = getSynth();
  if (!synth || primed) return;
  primed = true;
  try {
    if (synth.paused) synth.resume();
    const utter = new SpeechSynthesisUtterance(" ");
    utter.volume = 0;
    synth.speak(utter);
  } catch {
    // Non-critical — a failed prime just means later speaks fall back to whatever
    // the browser allows.
  }
}

// Establish activation as early as possible, app-wide, on the very first interaction.
if (typeof document !== "undefined") {
  const onFirstInteraction = () => {
    primeSpeechSynthesis();
    document.removeEventListener("pointerdown", onFirstInteraction, true);
    document.removeEventListener("keydown", onFirstInteraction, true);
  };
  document.addEventListener("pointerdown", onFirstInteraction, true);
  document.addEventListener("keydown", onFirstInteraction, true);
}

/** Fire-and-forget single utterance, bypassing the cue queue. Used for the audio
 * toggle's spoken confirmation (an in-gesture self-test that TTS actually works). */
export function speakOnce(text: string, langBcp47: string): void {
  const synth = getSynth();
  if (!synth) return;
  try {
    if (synth.paused) synth.resume();
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = langBcp47;
    const voice = pickVoice(langBcp47);
    if (voice) utter.voice = voice;
    synth.speak(utter);
  } catch {
    // Non-critical.
  }
}
