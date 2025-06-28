import uasyncio as asyncio
import random
import ws2812b


# ----------- Configuration générale -----------

PIN_NUM = 28
NUM_LEDS_TOTAL = 40
leds = ws2812b.ws2812b(NUM_LEDS_TOTAL, 0, PIN_NUM)

# Couleurs prédéfinies
COLORS = [
    (255, 0, 0),   # Rouge
    (0, 255, 0),   # Vert
    (0, 0, 255),   # Bleu
    (255, 255, 255),
    (255, 0, 255),
    (255, 255, 0),
    (0, 255, 255), 
]

# Pour limiter le nombre de blocs actifs
active_blocks = set()
MAX_ACTIVE = 2


# ----------- Classe de base pour un bloc -----------

class LEDBlock:
    def __init__(self, name, indices):
        self.name = name
        self.indices = indices

    def set_color(self, color):
        r, g, b = color
        grb = (g << 16) | (r << 8) | b
        for i in self.indices:
            leds.pixels[i] = grb
        leds.show()

    async def fade(self, color, fade_in=True, steps=30, delay=0.05):
        for step in range(steps + 1):
            t = step / steps if fade_in else (1 - step / steps)
            r = int(color[0] * t)
            g = int(color[1] * t)
            b = int(color[2] * t)
            self.set_color((r, g, b))
            await asyncio.sleep(delay)

    async def run(self):
        global active_blocks
        while True:
            while len(active_blocks) >= MAX_ACTIVE:
                await asyncio.sleep(0.5)

            active_blocks.add(self.name)
            color = random.choice(COLORS)
            on_time = random.uniform(5, 30)
            off_time = random.uniform(5, 30)

            await self.fade(color, fade_in=True)
            await asyncio.sleep(on_time)
            await self.fade(color, fade_in=False)

            active_blocks.remove(self.name)
            await asyncio.sleep(off_time)


# ----------- Blocs spécifiques (optionnels pour extension) -----------

class Block8LED(LEDBlock):
    def __init__(self, name, start_index):
        super().__init__(name, list(range(start_index, start_index + 8)))

class Block6LED(LEDBlock):
    def __init__(self, name, start_index):
        super().__init__(name, list(range(start_index, start_index + 6)))

class MirrorBlock24LED(LEDBlock):
    def __init__(self, name, start_index):
        super().__init__(name, list(range(start_index, start_index + 24)))
        # Tu pourrais ajouter un effet miroir spécifique ici

# ----------- Gestionnaire d’étagère -----------

class ShelfLighting:
    def __init__(self):
        self.blocks = []

    def add_block(self, block):
        self.blocks.append(block)

    async def run(self):
        tasks = [asyncio.create_task(block.run()) for block in self.blocks]
        await asyncio.gather(*tasks)


# ----------- Construction et lancement -----------

shelf = ShelfLighting()
shelf.add_block(Block8LED("A", 0))
shelf.add_block(Block8LED("B", 8))
shelf.add_block(Block6LED("C", 16))
shelf.add_block(Block6LED("D", 22))
shelf.add_block(MirrorBlock24LED("E", 24))

asyncio.run(shelf.run())
