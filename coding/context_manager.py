import time


# TODO: Implement a context manager that measures the time a code takes to execute.

with timing_context():
    # Some time-consuming work
    time.sleep(2)

# Expected output: Execution time: 2 seconds
