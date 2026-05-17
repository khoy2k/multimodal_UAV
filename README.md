# Multimodal UAV Control via Voice and SSVEP

**Undergraduate Research Thesis** | University of Washington | 2026

A UAV testbed for hands-free drone control combining voice recognition and SSVEP-based command verification. A drone command executes only when both input channels agree — if they disagree, the command is rejected. The thesis goal is a **gimbal-constrained flight test** of the full closed-loop pipeline under real motor dynamics.

---

## Background

This thesis builds on a proof-of-concept developed for the **UW Undergraduate Symposium (Spring 2026)**. The symposium work validated the multimodal pipeline at the bench level across three control modes — voice only, SSVEP only, and combined — over 270 trials:

| Metric | Voice Only | SSVEP Only | Multimodal |
|---|---|---|---|
| Accuracy | 97.8% | 95.4% | **98.8%** |
| Mean Latency | 2.16 s | 2.62 s | **2.08 s** |
| Misclassifications | 2 | 4 | **0** |
| Rejected Commands | — | — | 7 |

Two limitations from that work drive this thesis:

- SSVEP classification used keyboard-triggered replay of the Nakanishi et al. benchmark dataset rather than live EEG. The same approach is used here — the thesis contribution is the closed-loop flight test, not live BCI.
- Manual RC override was lost due to a UART integration error. The drone was never flown under multimodal control. **Restoring RC override is the prerequisite for the gimbal test.**

---

## Thesis Goal: Gimbal Flight Test

The drone is mounted on a **6 DOF gimbal** — constrained so it cannot fly away, but free to respond physically to commands. Propellers are on. Motors are live. This is the first time the multimodal pipeline will drive actual flight dynamics.

**What the gimbal test measures that bench testing cannot:**

- Latency under real motor load and vibration
- Voice recognition accuracy with propeller noise in the environment
- CCA classification stability when motor EMI is present on the LSL stream
- Betaflight RC channel response under commanded flight maneuvers

**SSVEP source:** Nakanishi et al. 12-class benchmark dataset, streamed in real-time via Lab Streaming Layer at 256 Hz. The pipeline is architecturally identical to live EEG — swapping the mock server for BrainFlow hardware acquisition is future work.

---

## Current Status

| Task | Status |
|---|---|
| Restore UART RC override (safety prerequisite) | In progress |
| Bench verify arm/disarm sequence via ground_station.py | Pending |
| Tune hover throttle value for airframe | Pending |
| Test voice recognition under propeller noise | Pending |
| Gimbal flight test | Pending |

---

## Test Flow

Three terminals and an RC transmitter as a safety cutoff:

```
Terminal 1:  python ssvep/eeg_server.py      # mock EEG headset via LSL
Terminal 2:  python ground_station.py        # voice + EEG + fusion + ESP32
Terminal 3:  python trial_sequencer.py       # automated trial runner
RC transmitter in hand                       # safety cutoff — kills motors instantly
```

**Per trial (example: target = FORWARD)**

1. `trial_sequencer` sends two UDP messages:
   - injects the 13.75 Hz Nakanishi clip into `eeg_server` (port 4213)
   - tells `ground_station` to start the trial in BOTH mode (port 4214)
2. `eeg_server` streams the clip through LSL at 256 Hz
3. `ground_station` EEG thread classifies the stream via CCA → FORWARD
4. Operator speaks **"forward"** into the microphone
5. `ground_station` voice thread recognizes the command → FORWARD
6. Fusion: both channels agree → command sent to ESP32 → Betaflight → motors
7. Gimbal absorbs the physical response; `trial_sequencer` logs latency and outcome

**If the two channels disagree, the command is rejected and nothing moves.**

---

## System Architecture

```
ground_station.py (Voice + EEG fusion)
         |
    ESP32 (UDP → MSP bridge)
         |
DolphinRC F405 V3 (Betaflight)
         |
    ESC Stack → Motors → Gimbal
```

**Voice:** Vosk offline speech recognition — no network dependency, runs on the host machine.

**SSVEP:** CCA against nine target stimulus frequencies (9.25 Hz – 14.75 Hz), one per command. Confidence threshold 0.566 (Youden's J Index).

**Fusion rule:** Both channels must predict the same command. One channel absent or disagreeing → rejected.

### Command Set

`TAKEOFF` · `LAND` · `STOP` · `FORWARD` · `BACKWARD` · `LEFT` · `RIGHT` · `UP` · `DOWN`

### Hardware

| Component | Part |
|---|---|
| Frame | Custom quad airframe |
| Flight Controller | DolphinRC F405 V3 (Betaflight) |
| Command Router | ESP32 |
| Onboard Compute | Raspberry Pi |
| Test Fixture | 6 DOF gimbal |

---

## Repository Structure

```
ground_station.py          core system — voice + EEG threads, fusion, ESP32 output
trial_sequencer.py         automated trial runner, no human in the data path
betaflight_msp.py          MSP v1 serial interface to Betaflight
experiment_logger.py       CSV trial logger
ssvep/
  eeg_server.py            Nakanishi mock EEG server over LSL
  nakanishi_data/          benchmark dataset (subject 8, 9 frequencies)
esp32/
  ESP32_Firmware.ino       UDP-to-MSP bridge firmware
tools/
  ssvep.html               SSVEP stimulus display
  compare_results.py       result analysis
  test_sequences.json      predefined command sequences
```

---

## Stack

| Layer | Technology |
|---|---|
| Voice Recognition | Python, Vosk |
| SSVEP Classification | Python, CCA (NumPy / SciPy) |
| Command Routing | ESP32 (C / Arduino) |
| Flight Controller | DolphinRC F405 V3, Betaflight |
| Onboard Compute | Raspberry Pi |
| SSVEP Data Source | Nakanishi et al. 12-class JFPM SSVEP dataset |

---

## References

1. Direct audio-to-command classification for drone control — accuracy 0.99, real-time capable
2. Siamese neural network voice command generalization — fastest inference, no full retrain for new commands
3. DJI + Nuance natural language drone control using regex for intuitive varied commands
4. Google STT + Levenshtein distance — short commands degrade significantly in noise; noise cancellation critical
5. LSTM-based low-latency SSVEP — 92.9% accuracy at 0.5 s window, single dry electrode
6. Multi-modal BCI (SSVEP + Motor Imagery + Eye Blink) — 86.5% outdoor 3D navigation success, reduced operator fatigue

---

## Contributors

The codebase (excluding `trial_sequencer.py`) was written by the original UW Undergraduate Symposium team:

- **[Jae-Lee-Tho](https://github.com/Jae-Lee-Tho)** — primary codebase author
- **[Samshin](https://github.com/Samshin)** — primary codebase author

Source repository: [Jae-Lee-Tho/MultiDrone](https://github.com/Jae-Lee-Tho/MultiDrone)

---

Portfolio: [khoy2k.github.io](https://khoy2k.github.io)
