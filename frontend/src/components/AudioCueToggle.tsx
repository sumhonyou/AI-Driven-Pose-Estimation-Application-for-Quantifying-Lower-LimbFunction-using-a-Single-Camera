// UAT remediation (Stage R6): mute/unmute control for spoken live cues. Dropped into
// every live session page's topbar (where the cues actually play) AND the shared
// DashTopbar (layouts/DashboardLayout.tsx) for out-of-session discoverability --
// testers never found the existing font-size control when it was topbar-only either
// (R14's finding), so this is deliberately visible outside the live pages too.
import { useTranslation } from "react-i18next";
import { usePreferences } from "../preferences";
import { primeSpeechSynthesis, speakOnce, toBcp47 } from "../utils/speech";
import { Volume2, VolumeX } from "./Icons";
import CtrlHint from "./CtrlHint";

export default function AudioCueToggle() {
  const { audioCues, toggleAudioCues } = usePreferences();
  const { t, i18n } = useTranslation();
  const label = t(audioCues ? "nav.audioCuesOn" : "nav.audioCuesOff");

  function handleToggle() {
    const willEnable = !audioCues;
    toggleAudioCues();
    // Turning cues ON speaks a short confirmation RIGHT HERE, inside the click
    // handler. This does double duty: (1) it's an audible self-test -- if the user
    // hears "Voice cues on", TTS works on their machine; if not, the problem is
    // their system voices, not the app; (2) it satisfies Chrome's user-activation
    // gate from within a real gesture, unlocking the later timer-driven cues that
    // otherwise never establish activation (see utils/speech.ts). Priming first
    // covers the case where no voice is installed (silent unlock still happens).
    if (willEnable) {
      primeSpeechSynthesis();
      speakOnce(t("nav.audioCuesOn"), toBcp47(i18n.language));
    }
  }

  return (
    <CtrlHint text={t("nav.audioCuesHint")}>
      <button
        type="button"
        className="ctrl icon-btn"
        onClick={handleToggle}
        aria-pressed={audioCues}
        aria-label={label}
      >
        {audioCues ? <Volume2 /> : <VolumeX />}
      </button>
    </CtrlHint>
  );
}
