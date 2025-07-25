# failure_simulation.py
import subprocess
import time
import signal
import os
from contextlib import contextmanager

class FailureSimulator:
    """Simulate real-world failure scenarios"""
    
    @contextmanager
    def simulate_network_failure(self):
        """Simulate network connectivity issues"""
        # Block outbound connections (Unix/Linux only)
        if os.name != 'nt':  # Not Windows
            try:
                subprocess.run(['sudo', 'iptables', '-A', 'OUTPUT', '-p', 'tcp', '--dport', '443', '-j', 'DROP'], 
                             check=False, capture_output=True)
                yield
            finally:
                subprocess.run(['sudo', 'iptables', '-D', 'OUTPUT', '-p', 'tcp', '--dport', '443', '-j', 'DROP'], 
                             check=False, capture_output=True)
        else:
            print("Network simulation not available on Windows")
            yield

    @contextmanager
    def simulate_high_cpu_load(self):
        """Simulate high CPU load conditions"""
        import multiprocessing
        
        def cpu_stress():
            while True:
                pass
        
        processes = []
        try:
            # Start CPU stress processes
            for _ in range(multiprocessing.cpu_count()):
                p = multiprocessing.Process(target=cpu_stress)
                p.start()
                processes.append(p)
            
            time.sleep(1)  # Let CPU load build up
            yield
        finally:
            for p in processes:
                p.terminate()
                p.join()

    @contextmanager
    def simulate_memory_pressure(self):
        """Simulate memory pressure conditions"""
        try:
            # Allocate large amounts of memory
            memory_hogs = []
            for _ in range(10):
                memory_hogs.append(bytearray(100 * 1024 * 1024))  # 100MB each
            yield
        finally:
            del memory_hogs

def test_system_under_stress():
    """Test the complete system under various stress conditions"""
    simulator = FailureSimulator()
    
    # Test under high CPU load
    with simulator.simulate_high_cpu_load():
        print("🔥 Testing under high CPU load...")
        result = subprocess.run(['python', 'main.py'], 
                              env={**os.environ, 'MAX_ATTEMPTS': '2'},
                              capture_output=True, text=True, timeout=120)
        assert result.returncode in [0, 1]  # Should exit gracefully
    
    # Test under memory pressure
    with simulator.simulate_memory_pressure():
        print("🧠 Testing under memory pressure...")
        result = subprocess.run(['python', 'main.py'], 
                              env={**os.environ, 'MAX_ATTEMPTS': '2'},
                              capture_output=True, text=True, timeout=120)
        assert result.returncode in [0, 1]  # Should exit gracefully

if __name__ == "__main__":
    test_system_under_stress()
