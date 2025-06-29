import uasyncio as asyncio
import random
import ws2812b

# === Config ===
PIN_NUM = 28
MAX_ACTIVE = 2
REFRESH_INTERVAL = 0.05  # actualisation globale (20 FPS)
GLOBAL_FLASH_INTERVAL = (120, 240)  # secondes: (min, max)

COLORS = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255),
    (255, 255, 255), (255, 0, 255),
    (255, 255, 0), (0, 255, 255)
]

# === Fonction de composition des couches ===
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
            await asyncio.sleep(REFRESH_INTERVAL)
        self._tokens -= 1

    async def __aexit__(self, exc_type, exc, tb):
        self._tokens += 1

# === Classe de base LEDBlock ===
class LEDBlock:
    def __init__(self, indices):
        self.indices = indices
        self.size = len(indices)
        self.active_layers = {}  # couche_name -> list[(r,g,b)]
        self.composition_fn = MyEt

    def set_layer(self, name, color_list):
        # ajoute ou met à jour une couche (fade, flash, spin...)
        self.active_layers[name] = color_list

    def clear_layer(self, name):
        if name in self.active_layers:
            del self.active_layers[name]

    def compute_pixels(self, buffer):
        # calcule la couleur finale par pixel via MyEt
        for i, pix in enumerate(self.indices):
            layers = [layer[i] for layer in self.active_layers.values() if i < len(layer)]
            r, g, b = self.composition_fn(*layers)
            buffer[pix] = (r, g, b)

    async def fade(self, color, fade_in=True, steps=30, delay=0.05):
        for step in range(steps + 1):
            t = step / steps if fade_in else (1 - step / steps)
            rgb = (int(color[0]*t), int(color[1]*t), int(color[2]*t))
            self.set_layer('fade', [rgb]*self.size)
            await asyncio.sleep(delay)
        if not fade_in:
            self.clear_layer('fade')

    async def full_light(self, color):
        # flash doux via fade in/out
        self.set_layer('flash', [color]*self.size)
        await asyncio.sleep(1)
        self.clear_layer('flash')

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

    async def spinning_effect(self, color=(0,0,255), delay=1):
        while True:
            for i in range(self.size):
                frame = [(0,0,0)]*self.size
                frame[i] = color
                self.set_layer('spin', frame)
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

# initialisation du buffer & LEDs
NUM_LEDS = sum(b.size for b in blocks)
buffer = [(0,0,0)] * NUM_LEDS
leds = ws2812b.ws2812b(NUM_LEDS, 0, PIN_NUM)

# === Actualisation globale ===
async def refresh_loop():
    while True:
        for block in blocks:
            block.compute_pixels(buffer)
        for idx, (r,g,b) in enumerate(buffer):
            leds.pixels[idx] = (g<<16)|(r<<8)|b
        leds.show()
        await asyncio.sleep(REFRESH_INTERVAL)

# === Tâche principale pour chaque bloc ===
async def block_loop(block, semaphore):
    while True:
        async with semaphore:
            color = random.choice(COLORS)
            await block.fade(color, fade_in=True)
            await asyncio.sleep(random.uniform(5, 30))
            await block.fade(color, fade_in=False)
        await asyncio.sleep(random.uniform(5, 30))

# === Flash global périodique ===
async def global_flash_loop():
    while True:
        interval = random.uniform(GLOBAL_FLASH_INTERVAL[0], GLOBAL_FLASH_INTERVAL[1])
        print('Next global flash in', interval)
        await asyncio.sleep(interval)
        color = random.choice(COLORS)
        # flash synchronisé sur tous les blocs
        await asyncio.gather(*(block.full_light(color) for block in blocks))

# === Programme principal ===
async def main():
    semaphore = SimpleAsyncSemaphore(MAX_ACTIVE)
    tasks = []
    tasks.extend(asyncio.create_task(block_loop(b, semaphore)) for b in blocks)
    tasks.append(asyncio.create_task(miroir.spinning_effect()))
    tasks.append(asyncio.create_task(global_flash_loop()))
    tasks.append(asyncio.create_task(refresh_loop()))
    await asyncio.gather(*tasks)

asyncio.run(main())
