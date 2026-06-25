"""
SoundPlayer.py — 实时音频引擎

使用 sounddevice + numpy 实现多音独立追踪的实时音频流。
play_chord() 始终先静音再播放 — 旧音符全部掐断，新音符立刻开始。
音频流惰性创建后常驻，不随停止而关闭。
"""
from __future__ import annotations

import threading
from dataclasses import dataclass

import numpy as np
import sounddevice as sd

# ── 音频参数 ──────────────────────────────────────────────────────────────────
SAMPLE_RATE = 44100
AMPLITUDE  = 0.25
DURATION   = 1.5
FADE_OUT   = 0.3
ATTACK     = 0.01
BLOCK_SIZE = 256


@dataclass
class _NoteState:
    freq: float
    phase: float
    volume: float
    age_samples: int
    ttl_samples: int


# ── 全局状态 ─────────────────────────────────────────────────────────────────
_lock = threading.Lock()
_active_notes: dict[int, _NoteState] = {}
_stream: sd.OutputStream | None = None


def _ensure_stream():
    global _stream
    if _stream is None or _stream.closed:
        _stream = sd.OutputStream(
            samplerate=SAMPLE_RATE, channels=1, blocksize=BLOCK_SIZE,
            callback=_audio_callback, dtype='float32',
        )
        _stream.start()


def _audio_callback(outdata: np.ndarray, frames: int, _ti, _st):
    buf = np.zeros(frames, dtype=np.float64)
    t = np.arange(frames, dtype=np.float64)

    with _lock:
        dead: list[int] = []
        for pitch, ns in list(_active_notes.items()):
            phases = ns.phase + 2.0 * np.pi * ns.freq * t / SAMPLE_RATE
            wave = np.sin(phases)
            ns.phase = phases[-1] % (2.0 * np.pi)
            ns.age_samples += frames
            wave *= _envelope(ns.age_samples, ns.ttl_samples) * ns.volume
            buf += wave
            if ns.age_samples >= ns.ttl_samples + int(FADE_OUT * SAMPLE_RATE):
                dead.append(pitch)
        for p in dead:
            del _active_notes[p]

    np.clip(buf, -1.0, 1.0, out=buf)
    outdata[:, 0] = buf.astype(np.float32)


def _envelope(age: int, ttl: int) -> float:
    atk = int(ATTACK * SAMPLE_RATE)
    rel = int(FADE_OUT * SAMPLE_RATE)
    if age < atk:
        return age / atk
    if age < ttl:
        return 1.0
    pos = (age - ttl) / rel
    return max(0.0, 1.0 - pos)


def _note_number_to_freq(note_number: int) -> float:
    return 440.0 * (2.0 ** ((note_number - 69) / 12.0))


def _pitch_to_note_number(pitch: int) -> int:
    return pitch + 12


# ── 公开 API ─────────────────────────────────────────────────────────────────

def play_chord(pitches: list[int], duration: float = DURATION):
    """
    播放和弦。
    始终先静音再播放新和弦（旧有音符全部掐断）。
    """
    if not pitches:
        return

    _ensure_stream()
    ttl = int(duration * SAMPLE_RATE)

    with _lock:
        _active_notes.clear()
        for pitch in pitches:
            nn = _pitch_to_note_number(pitch)
            _active_notes[pitch] = _NoteState(
                freq=_note_number_to_freq(nn), phase=0.0,
                volume=AMPLITUDE, age_samples=0, ttl_samples=ttl,
            )


def play_note(pitch: int, duration: float = DURATION):
    """播放单音"""
    play_chord([pitch], duration)


def play_arpeggio(pitches: list[int], note_duration: float = 0.3):
    """播放琶音"""
    for pitch in pitches:
        play_note(pitch, note_duration)


def stop_all():
    """立即停止所有正在播放的音符（不关闭音频流）。"""
    with _lock:
        _active_notes.clear()
