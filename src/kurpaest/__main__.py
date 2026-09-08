"""Launch the kurpaest HTTP entry with uvicorn."""

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the kurpaest.lt API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run("kurpaest.app:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
