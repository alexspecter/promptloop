import sys
import signal

def force_quit(sig, frame):
    print("\n\n[!] Signal received. Force quitting...")
    sys.exit(0)

def register_signal_handlers():
    signal.signal(signal.SIGINT, force_quit)