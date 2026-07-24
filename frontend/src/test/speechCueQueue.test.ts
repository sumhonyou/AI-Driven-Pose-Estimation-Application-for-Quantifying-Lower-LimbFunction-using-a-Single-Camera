// UAT remediation (Stage R6): coverage for SpeechCueQueue's priority/throttle/
// interrupt logic, using a mock speaker so no real speechSynthesis is needed.
import { describe, expect, it } from "vitest";
import { SpeechCueQueue, type SpeechCueSpeaker } from "../utils/speechCueQueue";

function mockSpeaker() {
  const spoken: string[] = [];
  const cancelled: number[] = [];
  let pendingOnDone: (() => void) | null = null;

  const speaker: SpeechCueSpeaker = {
    speak(text, onDone) {
      spoken.push(text);
      pendingOnDone = onDone;
    },
    cancel() {
      cancelled.push(spoken.length);
      pendingOnDone = null;
    },
  };

  return {
    speaker,
    spoken,
    cancelled,
    /** Simulates the current utterance finishing naturally. */
    finish() {
      const done = pendingOnDone;
      pendingOnDone = null;
      done?.();
    },
  };
}

describe("SpeechCueQueue fault sequencing", () => {
  it("speaks two simultaneous, distinct-key fault cues one after another", () => {
    const { speaker, spoken, finish } = mockSpeaker();
    const q = new SpeechCueQueue({ speaker });

    q.enqueue({ key: "insufficient_depth", text: "Go deeper", category: "fault" });
    q.enqueue({ key: "excessive_forward_lean", text: "Chest up", category: "fault" });

    expect(spoken).toEqual(["Go deeper"]);
    finish();
    expect(spoken).toEqual(["Go deeper", "Chest up"]);
  });

  it("speaks three simultaneous faults, none dropped", () => {
    const { speaker, spoken, finish } = mockSpeaker();
    const q = new SpeechCueQueue({ speaker });

    q.enqueue({ key: "insufficient_depth", text: "Go deeper", category: "fault" });
    q.enqueue({ key: "excessive_forward_lean", text: "Chest up", category: "fault" });
    q.enqueue({ key: "heel_lift", text: "Heels down", category: "fault" });

    finish();
    finish();
    expect(spoken).toEqual(["Go deeper", "Chest up", "Heels down"]);
  });
});

describe("SpeechCueQueue per-key fault throttle", () => {
  it("suppresses a repeat of the same key within the throttle window", () => {
    const { speaker, spoken, finish } = mockSpeaker();
    let t = 0;
    const q = new SpeechCueQueue({ speaker, now: () => t, faultThrottleMs: 4000 });

    q.enqueue({ key: "heel_lift", text: "Heels down", category: "fault" });
    finish();
    t = 1000; // still inside the 4s window
    q.enqueue({ key: "heel_lift", text: "Heels down", category: "fault" });

    expect(spoken).toEqual(["Heels down"]);
  });

  it("allows a repeat of the same key once the throttle window has elapsed", () => {
    const { speaker, spoken, finish } = mockSpeaker();
    let t = 0;
    const q = new SpeechCueQueue({ speaker, now: () => t, faultThrottleMs: 4000 });

    q.enqueue({ key: "heel_lift", text: "Heels down", category: "fault" });
    finish();
    t = 4001;
    q.enqueue({ key: "heel_lift", text: "Heels down", category: "fault" });

    expect(spoken).toEqual(["Heels down", "Heels down"]);
  });

  it("does not double-queue the same key while it is still waiting to be spoken", () => {
    const { speaker, spoken } = mockSpeaker();
    const q = new SpeechCueQueue({ speaker });

    q.enqueue({ key: "insufficient_depth", text: "Go deeper", category: "fault" });
    // Same key fires again before the first has even started speaking's onDone.
    q.enqueue({ key: "insufficient_depth", text: "Go deeper", category: "fault" });

    expect(spoken).toEqual(["Go deeper"]);
  });

  it("a different key is never suppressed by another key's throttle", () => {
    const { speaker, spoken, finish } = mockSpeaker();
    let t = 0;
    const q = new SpeechCueQueue({ speaker, now: () => t, faultThrottleMs: 4000 });

    q.enqueue({ key: "heel_lift", text: "Heels down", category: "fault" });
    finish();
    t = 500;
    q.enqueue({ key: "wrong_leg", text: "Wrong leg", category: "fault" });

    expect(spoken).toEqual(["Heels down", "Wrong leg"]);
  });
});

describe("SpeechCueQueue session-cue interruption", () => {
  it("a session cue cancels in-progress speech and speaks immediately", () => {
    const { speaker, spoken, cancelled } = mockSpeaker();
    const q = new SpeechCueQueue({ speaker });

    q.enqueue({ key: "heel_lift", text: "Heels down", category: "fault" });
    expect(spoken).toEqual(["Heels down"]);

    q.enqueue({ key: "session_start", text: "Starting", category: "session" });
    expect(cancelled.length).toBe(1);
    expect(spoken).toEqual(["Heels down", "Starting"]);
  });

  it("a session cue drops anything still waiting in the fault queue", () => {
    const { speaker, spoken, finish } = mockSpeaker();
    const q = new SpeechCueQueue({ speaker });

    q.enqueue({ key: "insufficient_depth", text: "Go deeper", category: "fault" });
    q.enqueue({ key: "excessive_forward_lean", text: "Chest up", category: "fault" });
    q.enqueue({ key: "session_end", text: "Set complete", category: "session" });

    expect(spoken).toEqual(["Go deeper", "Set complete"]);
    finish();
    // "Chest up" was dropped by the interrupt -- finishing "Set complete" must not
    // resurrect it.
    expect(spoken).toEqual(["Go deeper", "Set complete"]);
  });

  it("the aborted utterance's onDone never fires after cancel()", () => {
    // Simulates a real SpeechSynthesis speaker: cancel() does NOT invoke onDone.
    // The mock speaker here already honours that contract (pendingOnDone is
    // discarded on cancel), so this asserts the queue never double-pumps.
    const { speaker, spoken, cancelled } = mockSpeaker();
    const q = new SpeechCueQueue({ speaker });

    q.enqueue({ key: "heel_lift", text: "Heels down", category: "fault" });
    q.enqueue({ key: "session_end", text: "Set complete", category: "session" });

    expect(cancelled.length).toBe(1);
    expect(spoken).toEqual(["Heels down", "Set complete"]);
  });

  // Regression coverage for the "no audio at all" bug: enqueue() used to call
  // cancel() unconditionally for every session cue, even with nothing active --
  // e.g. every session's very first "Starting" announcement. Calling speak() in the
  // same synchronous tick as cancel() is a documented Chrome bug that silently
  // drops the new utterance (no sound, no error). Fixed by only cancelling when
  // there is genuinely something to interrupt.
  it("a session cue with nothing active never calls cancel()", () => {
    const { speaker, spoken, cancelled } = mockSpeaker();
    const q = new SpeechCueQueue({ speaker });

    q.enqueue({ key: "session_start", text: "Starting", category: "session" });

    expect(cancelled.length).toBe(0);
    expect(spoken).toEqual(["Starting"]);
  });

  it("a genuine interrupt defers the follow-up speak via scheduleAfterCancel", () => {
    const { speaker, spoken, cancelled } = mockSpeaker();
    const deferred: Array<() => void> = [];
    const q = new SpeechCueQueue({
      speaker,
      scheduleAfterCancel: (fn) => deferred.push(fn),
    });

    q.enqueue({ key: "heel_lift", text: "Heels down", category: "fault" });
    q.enqueue({ key: "session_start", text: "Starting", category: "session" });

    // cancel() has fired, but the re-speak is deferred -- not yet spoken.
    expect(cancelled.length).toBe(1);
    expect(spoken).toEqual(["Heels down"]);
    expect(deferred.length).toBe(1);

    deferred[0]();
    expect(spoken).toEqual(["Heels down", "Starting"]);
  });
});

describe("SpeechCueQueue mute (setEnabled)", () => {
  it("disabling clears the queue and cancels in-progress speech", () => {
    const { speaker, spoken, cancelled } = mockSpeaker();
    const q = new SpeechCueQueue({ speaker });

    q.enqueue({ key: "heel_lift", text: "Heels down", category: "fault" });
    q.setEnabled(false);

    expect(cancelled.length).toBe(1);
    expect(spoken).toEqual(["Heels down"]);
  });

  it("enqueue while disabled is a no-op", () => {
    const { speaker, spoken } = mockSpeaker();
    const q = new SpeechCueQueue({ speaker });

    q.setEnabled(false);
    q.enqueue({ key: "heel_lift", text: "Heels down", category: "fault" });
    q.enqueue({ key: "session_start", text: "Starting", category: "session" });

    expect(spoken).toEqual([]);
  });

  it("re-enabling allows new cues to speak again", () => {
    const { speaker, spoken } = mockSpeaker();
    const q = new SpeechCueQueue({ speaker });

    q.setEnabled(false);
    q.setEnabled(true);
    q.enqueue({ key: "heel_lift", text: "Heels down", category: "fault" });

    expect(spoken).toEqual(["Heels down"]);
  });
});
