"""Register the deployed digest webhook on a Friday schedule."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.digest_service import ScheduleRequest, register_weekly_digest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_url", help="Public URL of the deployed /digest/weekly route")
    args = parser.parse_args()
    result = register_weekly_digest(ScheduleRequest(task_url=args.task_url))
    print(f"Scheduled weekly digest: {result.job_id}")


if __name__ == "__main__":
    main()
