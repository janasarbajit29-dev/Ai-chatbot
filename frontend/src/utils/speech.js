let voicesLoaded = false;
let voices = [];
let speakQueue = [];

function loadVoices() {
  if (typeof window === "undefined" || !window.speechSynthesis) return;
  voices = window.speechSynthesis.getVoices();
  if (voices.length > 0) {
    voicesLoaded = true;
    console.log(`[AURA Speech] voices: ${voices.length}`);
    while (speakQueue.length > 0) {
      const { text, onEnd } = speakQueue.shift();
      speak(text, onEnd);
    }
  }
}

if (typeof window !== "undefined" && window.speechSynthesis) {
  loadVoices();
  if (window.speechSynthesis.onvoiceschanged !== undefined) {
    window.speechSynthesis.onvoiceschanged = loadVoices;
  }
}

export function getFemaleVoice() {
  if (!voices || voices.length === 0) return null;
  
  const preferredNames = ["samantha", "zira", "female", "victoria", "karen"];
  
  let voice = voices.find(v => 
    v.lang.startsWith("en") && 
    preferredNames.some(name => v.name.toLowerCase().includes(name))
  );
  
  if (voice) return voice;

  voice = voices.find(v => v.lang.startsWith("en"));
  
  if (voice) return voice;

  return voices[0] || null;
}

export function speak(text, onEnd = null) {
  console.log("[AURA Speech] speak() called");
  if (typeof window === "undefined" || !window.speechSynthesis) {
    console.log("[AURA Speech] supported: false");
    if (onEnd) onEnd();
    return;
  }
  
  console.log("[AURA Speech] supported: true");

  if (!voicesLoaded) {
    console.log("[AURA Speech] voices not loaded yet, queuing...");
    loadVoices();
    if (!voicesLoaded) {
      speakQueue.push({ text, onEnd });
      return;
    }
  }

  console.log(`[AURA Speech] speaking: ${window.speechSynthesis.speaking}, pending: ${window.speechSynthesis.pending}`);
  
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  console.log(`[AURA Speech] text: ${text}`);
  
  const voice = getFemaleVoice();
  if (voice) {
    console.log(`[AURA Speech] selected voice: ${voice.name} (${voice.lang})`);
    utterance.voice = voice;
  } else {
    console.log("[AURA Speech] selected voice: default (none found)");
  }
  
  utterance.lang = "en-US";
  utterance.rate = 0.90;
  utterance.pitch = 1.12;
  utterance.volume = 1.0;

  utterance.onstart = () => console.log("[AURA Speech] onstart");
  utterance.onend = () => {
    console.log("[AURA Speech] onend");
    if (onEnd) onEnd();
  };
  utterance.onerror = (e) => {
    console.log("[AURA Speech] onerror: ", e.error || e);
    if (onEnd) onEnd();
  };

  window.speechSynthesis.speak(utterance);
}
