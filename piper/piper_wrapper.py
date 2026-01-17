#!/usr/bin/env python3
"""
Wrapper to configure ONNX Runtime thread settings before starting wyoming-piper
"""
import os
import sys
import asyncio
import logging

# Ensure output is unbuffered
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Configure logging to show all output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s:%(message)s',
    stream=sys.stdout
)

# Configure ONNX Runtime threading to prevent affinity errors
# This must be done before importing onnxruntime
os.environ['OMP_NUM_THREADS'] = '4'
os.environ['OMP_WAIT_POLICY'] = 'PASSIVE'
os.environ['OMP_PROC_BIND'] = 'false'

# Patch onnxruntime InferenceSession to set thread options
try:
    import onnxruntime as ort

    original_init = ort.InferenceSession.__init__

    def patched_init(self, *args, **kwargs):
        # Create session options if not provided
        if 'sess_options' not in kwargs or kwargs['sess_options'] is None:
            sess_options = ort.SessionOptions()
            sess_options.intra_op_num_threads = 4
            sess_options.inter_op_num_threads = 4
            sess_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            kwargs['sess_options'] = sess_options
        else:
            # Modify existing session options
            kwargs['sess_options'].intra_op_num_threads = 4
            kwargs['sess_options'].inter_op_num_threads = 4
            kwargs['sess_options'].execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

        return original_init(self, *args, **kwargs)

    ort.InferenceSession.__init__ = patched_init
except ImportError:
    print("Warning: Could not import onnxruntime to patch thread settings", file=sys.stderr)

# Now run wyoming_piper
from wyoming_piper.__main__ import main

if __name__ == '__main__':
    asyncio.run(main())
