import argparse
import sys
import io

# Ensure UTF-8 output for Windows terminals
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from src.engine.policy_rate_engine import PolicyRateEngine
from src.engine.gdp_nowcast_engine import GDPCastNowEngine, format_report


def main():
    parser = argparse.ArgumentParser(
        description="AI Economist Skill: Central Bank Policy & GDP Nowcasting"
    )
    parser.add_argument(
        "task",
        choices=["policy", "gdp"],
        help="Task to perform: 'policy' for rate analysis or 'gdp' for nowcasting",
    )
    parser.add_argument(
        "--country",
        default="US",
        choices=["US", "Canada"],
        help="Target country (default: US)",
    )

    args = parser.parse_args()

    if args.task == "policy":
        engine = PolicyRateEngine()
        result = engine.generate_analysis(args.country)
        print(result["report"])
        print(f"\n[Visual] Chart generated at: {result['image_path']}")

    elif args.task == "gdp":
        engine = GDPCastNowEngine(args.country)
        res = engine.run_nowcast()
        report = format_report(args.country, res)
        print(report)


if __name__ == "__main__":
    main()
