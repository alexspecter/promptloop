import psutil

class MemoryGuardian:
    def __init__(self, max_ram_percent: float = 95.0, max_swap_gb: float = 0.5):
        """
        A strict watchdog for system memory.
        
        Args:
            max_ram_percent (float): Stop if RAM usage exceeds this % (Default: 95.0)
            max_swap_gb (float): Stop if Swap usage exceeds this GB (Default: 0.0 for zero-tolerance)
        """
        self.max_ram_percent = max_ram_percent
        self.max_swap_bytes = max_swap_gb * (1024 ** 3) # Convert GB to Bytes
        self.triggered = False

    def check(self):
        """
        Checks system memory status. Raises MemoryError if limits are exceeded.
        """
        # 1. Check RAM Pressure (Prevention)
        mem = psutil.virtual_memory()
        if mem.percent > self.max_ram_percent:
            self.triggered = True
            raise MemoryError(
                f"⚠️ CRITICAL: RAM reached {mem.percent}% (Limit: {self.max_ram_percent}%). "
                "Stopping to prevent swap."
            )

        # 2. Check Swap Usage (The Fail-Safe)
        # If strict 0.0 is set, any swap usage triggers this.
        swap = psutil.swap_memory()
        if swap.used > self.max_swap_bytes:
            self.triggered = True
            used_gb = swap.used / (1024 ** 3)
            limit_gb = self.max_swap_bytes / (1024 ** 3)
            raise MemoryError(
                f"⚠️ CRITICAL: System started swapping! ({used_gb:.2f}GB used). "
                "Immediate shutdown initiated to save system stability."
            )

def get_memory_stats() -> str:
    """Returns a formatted string of current memory stats for UI display."""
    mem = psutil.virtual_memory()
    return f"[RAM: {mem.percent}%]"