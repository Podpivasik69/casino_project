"""
Test multiplier growth formula
"""
import math

print("=" * 60)
print("MULTIPLIER GROWTH TEST")
print("=" * 60)

print("\nFormula: multiplier = 1.00 * (1.06 ^ elapsed_seconds)")
print("\nTime -> Multiplier:")
print("-" * 40)

test_times = [0, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 40, 50, 60]

for seconds in test_times:
    multiplier = math.pow(1.06, seconds)
    print(f"{seconds:3d}s -> {multiplier:6.2f}x")

print("\n" + "=" * 60)
print("This gives smooth, predictable growth:")
print("- 0-10s: 1.00x to 1.79x (slow start)")
print("- 10-30s: 1.79x to 5.74x (medium growth)")
print("- 30s+: exponential growth")
print("=" * 60)
