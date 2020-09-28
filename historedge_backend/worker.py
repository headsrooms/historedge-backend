import argparse
import subprocess
import uuid

from loguru import logger


def create_process(executable, consumer):
    return (
        consumer,
        subprocess.Popen(
            ["nohup", "python", "-m", executable, consumer], start_new_session=True,
        ),
    )


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("exec", help="command or program to execute in workers")
    parser.add_argument(
        "-w",
        "--workers",
        help="number of workers",
        nargs="?",
        type=int,
        const=15,
        default=15,
    )

    return parser


def main() -> None:
    parser = init_argparse()
    args = parser.parse_args()

    processes = [
        create_process(args.exec, str(uuid.uuid4())) for _ in range(args.workers)
    ]

    for consumer, p in processes:
        if p.wait() != 0:
            logger.error(f"There was an error in {consumer}")


if __name__ == "__main__":
    main()
