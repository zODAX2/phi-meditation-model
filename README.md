# Φ: an equation simulation for meditation practice

**A controllable way to push beyond human limits.** Φ is a minimal threshold model of a self-sustaining absorbed meditative state, with an interactive simulator, reproducible figures and a step-by-step single-case protocol for testing it.

```
∂Φ/∂t = (αI − β)Φ + κΦ² − γΦ³ + D∇²Φ + s + η
```

Φ is a latent variable: the intensity of the absorbed state at each point of a two-dimensional body map. It is not claimed to be a physical field. Each term is something a practitioner trains or measures:

| Term | Meaning |
| --- | --- |
| α | coupling: how strongly attention engages body signals |
| I | richness: how many body regions are bound into one state |
| β | noise: mind-wandering and arousal noise |
| κ | self-feedback: the pleasure–attention loop |
| γ | ceiling: saturation that caps the state at a plateau |
| D | spread across the body map |
| s | steady drive: a generated spark (goodwill, recalled joy) |
| η | fluctuations: a noticed spark |

## Why "controllable"

With r = αI − β, the model has a window −κ²/4γ < r < 0 in which rest and the absorbed state coexist. Inside it:

- **Entry** needs a spark above a threshold, or r crossing 0.
- **The ceiling** γ caps the state at a plateau. Without it (γ = 0) the state grows without limit.
- **Exit** is a deliberate move of r below −κ²/4γ: the off switch.

Because of this hysteresis, the same settings can hold either rest or the absorbed state depending on history, which is what the protocol's release test measures.

"Beyond human limits" is defined operationally: beyond the practitioner's own measured baseline and beyond an active paced-breathing control, on instrument-checked outcomes such as voluntary heart-rate change with the breath held constant, effortless sustained attention, and persistence after release.

## What is here

| Path | What it is |
| --- | --- |
| [`paper/phi-controllable-absorption.pdf`](paper/phi-controllable-absorption.pdf) | The paper: model, analysis, predictions, protocol summary, limitations, safety |
| [`simulator/index.html`](simulator/index.html) | Interactive simulator: open it in any browser, no install |
| [`protocol/protocol.md`](protocol/protocol.md) | The full practice, step by step: drills, session, comparison method, control, programme, fixes, safety, log |
| [`model/phi_model.py`](model/phi_model.py) | Reference implementation (NumPy) |
| [`model/make_figures.py`](model/make_figures.py) | Regenerates every figure and number in the paper |
| [`figures/`](figures/) | Figures and `results.json` |

## Reproduce

```bash
pip install numpy scipy matplotlib
python model/make_figures.py
```

Runs in under a minute and rewrites `figures/`.

## Seven predictions

H1 round regions hold better than points or scattered patches · H2 sparks must exceed a critical size · H3 a noise ceiling above which onset does not occur · H4 the state outlasts a paced-breathing control after release · H5 hysteresis within a session · H6 a plateau · H7 early-warning signals before gradual onsets but not after abrupt sparks. Details in the paper.

## Safety

Attention only: no forced breathing and no breath-holding. Every session ends with a deliberate off switch. Stop rules are in the protocol. This is training, not medical treatment; people with a personal or family history of psychosis or bipolar disorder should practise only with clinical oversight.

## Citation

Amarire, Z. (2026). *Φ: An Equation Simulation for Meditation Practice. A controllable way to push beyond human limits.* Version 1.0. See [`CITATION.cff`](CITATION.cff).

## Licence

Code: MIT ([`LICENSE`](LICENSE)). Paper, protocol and figures: CC BY 4.0.

Model code, simulations, figures and drafting were produced with the assistance of an AI system (Claude, Anthropic); the author directed the work and is responsible for its content.
