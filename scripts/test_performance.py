import asyncio
import time
import sys
import os

# Add parent directory to path to import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import run_bot

async def test():
    print("Starting Performance Test...")
    start_time = time.time()
    try:
        await run_bot()
    except Exception as e:
        print(f"Run failed: {e}")
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"\nPERFORMANCE SUMMARY")
    print(f"-------------------")
    print(f"Total Execution Time: {duration:.2f} seconds ({duration/60:.2f} minutes)")
    
    # Check report for stats
    report_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "last_run_report.md")
    if os.path.exists(report_path):
        print(f"\nReading Report: {report_path}")
        with open(report_path, "r", encoding="utf-8") as f:
            print(f.read())
    else:
        print("Report file not found.")

if __name__ == "__main__":
    asyncio.run(test())
