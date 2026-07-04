"""
PERT Three-Point Estimation Calculator
Usage: python estimate.py <optimistic> <most_likely> <pessimistic>
Example: python estimate.py 2 4 8
"""
import sys


def pert(optimistic: float, most_likely: float, pessimistic: float) -> dict:
    expected = (optimistic + 4 * most_likely + pessimistic) / 6
    std_dev = (pessimistic - optimistic) / 6
    variance = std_dev ** 2
    return {
        "optimistic": optimistic,
        "most_likely": most_likely,
        "pessimistic": pessimistic,
        "expected": round(expected, 2),
        "std_dev": round(std_dev, 2),
        "variance": round(variance, 2),
    }


def size_to_points(size: str) -> tuple:
    mapping = {
        "xs": (0.5, 1, 2),
        "s": (1, 2, 3),
        "m": (2, 3, 5),
        "l": (4, 5, 8),
        "xl": (5, 8, 13),
        "xxl": (8, 13, 21),
    }
    return mapping.get(size.lower(), (2, 3, 5))


if __name__ == "__main__":
    if len(sys.argv) == 4:
        o, m, p = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
    elif len(sys.argv) == 2:
        o, m, p = size_to_points(sys.argv[1])
    else:
        print("Usage: python estimate.py <optimistic> <most_likely> <pessimistic>")
        print("   or: python estimate.py <size: xs|s|m|l|xl|xxl>")
        sys.exit(1)

    result = pert(o, m, p)
    print(f"PERT Estimate: {result['expected']} story points")
    print(f"  Range: {result['optimistic']} - {result['pessimistic']}")
    print(f"  Std Dev: {result['std_dev']} | Variance: {result['variance']}")
