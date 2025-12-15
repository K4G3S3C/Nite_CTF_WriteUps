# Floating Point Guardian / \ AI

- CTF: NiteCTF 2025
- Category: AI
- Author: K4G3SEC
- Solver: W4ST3D
- Flag: `nite{br0_i5_n0t_g0nn4_b3_t4K1n6_any1s_j0bs_34x}`

---

## Challenge
> "Trick the Neural Network into outputting a specific probability."

The challenge provides a C implementation of a neural network (`src.c`) taking 15 floating-point inputs. The objective is to find an input vector that results in the network outputting exactly `0.7331337420`.

---

## Overview
- **Model**: A custom dense neural network implemented in C.
- **Target**: Output probability `P = 0.7331337420`.
- **Input**: 15 float values corresponding to features like Height, Weight, BMI, etc.
- **Constraint**: Must achieve high precision (within `1e-9` epsilon).

---

## Root Cause
The neural network is a continuous, differentiable function (mostly). The inverse problem—finding inputs for a specific output—can be solved via optimization (Gradient Descent or Hill Climbing). Because we have the source, we can replicate the forward pass locally.

---

## Exploitation Steps
1. **Port to Python**: Rewrite the C forward pass in Python for ease of use.
2. **Define Loss**: `Loss = abs(Forward(x) - Target)`.
3. **Local Search**:
   - Start with a random input vector.
   - Perturb each dimension by small steps (`±1.0`, `±0.1`, `±0.01`).
   - If Loss decreases, accept the new step.
4. **Fine Tuning**: As Loss approaches zero, reduce the step size to converge to the exact float representation.
5. **Submit**: Send the optimized 15 floats to the server to unlock the flag.

---
