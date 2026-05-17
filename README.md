# Multimodal UAV Control via Voice and SSVEP

**Undergraduate Research Thesis** | University of Washington | 2026

A UAV testbed for hands-free drone control combining voice recognition and SSVEP-based command verification. A drone command executes only when both input channels agree — if they disagree, the command is rejected.

---

## Background

This thesis builds on a proof-of-concept developed for the **UW Undergraduate Symposium (Spring 2026)**. The symposium work validated the multimodal pipeline at the bench level across three control modes — voice only, SSVEP only, and combined — over 270 trials:

| Metric | Voice Only | SSVEP Only | Multimodal |
|---|---|---|---|
| Accuracy | 97.8% | 95.4% | **98.8%** |
| Mean Latency | 2.16 s | 2.62 s | **2.08 s** |
| Misclassifications | 2 | 4 | **0** |
| Rejected Commands | — | — | 7 |

Key limitations from that work that this thesis addresses:
- Real-time EEG acquisition produced noisy signals peaking at 5–8 Hz rather than the target stimulus frequencies. SSVEP classification was validated against the Nakanishi et al. benchmark dataset, not live subject data. Hardware tests used keyboard-simulated SSVEP inputs.
- Manual RC override was not preserved in the final test configuration due to a UART integration error. The drone was not flown under live multimodal control.

---

## Thesis Goals

Extend the bench-level validation into a full flight-condition evaluation of the multimodal pipeline:

1. **Restore manual RC override** — resolve the UART integration issue for a reliable safety fallback
2. **Fix real-time SSVEP** — improve EEG signal quality through better electrode placement and noise shielding
3. **Flight-condition latency and accuracy measurement** — mount the UAV on a 6 DOF gimbal for controlled motion testing under actual flight dynamics, with live SSVEP classification replacing keyboard-simulated inputs

---

## System

### Command Set

`TAKEOFF` · `LAND` · `STOP` · `FORWARD` · `BACKWARD` · `LEFT` · `RIGHT` · `UP` · `DOWN`

### Architecture

```
Host Machine (Voice + SSVEP Classification)
        |
      ESP32 (Command Router)
        |
DolphinRC F405 V3 (Betaflight Flight Controller)
        |
    ESC Stack → Motors
```

**Voice:** Vosk offline speech recognition — local inference, no network dependency.

**SSVEP:** Canonical Correlation Analysis (CCA) against target stimulus frequencies (9.25 Hz – 14.75 Hz). Confidence threshold at 0.566 (Youden's J Index) to reject low-confidence classifications.

**Multimodal logic:** Voice and SSVEP predictions are compared before any command is forwarded to the flight controller. Disagreement → command rejected.

### Hardware

| Component | Part |
|---|---|
| Frame | Custom quad airframe |
| Flight Controller | DolphinRC F405 V3 (Betaflight) |
| Command Router | ESP32 |
| Onboard Compute | Raspberry Pi |

---

## Stack

| Layer | Technology |
|---|---|
| Voice Recognition | Python, Vosk |
| SSVEP Classification | Python, CCA (NumPy / SciPy) |
| Command Routing | ESP32 (C / Arduino) |
| Flight Controller | DolphinRC F405 V3, Betaflight |
| Onboard Compute | Raspberry Pi |
| SSVEP Benchmark | Nakanishi et al. 12-class JFPM SSVEP dataset |

---

## References

1. Direct audio-to-command classification for drone control — accuracy 0.99, real-time capable
2. Siamese neural network voice command generalization — fastest inference, no full retrain needed for new commands
3. DJI + Nuance natural language drone control using regex pattern matching for intuitive varied commands
4. Google STT + Levenshtein distance matching — short commands degrade significantly in noisy environments; noise cancellation is critical
5. LSTM-based low-latency SSVEP classification — 92.9% accuracy at 0.5 s window, single dry electrode
6. Multi-modal BCI (SSVEP + Motor Imagery + Eye Blink) — 86.5% outdoor 3D quadcopter navigation success, reduced operator fatigue vs. single-modality

---

Portfolio: [khoy2k.github.io](https://khoy2k.github.io)
