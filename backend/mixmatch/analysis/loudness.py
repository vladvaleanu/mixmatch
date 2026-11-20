"""Tăria integrată după EBU R128 (LUFS), pentru auto-gain."""

import essentia.standard as es

from mixmatch.analysis.audio import Audio


def integrated_lufs(audio: Audio) -> float | None:
    _, _, integrated, _ = es.LoudnessEBUR128(sampleRate=audio.sample_rate)(audio.stereo)
    value = float(integrated)
    return round(value, 1) if value > -70 else None  # sub −70 LUFS e practic liniște
