import uasyncio as asyncio
import random
from machine import Pin
import ws2812b

NUM_LEDS = 12
DATA_PIN = 28

leds = ws2812b.ws2812b(NUM_LEDS, 0, DATA_PIN)

active_leds = set()  # LEDs actuellement allumées


def set_led(index, r, g, b):
    leds.set_pixel(index, r, g, b)
    leds.show()


def clear_led(index):
    leds.set_pixel(index, 0, 0, 0)
    leds.show()


async def fade_led(index, color, steps=20, up=True):
    for i in range(steps + 1):
        factor = i / steps if up else (1 - i / steps)
        r = int(color[0] * factor)
        g = int(color[1] * factor)
        b = int(color[2] * factor)
        set_led(index, r, g, b)
        await asyncio.sleep(0.02)  # vitesse du fondu


async def led_behavior(index):
    global active_leds
    await asyncio.sleep(random.uniform(3, 10))  # décalage initial

    while True:
        # RGB pur : chaque canal peut être 0 ou 255
        color = (
            random.randint(0, 1) * 255,
            random.randint(0, 1) * 255,
            random.randint(0, 1) * 255,
        )
        # Évite le noir pur (0,0,0)
        if color == (0, 0, 0):
            continue
        if color == (255, 255, 255):
            continue
        if len(active_leds) < 5: 
            await fade_led(index, color, up=True)
            active_leds.add(index)

            await asyncio.sleep(random.uniform(30, 60))  # pause allumée

        if len(active_leds) > 1:
            
            await fade_led(index, color, up=False)
            active_leds.discard(index)
            await asyncio.sleep(random.uniform(10, 120))
        else:
            # Si c'est la dernière allumée, elle reste active un peu plus longtemps
            await asyncio.sleep(random.uniform(20, 20))


async def main():
    tasks = [led_behavior(i) for i in range(NUM_LEDS)]
    await asyncio.gather(*tasks)


asyncio.run(main())
