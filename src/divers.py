import uasyncio as asyncio
import gc

REFRESH_INTERVAL = 0.05  # actualisation globale (20 FPS)

async def memory_monitor_loop(interval=1):
    while True:
        free = gc.mem_free()
        print("[MEMORY] Libre:", free, "octets")
        if free < 10_000:
            print("[WARNING] Mémoire faible !")
            # Optionnel : désactiver des effets, purger des couches, etc.
        await asyncio.sleep(interval)

# === Sémaphore simple compatible MicroPython ===

class SimpleAsyncSemaphore:
    def __init__(self, max_tokens):
        self._max_tokens = max_tokens
        self._tokens = max_tokens
        self._lock = asyncio.Lock()
        self._waiters = []

    async def __aenter__(self):
        while True:
            async with self._lock:
                if self._tokens > 0:
                    self._tokens -= 1
                    return
            await asyncio.sleep(0.01)  # Petit délai pour éviter une boucle trop rapide

    async def __aexit__(self, exc_type, exc, tb):
        async with self._lock:
            self._tokens += 1

