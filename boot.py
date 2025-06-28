import uasyncio as asyncio
import random
import ws2812b


# Configuration générale
NUM_LEDS = 40
PIN_NUM = 28  # GPIO0
leds = ws2812b.ws2812b(NUM_LEDS, 0, PIN_NUM)
NUM_BLOCK = 5
# Blocs de 8 LEDs
BLOCK_SIZE = 8
BLOCKS = [list(range(i * BLOCK_SIZE, (i + 1) * BLOCK_SIZE)) for i in range(5)]

# Couleurs primaires
COLORS = [
    (255, 0, 0),   # Rouge
    (0, 255, 0),   # Vert
    (0, 0, 255),
    (255, 255, 255),
    (255, 0, 255),
    (255, 255, 0),
    (0, 255, 255), 
]

# Suivi des blocs actifs
active_blocks = set()

def set_block_color(block_id, color):
    r, g, b = color
    color_value = (g << 16) | (r << 8) | b  # Format GRB pour WS2812
    for i in BLOCKS[block_id]:
        leds.pixels[i] = color_value
    leds.show()


# Fade in/out progressif
async def fade_block(block_id, color, fade_in=True, steps=30, delay=0.05):
    for step in range(steps + 1):
        t = step / steps if fade_in else (1 - step / steps)
        r = int(color[0] * t)
        g = int(color[1] * t)
        b = int(color[2] * t)
        set_block_color(block_id, (r, g, b))
        await asyncio.sleep(delay)

# Comportement d'un bloc
async def block_task(block_id):
    global active_blocks
    while True:
        # Attendre qu'on puisse activer ce bloc
        while len(active_blocks) >= 2:
            await asyncio.sleep(0.5)

        # Activation
        active_blocks.add(block_id)
        color = random.choice(COLORS)
        on_time = random.uniform(5, 30)
        off_time = random.uniform(5, 30)

        # Allumage progressif
        await fade_block(block_id, color, fade_in=True)

        # Temps allumé
        await asyncio.sleep(on_time)

        # Extinction progressive
        await fade_block(block_id, color, fade_in=False)

        # Désactivation
        active_blocks.remove(block_id)

        # Temps éteint
        await asyncio.sleep(off_time)

# Boucle principale
async def main():
    tasks = [asyncio.create_task(block_task(i)) for i in range(5)]
    await asyncio.gather(*tasks)

# Lancement du programme
asyncio.run(main())
