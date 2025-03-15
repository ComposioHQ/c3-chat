#!/usr/bin/env python
"""
Runner script for the C3 Chat application.

This script can be used to start the application without using the Chainlit CLI directly.
"""
import os
import sys
import subprocess

def main():
    """Run the Chainlit application with the specified flags."""
    # Get the absolute path to the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set PYTHONPATH to include the current directory
    os.environ["PYTHONPATH"] = current_dir
    
    # Default command with watch mode and host flags
    cmd = ["chainlit", "run", "main.py", "-w", "-h"]
    
    # Get additional arguments
    args = sys.argv[1:]
    if args:
        cmd.extend(args)
    
    print(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main() 