# Multimodal UAV Control via Voice and SSVEP

**UW Undergraduate Thesis Project** | Jan 2026 – Present

A custom UAV testbed for hands-free drone control, integrating voice recognition and SSVEP-based command verification through an ESP32 routing layer and Betaflight flight controller. Validated across three control modes with **98.8% command accuracy** and a **mean latency of 2.08 seconds** over 270 trials.

---

## Team

Four-person interdisciplinary team from the University of Washington:

| Role | Department |
|---|---|
| UAV Hardware, Integration, Pipeline | Aeronautics & Astronautics |
| EEG / SSVEP Signal Processing | Electrical & Computer Engineering |
| Speech Recognition / Software | Computer Science |
| Physiological Signal Analysis | Biochemistry |

Presented at the **UW Undergraduate Symposium, Spring 2026**.

---

## Problem

Voice recognition offers fast, intuitive drone control — but a single noisy misclassification can cause unintended flight behavior. Background noise, pronunciation variation, and short-command ambiguity all degrade reliability in real UAV environments.

This project addresses that risk by pairing voice recognition with **SSVEP-based command verification** as a second confirmation layer. A drone command executes only when both input channels agree. If they disagree, the command is rejected.

---

## System Overview

### Command Set

Nine commands mapped across both input modalities:

`TAKEOFF` · `LAND` · `STOP` · `FORWARD` · `BACKWARD` · `LEFT` · `RIGHT` · `UP` · `DOWN`

### Control Modes

Three modes evaluated:

- **Voice Only** — Vosk-based speech recognition on a host machine
- **SSVEP Only** — CCA classification against target stimulus frequencies (9.25 Hz – 14.75 Hz)
- **Multimodal** — Command executes only when voice and SSVEP predictions match

### Voice Recognition

Speech commands are classified using a **Vosk** offline speech recognition model. The model was selected for low-latency local inference without network dependency.

> **Literature context:** Direct audio-to-command classification achieves accuracy up to 0.99 and is the most efficient pipeline for real-time drone control, though it offers less flexibility for adding new commands. STT + LLM pipelines offer higher flexibility but introduce sequential latency. Siamese neural network approaches provide the fastest inference with the best generalization to new commands without full retraining.

### SSVEP Classification

EEG signals are classified using **Canonical Correlation Analysis (CCA)**, correlating the EEG response against reference signals at the seven target stimulus frequencies. The CCA confidence score is thresholded at **0.566**, determined via Youden's J Index, to reject low-confidence classifications.

> **Literature context:** LSTM-based SSVEP classifiers achieve 92.9% accuracy at 0.5-second processing windows using single dry-electrode setups, significantly reducing system delay. Multi-modal BCI systems combining SSVEP with Motor Imagery and eye-blink switching have achieved 86.5% outdoor 3D navigation success rates with reduced mental fatigue compared to single-modality approaches.

### Hardware Pipeline

```
Host Machine (Voice + SSVEP Classification)
        |
      ESP32 (Command Router)
        |
DolphinRC F405 V3 (Betaflight Flight Controller)
        |
    ESC Stack → Motors
```

- **Microcontroller:** ESP32 (command routing and UART interface)
- **Flight Controller:** DolphinRC F405 V3 running Betaflight
- **Onboard Compute:** Raspberry Pi
- **Frame:** Custom quad airframe

---

## Results

| Metric | Voice Only | SSVEP Only | Multimodal |
|---|---|---|---|
| Accuracy | 97.8% | 95.4% | **98.8%** |
| Mean Latency | 2.16 s | 2.62 s | **2.08 s** |
| Misclassifications | 2 | 4 | **0** |
| Rejected Commands | — | — | 7 |

Total trials: **270** (90 per mode).

Seven multimodal trials were rejected due to channel disagreement or missing input — confirming the safety logic actively discards uncertain commands rather than executing them. Zero misclassifications occurred in multimodal mode.

---

## My Contributions

**Hardware**
- Drone assembly, soldering, and wiring
- Part selection and propulsion system sizing
- DolphinRC F405 V3 configuration in Betaflight: receiver setup, motor mapping, mode configuration, safety behavior
- ESP32 command routing and embedded interface setup
- Baseline RC flight demonstration to verify airframe and flight controller readiness

**Software & Integration**
- Command pipeline integration connecting the classification layer to the flight controller
- Latency measurement pipeline design and data collection across all three control modes
- Safety and testing procedure development

---

## Limitations

**EEG Signal Quality**
Real-time EEG acquisition did not produce clean SSVEP signals during hardware testing. Recorded spectral peaks concentrated in the 5–8 Hz range rather than at the target stimulus frequencies, indicating significant noise and weak stimulus-locked responses. SSVEP classification performance was therefore evaluated using the open-source benchmark dataset from [Nakanishi et al.](https://github.com/mnakanishi/12JFPM_SSVEP) rather than live subject data.

During integrated hardware tests, SSVEP inputs were simulated via keyboard entries mapped to the seven target frequencies.

**Manual RC Override**
Manual RC override was explored as a safety fallback but was not preserved in the final test configuration due to UART integration errors. The drone was not flown under live multimodal control. The baseline flight demonstration used standard RC control only.

---

## Next Steps (Thesis)

Following the symposium, this project is transitioning into an **undergraduate thesis** extending bench-level validation to flight-condition evaluation.

**Immediate priorities:**
1. Resolve the UART integration issue to restore a reliable manual RC override path
2. Improve real-time EEG signal quality via better electrode placement, dry electrode selection, and noise shielding

**Flight-condition validation:**
- Mount the UAV on a **6 DOF gimbal** to enable controlled motion testing in a constrained environment
- Measure latency and command accuracy under actual flight dynamics without free-flight safety constraints
- Evaluate with live SSVEP classification replacing keyboard-simulated inputs

---

## Stack

| Layer | Technology |
|---|---|
| Voice Recognition | Python, Vosk |
| SSVEP Classification | Python, CCA (NumPy/SciPy) |
| Command Routing | ESP32 (C/Arduino) |
| Flight Controller | DolphinRC F405 V3, Betaflight |
| Onboard Compute | Raspberry Pi |
| EEG Benchmark Dataset | Nakanishi et al. 12-class JFPM SSVEP |

---

## References

1. Direct classification pipeline for drone voice control — accuracy 0.99, real-time capable
2. Siamese neural network voice command generalization — fastest inference, no full retrain needed for new commands
3. DJI + Nuance natural language drone control using regex pattern matching for intuitive varied commands
4. Google STT + Levenshtein distance matching — performance degrades for short commands in noisy environments; noise cancellation critical for real-world operation
5. LSTM-based low-latency SSVEP classification — 92.9% accuracy at 0.5 s window, single dry electrode
6. Multi-modal BCI (SSVEP + Motor Imagery + Eye Blink) — 86.5% outdoor 3D quadcopter navigation success, reduced operator fatigue vs. single-modality

---

## Portfolio

Project page: [khoy2k.github.io](https://khoy2k.github.io) — Multimodal UAV Control via Voice and SSVEP
