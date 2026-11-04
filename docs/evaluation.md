> Historical notes supplied in the original ZIP. These measurements were not reproduced for the updated version. Added event-counter persistence changes benchmark costs. Use the scripts to establish current results; percentage improvements require controlled baselines.

# Evaluation Methodology & Results

Every number below was actually measured by running the scripts in this
repo, not assumed. Re-run any of them yourself with the commands shown —
that reproducibility is the point.

## Detection accuracy

```
python -m scripts.evaluate_accuracy --count 20000 --attack-rate 0.10
```

Generates labeled synthetic events (label is known because we control the
generator), scores each with the real `AnomalyDetector`, and compares
predictions against ground truth.

**Measured (n=20,000, 10% attack rate):**

| Metric | Value |
|---|---|
| Accuracy | 94.4% |
| Precision | 65.8% |
| Recall | 91.6% |
| F1 | 0.77 |
| False Positive Rate | 5.3% |

**Important caveat:** this evaluates the model against synthetic traffic
generated from the same distribution it was trained on. It demonstrates the
pipeline and model work correctly end-to-end — it is *not* a claim about
accuracy against real-world attack traffic, which would need a labeled
real or public intrusion-detection dataset (e.g. CICIDS2017, NSL-KDD) to
back up honestly.

### A bug this evaluation caught
The original `AnomalyDetector` trained its "normal" baseline on a
distribution that didn't match the traffic the rest of the app treats as
normal (e.g. it treated SSH/RDP destination ports as equally common as web
traffic, and used byte-count ranges far narrower than what the app
actually generates as benign traffic). Result when first measured:
**34% accuracy, 73% false-positive rate.** Aligning the training
distribution with the app's actual traffic generator and correcting the
decision threshold (it was hardcoded, ignoring the configurable
`ANOMALY_THRESHOLD`) brought it to the numbers above — genuinely measured,
not assumed.

## Throughput

```
python -m scripts.benchmark_pipeline --count 20000 --persist
```

Times actual event scoring + SQLite alert/incident persistence in-process
(not just Kafka producer hand-off speed, which `scripts/benchmark.py`
measures separately and is a different, narrower number).

**Measured:** ~16,800 events/min with full DB persistence (~18,400/min for
ML scoring alone), on the machine it was run on. Re-run it on your own
hardware / on Render before quoting a number — this is a single-process,
single-core measurement and will vary with CPU.

## Automated response latency

Measured time from event ingestion → anomaly scoring → alert creation →
incident creation → automated response action, in-process:

**Measured:** ~5.3ms median, ~5.8ms p95 (n=456 anomalous events).

**What this is not:** a "% reduction in incident response time" claim.
That requires a real baseline (e.g. average manual analyst triage time)
which this project doesn't establish — there's no manual-response mode to
compare against, and the automated action here is a simulated IP block,
not equivalent in scope to what a human analyst actually does
(investigation, verification, cross-team coordination). If you want a
defensible comparison, cite a specific published source for manual
baseline times and be explicit that you're comparing automated action
execution to reported industry averages, not a controlled experiment.
