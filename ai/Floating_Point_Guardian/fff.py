#!/usr/bin/env python3
"""
Dense local search around best known solution
"""

import numpy as np
import sys
sys.path.append('.')
from solver2 import forward_pass, TARGET_PROBABILITY, EPSILON

# Best solution found so far
best_known = np.array([
    106.27198073766806,
    -299.83287012415417,
    -166.25725160766382,
    59.09137816773239,
    -88.62975748375288,
    129.15181204265036,
    263.57449889112604,
    -56.276861964985244,
    -388.7590940969317,
    228.74918967183942,
    443.43398318298205,
    -20.741302823491765,
    414.2841539144946,
    170.134247026911,
    -203.10484760957416
])

print("Dense local search around best known solution")
print(f"Target: {TARGET_PROBABILITY:.10f}")
print(f"Best known output: {forward_pass(best_known):.10f}")
print(f"Best known error: {abs(forward_pass(best_known) - TARGET_PROBABILITY):.10e}\n")

best_x = best_known.copy()
best_error = abs(forward_pass(best_known) - TARGET_PROBABILITY)
best_output = forward_pass(best_known)

# Try perturbations in each dimension
print("Trying systematic perturbations...")
for i in range(15):
    print(f"\nDimension {i+1}/15:")
    
    # Try different step sizes
    for step in [0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0]:
        for direction in [-1, 1]:
            x = best_known.copy()
            x[i] += direction * step
            
            output = forward_pass(x)
            error = abs(output - TARGET_PROBABILITY)
            
            if error < best_error:
                best_error = error
                best_x = x.copy()
                best_output = output
                print(f"  Step {direction*step:+8.1f}: error={error:.10e}, output={output:.10f} ✓")
                
                if error < EPSILON:
                    print(f"\n  ✓✓ SOLUTION FOUND!")
                    break
        
        if best_error < EPSILON:
            break
    
    if best_error < EPSILON:
        break

# Try random perturbations around best
if best_error >= EPSILON:
    print(f"\n\nTrying random perturbations around best solution...")
    for i in range(50000):
        # Small random perturbation
        perturbation = np.random.randn(15) * 10
        x = best_x + perturbation
        
        output = forward_pass(x)
        error = abs(output - TARGET_PROBABILITY)
        
        if error < best_error:
            best_error = error
            best_x = x.copy()
            best_output = output
            print(f"  Iteration {i}: error={error:.10e}, output={output:.10f}")
            
            if error < EPSILON:
                print(f"  ✓✓ SOLUTION FOUND!")
                break
        
        if i % 5000 == 0 and i > 0:
            print(f"  Processed {i} perturbations, best error: {best_error:.10e}")

# Final result
print(f"\n{'='*60}")
print(f"FINAL RESULT:")
print(f"Error: {best_error:.10e}")
print(f"Output: {best_output:.10f}")
print(f"Target: {TARGET_PROBABILITY:.10f}")
print(f"Within epsilon? {best_error < EPSILON}")
print(f"{'='*60}\n")

questions = [
    "Q1:  Height (cm)",
    "Q2:  Weight (kg)",
    "Q3:  Age (years)",
    "Q4:  Heart rate (bpm)",
    "Q5:  Sleep hours",
    "Q6:  Body temp (C)",
    "Q7:  Steps per day",
    "Q8:  Blood pressure",
    "Q9:  Calories daily",
    "Q10: BMI",
    "Q11: Water (liters)",
    "Q12: Metabolic rate",
    "Q13: Exercise hours/week",
    "Q14: Blood glucose",
    "Q15: CTF rating"
]

print("Solution values:")
for q, val in zip(questions, best_x):
    print(f"{q}: {val}")

print("\n\nFor copy-paste:")
for val in best_x:
    print(f"{val}")
