"""
sounds.py
All audio generated in pure Python/numpy — no audio files required.

  SoundManager.build()  — call once after pygame.mixer.init()
  .start_engine()       — loop engine hum
  .update_engine_pitch(speed, max_speed) — shift engine tier each frame
  .stop_engine()
  .play_crash()
  .play_glass()         — fires glass 180 ms later via USEREVENT+1
  .trigger_glass_now()  — called when the timer fires
  .start_bgm()          — loop background music
  .stop_bgm()
  .toggle_mute()        — returns new muted state
"""

import numpy as np
import pygame

SR = 44100 

def _pcm(wave: np.ndarray) -> pygame.mixer.Sound:
    """Normalise mono wave → stereo int16 pygame Sound."""
    peak = np.max(np.abs(wave))
    if peak > 0:
        wave = wave / peak
    stereo = np.column_stack([wave, wave])
    return pygame.sndarray.make_sound(
        np.ascontiguousarray((stereo * 32767).astype(np.int16)))

def _t(dur):  return np.linspace(0, dur, int(SR * dur), endpoint=False)
def _adsr(a, n):
    env = np.ones(n)
    ai = int(a * n);  env[:ai] = np.linspace(0, 1, ai)
    ri = int(0.15*n); env[-ri:] = np.linspace(1, 0, ri)
    return env

def _engine(rpm: float) -> pygame.mixer.Sound:
    """Loopable engine rumble at given rpm multiplier."""
    dur = 0.5
    f   = 80 * rpm
    t   = _t(dur)
    w   = (0.50 * np.sin(2*np.pi*f*t)
         + 0.25 * np.sin(2*np.pi*f*2*t)
         + 0.15 * np.sin(2*np.pi*f*3*t)
         + 0.08 * np.sin(2*np.pi*f*4*t))
    w  *= (0.75 + 0.25 * np.sin(2*np.pi*(f/2)*t))
    w  += 0.05 * np.random.uniform(-1, 1, len(t))
    fade = int(0.005*SR)
    w[-fade:] *= np.linspace(1, 0, fade)
    w[:fade]  *= np.linspace(0, 1, fade)
    snd = _pcm(w * 0.5)
    snd.set_volume(0.40)
    return snd

def _crash() -> pygame.mixer.Sound:
    dur = 1.4;  t = _t(dur)
    w  = (0.6 * np.sin(2*np.pi*55*t) * np.exp(-8*t)
        + 0.4 * np.sin(2*np.pi*82*t) * np.exp(-10*t)
        + 0.3 * np.sin(2*np.pi*47*t) * np.exp(-6*t))
    w += np.random.uniform(-1, 1, len(t)) * np.exp(-30*t) * 0.9
    snd = _pcm(w)
    snd.set_volume(0.95)
    return snd
def _glass() -> pygame.mixer.Sound:
    samples = int(SR * 1.6)
    w = np.zeros(samples)
    rng = np.random.default_rng(7)
    for _ in range(90):
        freq  = rng.uniform(1800, 6500)
        start = int(rng.uniform(0, 0.4) * samples)
        n     = int(rng.uniform(0.02, 0.18) * SR)
        amp   = rng.uniform(0.15, 0.6)
        decay = rng.uniform(12, 38)
        end   = min(start+n, samples)
        lt    = np.arange(end-start) / SR
        w[start:end] += amp * np.sin(2*np.pi*freq*lt) * np.exp(-decay*lt)
    w += 0.1 * np.random.uniform(-1, 1, samples) * np.exp(
        -4 * np.linspace(0, 1.6, samples))
    snd = _pcm(w * 0.8)
    snd.set_volume(0.88)
    return snd

def _bgm() -> pygame.mixer.Sound:
    """
    4-bar loopable synth-driving BGM:
      • Bass kick every beat
      • Synth lead melody
      • Hi-hat pulse
      • Pad chord layer
    """
    bpm      = 128
    beats    = 16           
    dur      = beats * 60 / bpm
    n        = int(SR * dur)
    w        = np.zeros(n)
    beat_s   = 60 / bpm     
    beat_n   = int(SR * beat_s)

    def kick(pos):
        k = int(0.18 * SR)
        t = np.arange(k) / SR
        f = 180 * np.exp(-35 * t)   
        env = np.exp(-18 * t)
        chunk = np.sin(2*np.pi*f*t) * env * 0.9
        end = min(pos+k, n)
        w[pos:end] += chunk[:end-pos]

    for b in range(beats):
        kick(b * beat_n)

    def hihat(pos, vol=0.18):
        k = int(0.04 * SR)
        noise = np.random.default_rng(pos).uniform(-1, 1, k)
        env   = np.exp(-80 * np.arange(k) / SR)
        chunk = noise * env * vol
        end   = min(pos+k, n)
        w[pos:end] += chunk[:end-pos]
    for b in range(beats * 2):
        hihat(int(b * beat_n / 2))
    def bass(pos, freq, dur_beats=0.45):
        k = int(dur_beats * beat_s * SR)
        t = np.arange(k) / SR
        b_w = (0.6 * np.sin(2*np.pi*freq*t)
             + 0.3 * np.sin(2*np.pi*freq*2*t)
             + 0.1 * np.sin(2*np.pi*freq*3*t))
        env = np.exp(-3 * t / (dur_beats * beat_s)) * 0.55
        b_w *= env
        end = min(pos+k, n)
        w[pos:end] += b_w[:end-pos]
    bass_notes = [110, 110, 82.4, 98.0,
                  110, 110, 82.4, 98.0,
                  110, 130.8, 110, 82.4,
                  110, 98.0, 110, 130.8]
    for i, freq in enumerate(bass_notes):
        bass(i * beat_n, freq)
    def lead(pos, freq, dur_beats=0.9, vol=0.22):
        k = int(dur_beats * beat_s * SR)
        t = np.arange(k) / SR
        lw = (0.5 * np.sin(2*np.pi*freq*t)
            + 0.3 * np.sin(2*np.pi*freq*2*t)
            + 0.2 * np.sin(2*np.pi*freq*3*t))
        env = _adsr(0.05, k)
        lw  = lw * env * vol
        end = min(pos+k, n)
        w[pos:end] += lw[:end-pos]
    E4, Fs4, A4, B4, Cs5 = 329.6, 370.0, 440.0, 493.9, 554.4
    melody = [
        (0,  A4,  1.8), (2, Cs5, 0.9), (3, B4,  0.9),
        (4,  A4,  0.9), (5, Fs4, 0.9), (6, E4,  1.8),
        (8,  A4,  1.8), (10, B4, 0.9), (11, Cs5,0.9),
        (12, B4,  0.9), (13, A4, 0.9), (14, Fs4, 1.8),
    ]
    for beat_pos, freq, dur in melody:
        lead(int(beat_pos * beat_n), freq, dur)
    def pad(pos, freqs, dur_beats=4.0, vol=0.12):
        k   = int(dur_beats * beat_s * SR)
        t   = np.arange(k) / SR
        pw  = sum(np.sin(2*np.pi*f*t) for f in freqs)
        env = _adsr(0.1, k)
        pw  = pw * env * vol / len(freqs)
        end = min(pos+k, n)
        w[pos:end] += pw[:end-pos]

    Am = [220, 261.6, 329.6]
    Em = [164.8, 196.0, 246.9]
    pad(0,          Am)
    pad(4*beat_n,   Em)
    pad(8*beat_n,   Am)
    pad(12*beat_n,  Em)
    xf = int(0.02 * SR)
    w[-xf:] *= np.linspace(1, 0, xf)
    w[:xf]  *= np.linspace(0, 1, xf)

    snd = _pcm(w)
    snd.set_volume(0.38)
    return snd
class SoundManager:
    ENGINE_RPMS = [1.0, 1.35, 1.7, 2.1, 2.6]

    def __init__(self):
        self._engines : list = []
        self._crash_snd      = None
        self._glass_snd      = None
        self._bgm_snd        = None
        self._eng_ch         = None
        self._bgm_ch         = None
        self._cur_tier       = -1
        self._muted          = False

    def build(self):
        print("[Sound] Building engine tiers…")
        self._engines = [_engine(r) for r in self.ENGINE_RPMS]
        print("[Sound] Crash…")
        self._crash_snd = _crash()
        print("[Sound] Glass…")
        self._glass_snd = _glass()
        print("[Sound] BGM…")
        self._bgm_snd   = _bgm()
        self._eng_ch    = pygame.mixer.Channel(0)
        self._bgm_ch    = pygame.mixer.Channel(1)
        print("[Sound] Ready.")
    def start_engine(self):
        if self._muted or not self._engines: return
        self._cur_tier = 0
        self._eng_ch.play(self._engines[0], loops=-1)

    def update_engine_pitch(self, speed, max_speed):
        if self._muted or not self._engines: return
        ratio = min(speed / max_speed, 1.0)
        tier  = min(int(ratio * len(self.ENGINE_RPMS)),
                    len(self.ENGINE_RPMS) - 1)
        if tier != self._cur_tier:
            self._cur_tier = tier
            self._eng_ch.play(self._engines[tier], loops=-1, fade_ms=100)

    def stop_engine(self):
        if self._eng_ch: self._eng_ch.fadeout(250)
        self._cur_tier = -1
    def play_crash(self):
        if not self._muted and self._crash_snd:
            pygame.mixer.Channel(2).play(self._crash_snd)

    def play_glass(self):
        """Schedule glass sound 200 ms after crash."""
        if not self._muted:
            pygame.time.set_timer(pygame.USEREVENT + 1, 200, loops=1)

    def trigger_glass_now(self):
        if not self._muted and self._glass_snd:
            pygame.mixer.Channel(3).play(self._glass_snd)
    def start_bgm(self):
        if self._muted or not self._bgm_snd: return
        self._bgm_ch.play(self._bgm_snd, loops=-1)

    def stop_bgm(self):
        if self._bgm_ch: self._bgm_ch.fadeout(500)
    def toggle_mute(self) -> bool:
        self._muted = not self._muted
        if self._muted:
            pygame.mixer.pause()
        else:
            pygame.mixer.unpause()
        return self._muted
    @property
    def muted(self): return self._muted
