// UAT remediation (Stage R6): the real speechSynthesis-backed speaker for
// SpeechCueQueue, plus the React glue -- mute toggle from preferences, spoken
// language matched to the current UI language (HY's call: best-effort, no locale
// routing/validation beyond what the OS voice table already provides). Malay (ms-MY)
// voice availability varies a lot by OS/browser; where it's missing the platform
// falls back to whatever default voice it has, or silently no-ops -- documented as a
// known limitation in task.md, same spirit as R3's English-only LLM deferral.
import { useEffect, useMemo, useRef } from "react";
import { useTranslation } from "react-i18next";
import { usePreferences } from "../preferences";
import { SpeechCueQueue, type SpeechCueSpeaker } from "../utils/speechCueQueue";
import { pickVoice, toBcp47 } from "../utils/speech";

/** How long to wait for an utterance to actually START before assuming Chrome's
 * speech engine has gone stale. Short cue phrases normally begin within a few
 * hundred ms, so this is generous. */
const SPEAK_START_TIMEOUT_MS = 1500;

function createSpeechSynthesisSpeaker(getLang: () => string): SpeechCueSpeaker {
  let active: SpeechSynthesisUtterance | null = null;
  let watchdogId: number | null = null;

  function clearWatchdog() {
    if (watchdogId !== null) {
      window.clearTimeout(watchdogId);
      watchdogId = null;
    }
  }

  return {
    speak(text, onDone) {
      const synth = typeof window !== "undefined" ? window.speechSynthesis : undefined;
      if (!synth) {
        onDone();
        return;
      }

      let settled = false;
      let started = false;
      let retried = false;

      const settle = () => {
        if (settled) return;
        settled = true;
        clearWatchdog();
        active = null;
        onDone();
      };

      const buildUtterance = () => {
        const utter = new SpeechSynthesisUtterance(text);
        utter.lang = getLang();
        // Set a CONCRETE voice, not just the lang tag -- lang-only silently produces
        // no sound on some setups (see utils/speech.ts). Falls back to lang-only if
        // no matching voice is installed (e.g. ms-MY on most machines).
        const voice = pickVoice(utter.lang);
        if (voice) utter.voice = voice;
        utter.onstart = () => {
          started = true;
          clearWatchdog();
        };
        utter.onend = settle;
        utter.onerror = settle;
        return utter;
      };

      const dispatch = (utter: SpeechSynthesisUtterance) => {
        active = utter;
        // resume() is a harmless no-op when the engine isn't paused, and un-sticks
        // it when it is (a background tab / extension can leave it paused).
        synth.resume();
        synth.speak(utter);
        watchdogId = window.setTimeout(onWatchdogExpired, SPEAK_START_TIMEOUT_MS);
      };

      // Chrome's speech engine can wedge at the BROWSER-process level: speak()
      // returns normally but the utterance never starts, no error fires, and a page
      // reload does NOT clear it (only restarting Chrome does). HY hit exactly this
      // -- STS spoke because its first cue lands ~5s after page load, while
      // squat/SLS/WBLT (first cue 30s+ in, after target-picking / positioning) were
      // silent. A page can't fully cure a wedged engine, but it can (a) try a
      // reset+retry, and (b) never leave the cue queue stalled waiting on an
      // utterance that will never report back.
      function onWatchdogExpired() {
        watchdogId = null;
        if (started || settled) return;
        if (retried) {
          settle();
          return;
        }
        retried = true;
        try {
          synth.cancel();
          synth.resume();
        } catch {
          // Non-critical.
        }
        // Re-speak on a fresh tick -- speak() immediately after cancel() is itself
        // unreliable in Chrome.
        window.setTimeout(() => {
          if (settled) return;
          dispatch(buildUtterance());
        }, 60);
      }

      dispatch(buildUtterance());
    },
    cancel() {
      clearWatchdog();
      // Detach handlers from the active utterance BEFORE cancelling -- browsers are
      // inconsistent about whether cancel() fires onend or onerror on the aborted
      // utterance, and the SpeechCueQueue contract requires cancel() to never
      // trigger the pending onDone (that would double-pump the queue).
      if (active) {
        active.onstart = null;
        active.onend = null;
        active.onerror = null;
        active = null;
      }
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    },
  };
}

export interface SpeechCues {
  /** Urgent, never-throttled cue that interrupts anything currently speaking/queued
   * -- session start/end/leg-transition announcements. */
  speakSession: (key: string, text: string) => void;
  /** Queued + per-key-throttled corrective cue. Every distinct fault key fires --
   * simultaneous faults are all spoken, one after another, never capped to one. */
  speakFault: (key: string, text: string) => void;
  /** Stops speech and drops anything queued -- call on session cancel/navigate-away. */
  stop: () => void;
}

export function useSpeechCues(): SpeechCues {
  const { audioCues } = usePreferences();
  const { i18n } = useTranslation();

  // Always reflects the CURRENT language for the speaker's lazy `getLang()` call,
  // without needing to recreate the queue (and lose its throttle state) on a
  // mid-session language change.
  const langRef = useRef(i18n.language);
  langRef.current = i18n.language;

  const queue = useMemo(() => {
    const speaker = createSpeechSynthesisSpeaker(() => toBcp47(langRef.current));
    return new SpeechCueQueue({
      speaker,
      // Real-browser workaround for the speak()-right-after-cancel() Chrome bug
      // (see SpeechCueQueue's doc) -- only used when genuinely interrupting active
      // speech, which needs a tick for the cancel to actually settle first.
      scheduleAfterCancel: (fn) => {
        window.setTimeout(fn, 0);
      },
    });
    // Deliberately created once per mount -- see the langRef above for how it stays
    // in sync with language changes without a recreate.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    queue.setEnabled(audioCues);
  }, [queue, audioCues]);

  // Deliberately NOT cancelled on unmount. Every page navigates away right after its
  // "session complete" cue fires (finish -> sessionService.end() -> nav to /report),
  // so an unmount-triggered clear() would cut that announcement off before it's ever
  // heard. speechSynthesis is a browser-global queue independent of the React tree --
  // letting it finish across the navigation matches how the existing rep sound
  // effects already behave (nothing pauses them on unmount either). An ABANDONED
  // session (the Cancel button) must still stop speech immediately -- that's `stop()`
  // below, called explicitly from each page's handleCancel, not left to unmount.
  return useMemo(
    () => ({
      speakSession: (key: string, text: string) =>
        queue.enqueue({ key, text, category: "session" }),
      speakFault: (key: string, text: string) => queue.enqueue({ key, text, category: "fault" }),
      stop: () => queue.clear(),
    }),
    [queue],
  );
}
