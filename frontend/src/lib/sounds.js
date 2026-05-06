let audioContext;

function getContext() {
  if (!audioContext) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
  }
  return audioContext;
}

function tone({ frequency, duration, type = "sine", gain = 0.05 }) {
  const ctx = getContext();
  const oscillator = ctx.createOscillator();
  const volume = ctx.createGain();
  oscillator.type = type;
  oscillator.frequency.value = frequency;
  volume.gain.setValueAtTime(gain, ctx.currentTime);
  volume.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
  oscillator.connect(volume);
  volume.connect(ctx.destination);
  oscillator.start();
  oscillator.stop(ctx.currentTime + duration);
}

export const fx = {
  startup() {
    [220, 330, 520, 740].forEach((frequency, index) => {
      window.setTimeout(() => tone({ frequency, duration: 0.18, type: "triangle", gain: 0.04 }), index * 110);
    });
  },
  click() {
    tone({ frequency: 920, duration: 0.08, type: "square", gain: 0.025 });
  },
  listening() {
    tone({ frequency: 420, duration: 0.18, type: "sawtooth", gain: 0.025 });
  },
  response() {
    tone({ frequency: 660, duration: 0.12, type: "triangle", gain: 0.035 });
    window.setTimeout(() => tone({ frequency: 990, duration: 0.16, type: "triangle", gain: 0.03 }), 90);
  },
};
