import uasyncio as asyncio
import random

COLORS = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255),
    (255, 255, 255), (255, 0, 255),
    (255, 255, 0), (0, 255, 255)
]


# === Classe de base LEDBlock ===
class LEDBlock:
    def __init__(self, indices):
        self.indices = indices
        self.size = len(indices)
        self.active_layers = {}  # couche_name -> list[(r,g,b)]
        self.composition_fn = MyEt
        
    def set_static_color(self, color, layer='static'):
        self.set_layer(layer, [color]*self.size)

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

    async def full_light(self, color=None):
        if color is None:
            color = random.choice(COLORS)
            print("[full_light] Couleur choisie:", color)
        # Fade in
        await self.fade(color, fade_in=True, steps=20, delay=0.03)
        # Maintien plein éclairage
        await asyncio.sleep(1)
        # Fade out
        await self.fade(color, fade_in=False, steps=20, delay=0.03)


# === Sous-classes de blocs ===
class Block8LED(LEDBlock):
    def __init__(self, start_index):
        super().__init__([start_index + i for i in range(8)])

class Block6LED(LEDBlock):
    def __init__(self, start_index):
        super().__init__([start_index + i for i in range(6)])

class BlockMiroirInfini(LEDBlock):
    def __init__(self, start_index):
        super().__init__([start_index + i for i in range(36)])

    async def spinning_effect(self, color=(0,0,255), delay=1):
        while True:
            for i in range(self.size/4):
                frame = [(0,0,0)]*self.size
                frame[i] = color
                frame[18-i-1] = color
                frame[18+i] = color
                frame[36-i-1] = color
                
                self.set_layer('spin', frame)
                await asyncio.sleep(delay)
                
# === Fonction de composition des couches ===
def MyEt(*colors):
    r = max((c[0] for c in colors), default=0)
    g = max((c[1] for c in colors), default=0)
    b = max((c[2] for c in colors), default=0)
    return (r, g, b)



print("hello")

