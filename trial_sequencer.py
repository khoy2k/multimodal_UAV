"""
trial_sequencer.py

Automated trial runner for the multimodal UAV control experiment.
Replaces the human keyboard operator from the symposium setup.

HOW IT WORKS
------------
Three processes must already be running before you start this:

  Terminal 1:  python ssvep/eeg_server.py
  Terminal 2:  python ground_station.py
  Terminal 3:  python trial_sequencer.py   ← this file

For each trial the sequencer:
  1. Tells ground_station.py which mode and target are active  (port 4214)
  2. Tells eeg_server.py   to inject the matching Nakanishi clip (port 4213)
  3. Listens to ground_station.py telemetry for the final command (port 4211)
  4. Scores the trial (correct / wrong / rejected) and logs it to CSV

PORT MAP (must match ground_station.py)
  4211  ← telemetry OUT from ground_station  (we listen here)
  4213  → EEG trigger    to   eeg_server      (we send here)
  4214  → control msg    to   ground_station   (we send here)
"""

import csv
import json
import os
import socket
import time
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

GS_CONTROL_IP   = "127.0.0.1"
GS_CONTROL_PORT = 4214   # ground_station control socket

EEG_TRIGGER_IP   = "127.0.0.1"
EEG_TRIGGER_PORT = 4213  # eeg_server UDP listener

TELEMETRY_LISTEN_PORT = 4211  # ground_station sends telemetry here

TRIAL_TIMEOUT_SEC = 8.0   # give up waiting for a command after this many seconds
INTER_TRIAL_SEC   = 2.5   # pause between trials so drone settles

# eeg_server.py keyboard-to-frequency mapping (from eeg_server.py COMMAND_MAPPING)
COMMAND_TO_EEG_KEY = {
    "TAKEOFF":  "t",   # 9.25 Hz
    "STOP":     "q",   # 10.25 Hz
    "LAND":     "l",   # 11.25 Hz
    "DOWN":     "j",   # 12.25 Hz
    "RIGHT":    "d",   # 12.75 Hz
    "UP":       "u",   # 13.25 Hz
    "FORWARD":  "w",   # 13.75 Hz
    "BACKWARD": "s",   # 14.25 Hz
    "LEFT":     "a",   # 14.75 Hz
}

VALID_MODES = ["VOICE_ONLY", "EEG_ONLY", "BOTH"]

BUILTIN_SEQUENCES = [
    {
        "name": "Level 1 - Baseline",
        "sequence": ["FORWARD", "BACKWARD"],
    },
    {
        "name": "Level 2 - Lateral",
        "sequence": ["LEFT", "LEFT", "RIGHT", "RIGHT"],
    },
    {
        "name": "Level 3 - Box",
        "sequence": ["FORWARD", "LEFT", "BACKWARD", "RIGHT"],
    },
    {
        "name": "Level 4 - Full Flight",
        "sequence": ["TAKEOFF", "FORWARD", "RIGHT", "BACKWARD", "LEFT", "LAND"],
    },
]

# =============================================================================
# SETUP SOCKETS
# =============================================================================

def make_send_socket() -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return s

def make_listen_socket(port: int, timeout: float) -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", port))
    s.settimeout(timeout)
    return s

# =============================================================================
# MENU HELPERS
# =============================================================================

def pick_mode() -> str:
    print("\nSelect experiment mode:")
    for i, m in enumerate(VALID_MODES, 1):
        print(f"  {i}. {m}")
    while True:
        raw = input("Choice: ").strip()
        if raw in VALID_MODES:
            return raw
        if raw in {"1", "2", "3"}:
            return VALID_MODES[int(raw) - 1]
        print("  Enter 1, 2, 3, or the mode name.")


def pick_sequence() -> dict:
    sequences = BUILTIN_SEQUENCES
    json_path = os.path.join("tools", "test_sequences.json")
    if os.path.exists(json_path):
        with open(json_path) as f:
            sequences = json.load(f).get("tests", BUILTIN_SEQUENCES)

    print("\nSelect test sequence:")
    for i, seq in enumerate(sequences, 1):
        print(f"  {i}. {seq['name']}  →  {seq['sequence']}")
    while True:
        raw = input(f"Choice (1-{len(sequences)}): ").strip()
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(sequences):
                return sequences[idx]
        except ValueError:
            pass
        print(f"  Enter a number between 1 and {len(sequences)}.")

# =============================================================================
# CORE TRIAL LOGIC
# =============================================================================

def send_control(sock: socket.socket, mode: str, target: str) -> None:
    """Tell ground_station.py to start a new trial."""
    msg = json.dumps({"action": "start_trial", "mode": mode, "target": target})
    sock.sendto(msg.encode(), (GS_CONTROL_IP, GS_CONTROL_PORT))


def send_eeg_trigger(sock: socket.socket, command: str) -> bool:
    """Inject the matching Nakanishi clip into eeg_server.py via UDP."""
    key = COMMAND_TO_EEG_KEY.get(command.upper())
    if key is None:
        print(f"  [EEG] No frequency mapping for command '{command}' — skipping EEG inject.")
        return False
    sock.sendto(key.encode(), (EEG_TRIGGER_IP, EEG_TRIGGER_PORT))
    return True


def wait_for_command(
    listen_sock: socket.socket,
    target: str,
    mode: str,
    timeout: float,
) -> dict:
    """
    Drain the telemetry socket until ground_station fires a final_cmd,
    or until `timeout` seconds elapse.

    Returns a result dict with keys: final_cmd, correct, latency_sec, rejected.
    """
    deadline = time.perf_counter() + timeout
    t_start  = time.perf_counter()

    while time.perf_counter() < deadline:
        try:
            data, _ = listen_sock.recvfrom(4096)
            telem   = json.loads(data.decode())

            final = telem.get("final_cmd")
            if final is None:
                continue

            latency = round(time.perf_counter() - t_start, 4)
            correct = (final.upper() == target.upper())
            return {
                "final_cmd":    final,
                "correct":      correct,
                "latency_sec":  latency,
                "rejected":     False,
                "eeg_score":    telem.get("eeg_score", 0.0),
                "voice_cmd":    telem.get("voice_cmd"),
                "eeg_cmd":      telem.get("eeg_cmd"),
            }

        except socket.timeout:
            break
        except (json.JSONDecodeError, OSError):
            continue

    # Timed out — no command fired
    return {
        "final_cmd":   "NONE",
        "correct":     False,
        "latency_sec": round(time.perf_counter() - t_start, 4),
        "rejected":    True,
        "eeg_score":   0.0,
        "voice_cmd":   None,
        "eeg_cmd":     None,
    }


def run_trial(
    trial_id:    int,
    mode:        str,
    target:      str,
    send_sock:   socket.socket,
    listen_sock: socket.socket,
) -> dict:
    print(f"\n{'═' * 52}")
    print(f"  Trial #{trial_id:03d}  |  Mode: {mode}  |  Target: {target}")
    print(f"{'═' * 52}")

    # 1. Tell ground_station a new trial is starting
    send_control(send_sock, mode, target)

    # 2. Inject matching EEG clip (skipped in VOICE_ONLY mode)
    if mode != "VOICE_ONLY":
        injected = send_eeg_trigger(send_sock, target)
        if injected:
            print(f"  [EEG]   Injected Nakanishi clip for {target}")
    else:
        print(f"  [EEG]   Skipped (VOICE_ONLY mode)")

    # 3. If not EEG_ONLY, prompt operator to speak the command
    if mode != "EEG_ONLY":
        print(f"  [VOICE] Speak '{target.lower()}' now ...")

    # 4. Wait for ground_station to fire a final command
    result = wait_for_command(listen_sock, target, mode, TRIAL_TIMEOUT_SEC)

    # 5. Print outcome
    if result["rejected"]:
        print(f"  ⛔  REJECTED — no command fired within {TRIAL_TIMEOUT_SEC:.0f}s")
    elif result["correct"]:
        print(f"  ✅  CORRECT  — '{result['final_cmd']}'  ({result['latency_sec']:.3f}s)")
    else:
        print(f"  ❌  WRONG    — got '{result['final_cmd']}', expected '{target}'")

    result["trial_id"]    = trial_id
    result["mode"]        = mode
    result["target"]      = target
    return result

# =============================================================================
# CSV LOGGING
# =============================================================================

COLUMNS = [
    "trial_id", "timestamp", "mode", "target",
    "final_cmd", "voice_cmd", "eeg_cmd",
    "correct", "rejected", "latency_sec", "eeg_score",
]

def open_csv(path: str):
    existed = os.path.exists(path)
    f = open(path, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
    if not existed:
        writer.writeheader()
    return f, writer

# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    print("=" * 52)
    print("   MULTIMODAL UAV — AUTOMATED TRIAL SEQUENCER")
    print("=" * 52)
    print("\nEnsure these are running BEFORE continuing:")
    print("  Terminal 1:  python ssvep/eeg_server.py")
    print("  Terminal 2:  python ground_station.py")
    input("\nPress Enter when both are ready ...")

    mode     = pick_mode()
    sequence = pick_sequence()

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"results_{mode}_{timestamp_str}.csv"

    os.makedirs("results", exist_ok=True)
    csv_path = os.path.join("results", f"{mode}_{timestamp_str}.csv")

    print(f"\n  Mode:      {mode}")
    print(f"  Sequence:  {sequence['name']}")
    print(f"  Commands:  {sequence['sequence']}")
    print(f"  Output:    {csv_path}")

    send_sock   = make_send_socket()
    listen_sock = make_listen_socket(TELEMETRY_LISTEN_PORT, timeout=0.5)
    csv_file, writer = open_csv(csv_path)

    results = []
    trial_id = 1

    try:
        for target in sequence["sequence"]:
            result = run_trial(trial_id, mode, target, send_sock, listen_sock)
            result["timestamp"] = datetime.now().isoformat(timespec="milliseconds")
            writer.writerow(result)
            csv_file.flush()
            results.append(result)
            trial_id += 1
            time.sleep(INTER_TRIAL_SEC)

    except KeyboardInterrupt:
        print("\n\n  [Interrupted]")

    finally:
        send_sock.close()
        listen_sock.close()
        csv_file.close()

    # Summary
    total    = len(results)
    correct  = sum(1 for r in results if r["correct"])
    rejected = sum(1 for r in results if r["rejected"])
    latencies = [r["latency_sec"] for r in results if not r["rejected"]]
    mean_lat = round(sum(latencies) / len(latencies), 4) if latencies else 0.0

    print(f"\n{'=' * 52}")
    print(f"  SEQUENCE COMPLETE")
    print(f"{'=' * 52}")
    print(f"  Trials:      {total}")
    print(f"  Correct:     {correct} / {total}")
    print(f"  Rejected:    {rejected}")
    print(f"  Mean latency: {mean_lat:.3f}s  (executed trials only)")
    print(f"  Results:     {csv_path}")
    print("=" * 52)


if __name__ == "__main__":
    main()
