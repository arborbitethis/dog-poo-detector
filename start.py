#!/usr/bin/env python3
"""
Startup script to run both backend and frontend servers together.
"""

import subprocess
import signal
import sys
import time
import os
from pathlib import Path

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

processes = []

def print_header():
    """Print startup header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  🐕 Dog Poop Detector - Development Server{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")

def cleanup(signum=None, frame=None):
    """Cleanup processes on exit."""
    print(f"\n{Colors.YELLOW}Shutting down servers...{Colors.END}")

    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

    print(f"{Colors.GREEN}All servers stopped.{Colors.END}")
    sys.exit(0)

def check_dependencies():
    """Check if required dependencies are installed."""
    print(f"{Colors.BLUE}Checking dependencies...{Colors.END}")

    # Check Python dependencies
    try:
        import yaml
        import cv2
        import fastapi
        import uvicorn
        print(f"{Colors.GREEN}✓ Python dependencies installed{Colors.END}")
    except ImportError as e:
        print(f"{Colors.RED}✗ Missing Python dependency: {e.name}{Colors.END}")
        print(f"{Colors.YELLOW}Run: pip install -r requirements.txt{Colors.END}")
        sys.exit(1)

    # Check if Node.js is available
    try:
        result = subprocess.run(['node', '--version'],
                              capture_output=True,
                              text=True,
                              check=True)
        print(f"{Colors.GREEN}✓ Node.js installed ({result.stdout.strip()}){Colors.END}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"{Colors.RED}✗ Node.js not found{Colors.END}")
        print(f"{Colors.YELLOW}Install Node.js from: https://nodejs.org{Colors.END}")
        sys.exit(1)

    # Check if frontend dependencies are installed
    node_modules = Path('frontend/node_modules')
    if not node_modules.exists():
        print(f"{Colors.YELLOW}Installing frontend dependencies...{Colors.END}")
        subprocess.run(['npm', 'install'], cwd='frontend', check=True)
        print(f"{Colors.GREEN}✓ Frontend dependencies installed{Colors.END}")
    else:
        print(f"{Colors.GREEN}✓ Frontend dependencies installed{Colors.END}")

def start_backend():
    """Start the backend server."""
    print(f"\n{Colors.BLUE}Starting backend server (port 8080)...{Colors.END}")

    # Use demo.py which includes web server
    backend_process = subprocess.Popen(
        [sys.executable, 'demo.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )

    processes.append(backend_process)

    # Wait for backend to start
    time.sleep(2)

    if backend_process.poll() is None:
        print(f"{Colors.GREEN}✓ Backend server started{Colors.END}")
        print(f"{Colors.CYAN}  API: http://localhost:8080/api/status{Colors.END}")
        return backend_process
    else:
        print(f"{Colors.RED}✗ Backend failed to start{Colors.END}")
        sys.exit(1)

def start_frontend():
    """Start the frontend dev server."""
    print(f"\n{Colors.BLUE}Starting frontend dev server (port 5173)...{Colors.END}")

    frontend_process = subprocess.Popen(
        ['npm', 'run', 'dev'],
        cwd='frontend',
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )

    processes.append(frontend_process)

    # Wait for frontend to start
    time.sleep(3)

    if frontend_process.poll() is None:
        print(f"{Colors.GREEN}✓ Frontend dev server started{Colors.END}")
        return frontend_process
    else:
        print(f"{Colors.RED}✗ Frontend failed to start{Colors.END}")
        sys.exit(1)

def print_ready():
    """Print ready message."""
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}  ✓ All servers running!{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.END}\n")

    print(f"{Colors.BOLD}🌐 Open your browser:{Colors.END}")
    print(f"{Colors.CYAN}   http://localhost:5173{Colors.END}\n")

    print(f"{Colors.BOLD}Endpoints:{Colors.END}")
    print(f"   Frontend: {Colors.CYAN}http://localhost:5173{Colors.END}")
    print(f"   Backend:  {Colors.CYAN}http://localhost:8080{Colors.END}")
    print(f"   API:      {Colors.CYAN}http://localhost:8080/api/status{Colors.END}")
    print(f"   Video:    {Colors.CYAN}http://localhost:8080/video/feed{Colors.END}\n")

    print(f"{Colors.YELLOW}Press Ctrl+C to stop all servers{Colors.END}\n")

def tail_logs(backend_process, frontend_process):
    """Tail logs from both processes."""
    import select

    while True:
        # Check if processes are still running
        if backend_process.poll() is not None:
            print(f"{Colors.RED}Backend process exited{Colors.END}")
            cleanup()

        if frontend_process.poll() is not None:
            print(f"{Colors.RED}Frontend process exited{Colors.END}")
            cleanup()

        # Read and print output
        try:
            # Read from backend
            line = backend_process.stdout.readline()
            if line:
                print(f"{Colors.BLUE}[Backend]{Colors.END} {line.rstrip()}")

            # Read from frontend
            line = frontend_process.stdout.readline()
            if line:
                # Filter out verbose Vite output
                if 'hmr update' not in line.lower() and 'page reload' not in line.lower():
                    print(f"{Colors.CYAN}[Frontend]{Colors.END} {line.rstrip()}")

            time.sleep(0.1)
        except KeyboardInterrupt:
            cleanup()

def main():
    """Main entry point."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print_header()

    # Check dependencies
    check_dependencies()

    # Start servers
    backend_process = start_backend()
    frontend_process = start_frontend()

    # Print ready message
    print_ready()

    # Tail logs
    try:
        tail_logs(backend_process, frontend_process)
    except KeyboardInterrupt:
        cleanup()

if __name__ == '__main__':
    main()
