// Mute/unmute control for spoken live cues, shown in live pages and the dashboard topbar.
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
