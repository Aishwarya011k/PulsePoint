"""
flaky_server.py — A test target that randomly goes up/down.

Use this as a PulsePoint monitored target to test your Prober Worker's
ability to detect incidents (down transitions) and resolutions (up transitions),
plus varying latency.

Run:
    pip install flask
    python flaky_server.py

Then register http://localhost:5050/health as a target in PulsePoint.

Behavior:
- ~80% of requests succeed (200 OK)
- ~20% of requests fail (randomly 500 or 503)
- Response time randomly varies between 20ms and 2000ms to simulate
  degradation before a full outage
- Every ~30 seconds, there's a chance of entering a "bad patch" (elevated
  failure rate for a stretch) to simulate a realistic incident window,
  not just isolated blips
"""

import random
import time
from flask import Flask, jsonify

app = Flask(__name__)

# Tunable parameters
BASE_FAILURE_RATE = 0.20        # 20% chance of failure under normal conditions
BAD_PATCH_FAILURE_RATE = 0.85   # 85% chance of failure during a "bad patch"
BAD_PATCH_CHANCE_PER_REQUEST = 0.02   # chance a bad patch starts on any given request
BAD_PATCH_DURATION_SECONDS = 25       # how long a bad patch lasts once triggered

_bad_patch_until = 0.0  # timestamp until which we're in a "bad patch"


@app.route("/health")
def health():
    global _bad_patch_until
    now = time.time()

    # Randomly trigger a bad patch (simulates a real incident window)
    if now > _bad_patch_until and random.random() < BAD_PATCH_CHANCE_PER_REQUEST:
        _bad_patch_until = now + BAD_PATCH_DURATION_SECONDS
        print(f"[flaky_server] Entering bad patch for {BAD_PATCH_DURATION_SECONDS}s")

    in_bad_patch = now < _bad_patch_until
    failure_rate = BAD_PATCH_FAILURE_RATE if in_bad_patch else BASE_FAILURE_RATE

    # Simulate variable latency — higher during bad patches
    if in_bad_patch:
        delay = random.uniform(0.5, 2.0)
    else:
        delay = random.uniform(0.02, 0.3)
    time.sleep(delay)

    if random.random() < failure_rate:
        status_code = random.choice([500, 502, 503])
        return jsonify({
            "status": "error",
            "bad_patch": in_bad_patch,
            "response_time_ms": round(delay * 1000, 1),
        }), status_code

    return jsonify({
        "status": "ok",
        "bad_patch": in_bad_patch,
        "response_time_ms": round(delay * 1000, 1),
    }), 200


@app.route("/")
def index():
    return "flaky_server is running — hit /health to check status"


if __name__ == "__main__":
    print("flaky_server running at http://localhost:5050/health")
    print(f"Base failure rate: {BASE_FAILURE_RATE*100:.0f}% | "
          f"Bad patch failure rate: {BAD_PATCH_FAILURE_RATE*100:.0f}%")
    app.run(host="0.0.0.0", port=5050)