// UAT remediation (Stage R6): a framework-free, fully-testable priority queue for
// spoken live cues. Deliberately has no dependency on `speechSynthesis` -- that lets
// the queue/priority/throttle logic run under vitest (no real speech engine in that
// environment), with the actual Web Speech API wired in separately by an injected
// `SpeechCueSpeaker` (see hooks/useSpeechCues.ts for the real one).
//
// Two categories, two policies:
//   - "session": urgent, never throttled. Interrupts (cancels) whatever is currently
//     speaking or queued, so "Starting"/"Set complete" is never delayed or dropped.
//   - "fault": queued and spoken sequentially (via onDone chaining), so if several
//     distinct faults fire together (e.g. squat's depth + lean gates on the same rep,
//     or SLS's wrong-leg signal alongside another cue), EVERY one is read aloud, one
//     after another -- never capped to just the first/primary. Throttled per-KEY only
//     (e.g. the same standing fault tag) so a fault that keeps re-firing every frame
//     isn't repeated faster than `faultThrottleMs`; a genuinely different key is never
//     dropped by this throttle. (throttle means don't repeat the same cue within a certain time period)

// This define the queue logic
export type SpeechCueCategory = "session" | "fault";

export interface SpeechCue {
  /** Stable identity for per-key throttling (e.g. a fault tag like "heel_lift"). */
  key: string;
  text: string;
  category: SpeechCueCategory;
}

export interface SpeechCueSpeaker {
  /** Speak `text`; MUST call `onDone` exactly once when speech naturally finishes. */
  speak(text: string, onDone: () => void): void;
  /** Stop in-progress speech immediately. MUST NOT call the pending `onDone`. */
  cancel(): void;
}

const DEFAULT_FAULT_THROTTLE_MS = 4000;

export interface SpeechCueQueueOptions {
  speaker: SpeechCueSpeaker;
  /** Injectable clock for deterministic throttle tests. Defaults to Date.now. */
  now?: () => number;
  faultThrottleMs?: number;
  /**
   * Schedules a callback to run AFTER an active speech cancel(), giving the
   * browser's cancel a tick to actually settle before the next speak() call.
   * Calling speak() in the same synchronous task as cancel() is a well-documented
   * Chrome bug -- the new utterance is silently dropped (no audio, no error, no
   * onstart/onend). Defaults to synchronous execution (deterministic for tests,
   * and harmless for a mock speaker); the real hook overrides this to
   * `(fn) => setTimeout(fn, 0)`. Only used when there was actually something to
   * interrupt -- the far more common "nothing was speaking yet" path never calls
   * cancel() at all (see enqueue() below), so it never needs this deferral.
   */
  scheduleAfterCancel?: (fn: () => void) => void;
}

export class SpeechCueQueue {
  private readonly speaker: SpeechCueSpeaker;
  private readonly now: () => number;
  private readonly faultThrottleMs: number;
  private readonly scheduleAfterCancel: (fn: () => void) => void;
  private queue: SpeechCue[] = [];
  private speaking = false;
  private readonly lastSpokenAt = new Map<string, number>();
  private enabled = true;

  constructor(opts: SpeechCueQueueOptions) {
    this.speaker = opts.speaker;
    this.now = opts.now ?? (() => Date.now());
    this.faultThrottleMs = opts.faultThrottleMs ?? DEFAULT_FAULT_THROTTLE_MS;
    this.scheduleAfterCancel = opts.scheduleAfterCancel ?? ((fn) => fn());
  }

  /** Mute toggle. Disabling immediately stops speech and drops anything queued. */
  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
    if (!enabled) this.clear();
  }

  /** Drops the pending queue and stops any speech in progress right away. */
  clear(): void {
    this.queue = [];
    this.speaking = false;
    this.speaker.cancel();
  }
 // Add a new spoken cue into the system
  enqueue(cue: SpeechCue): void {
    if (!this.enabled) return;

    if (cue.category === "session") {
      const wasActive = this.speaking || this.queue.length > 0;
      this.queue = [cue];
      this.speaking = false;
      if (wasActive) {
        this.speaker.cancel();
        this.scheduleAfterCancel(() => this.pump());
      } else {
        this.pump();
      }
      return;
    }

    const last = this.lastSpokenAt.get(cue.key);
    if (last !== undefined && this.now() - last < this.faultThrottleMs) return;
    if (this.queue.some((q) => q.key === cue.key)) return;

    this.queue.push(cue);
    this.pump();
  }

  // Start speaking the next cue in the queue, if nothing is currently speaking. 
  // When one finishes, it calls itself again to play the next one.
  private pump(): void {
    if (this.speaking || this.queue.length === 0) return;
    const cue = this.queue.shift();
    if (!cue) return;
    this.speaking = true;
    this.lastSpokenAt.set(cue.key, this.now());
    this.speaker.speak(cue.text, () => {
      this.speaking = false;
      this.pump();
    });
  }
}
