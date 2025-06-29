import uasyncio as asyncio
import random
import ws2812b

# === Config ===
PIN_NUM = 28
MAX_ACTIVE = 2

COLORS = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255),
    (255, 255, 255), (255, 0, 255),
    (255, 255, 0), (0, 255, 255)
]

# === Fonction de combinaison des couches ===
def MyEt(*colors):
    r = max((c[0] for c in colors), default=0)
    g = max((c[1] for c in colors), default=0)
    b = max((c[2] for c in colors), default=0)
    return (r, g, b)

# === Sémaphore simple compatible MicroPython ===
class SimpleAsyncSemaphore:
    def __init__(self, max_tokens):
        self._tokens = max_tokens

    async def __aenter__(self):
        while self._tokens <= 0:
            await asyncio.sleep(0.05)
        self._tokens -= 1

    async def __aexit__(self, exc_type, exc, tb):
        self._tokens += 1

# === Classe de base LEDBlock ===
class LEDBlock:
    def __init__(self, indices):
        self.indices = indices
        self.size = len(indices)
        self.active_layers = {}
        self.composition_fn = MyEt

    def set_layer(self, name, color_list):
        self.active_layers[name] = color_list
        self._update_combined()

    def clear_layer(self, name):
        if name in self.active_layers:
            del self.active_layers[name]
            self._update_combined()

    def _update_combined(self):
        # Le flash remplace tout si actif
        if "flash" in self.active_layers:
            flash_layer = self.active_layers["flash"]
            for i, pix in enumerate(self.indices):
                r, g, b = flash_layer[i]
                leds.pixels[pix] = (g << 16) | (r << 8) | b
        else:
            for i, pix in enumerate(self.indices):
                colors = [layer[i] for name, layer in self.active_layers.items()
                          if name != "flash" and i < len(layer)]
                r, g, b = self.composition_fn(*colors)
                leds.pixels[pix] = (g << 16) | (r << 8) | b
        leds.show()

    async def fade(self, color, fade_in=True, steps=30, delay=0.05):
        for step in range(steps + 1):
            t = step / steps if fade_in else (1 - step / steps)
            r = int(color[0] * t)
            g = int(color[1] * t)
            b = int(color[2] * t)
            self.set_layer("fade", [(r, g, b)] * self.size)
            await asyncio.sleep(delay)
        if not fade_in:
            self.clear_layer("fade")

    async def full_light(self, color):
        self.set_layer("flash", [color] * self.size)
        await asyncio.sleep(10)
        self.clear_layer("flash")

    async def auto_flash_loop(self):
        while True:
            await asyncio.sleep(random.uniform(120, 240))
            await self.full_light(random.choice(COLORS))

# === Sous-classes de blocs ===
class Block8LED(LEDBlock):
    def __init__(self, start_index):
        super().__init__([start_index + i for i in range(8)])

class Block6LED(LEDBlock):
    def __init__(self, start_index):
        super().__init__([start_index + i for i in range(6)])

class BlockMiroirInfini(LEDBlock):
    def __init__(self, start_index):
        super().__init__([start_index + i for i in range(24)])

    async def spinning_effect(self, delay=0.4):
        while True:
            for i in range(self.size):
                frame = [(0, 0, 0)] * self.size
                frame[i] = random.choice(COLORS)
                self.set_layer("spin", frame)
                await asyncio.sleep(delay)

# === Construction dynamique des blocs ===
blocks = []
current_index = 0
for cls in [Block8LED, Block8LED, Block8LED, Block8LED, Block6LED, BlockMiroirInfini]:
    block = cls(current_index)
    blocks.append(block)
    current_index += block.size
    if isinstance(block, BlockMiroirInfini):
        miroir = block

# Initialisation des LEDs
NUM_LEDS = sum(b.size for b in blocks)
leds = ws2812b.ws2812b(NUM_LEDS, 0, PIN_NUM)

# === Tâche principale pour chaque bloc ===
async def block_loop(block, semaphore):
    while True:
        async with semaphore:
            color = random.choice(COLORS)
            await block.fade(color, fade_in=True)
            await asyncio.sleep(random.uniform(5, 30))
            await block.fade(color, fade_in=False)
        await asyncio.sleep(random.uniform(5, 30))

# === Programme principal ===
async def main():
    semaphore = SimpleAsyncSemaphore(MAX_ACTIVE)
    tasks = []

    for block in blocks:
        tasks.append(asyncio.create_task(block_loop(block, semaphore)))
        tasks.append(asyncio.create_task(block.auto_flash_loop()))
    # Lancement de l'effet tournant du miroir
    tasks.append(asyncio.create_task(miroir.spinning_effect()))

    await asyncio.gather(*tasks)

asyncio.run(main())
