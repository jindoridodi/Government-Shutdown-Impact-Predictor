"""Small wrapper to run the model orchestrator safely from the repository root.

This executes `models.predictor` as a module (equivalent to
`python -m models.predictor`) without moving or editing that file.

Usage:
    python run_predictor.py
"""
import sys
import runpy


def main():
    try:
        # Run the models.predictor module as __main__ so its
        # ``if __name__ == '__main__'`` block executes.
        runpy.run_module("models.predictor", run_name="__main__")
    except SystemExit:
        # allow SystemExit to propagate
        raise
    except Exception as exc:
        print(f"Error running models.predictor: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
