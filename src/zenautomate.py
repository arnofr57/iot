from machine import Pin
import array
import random
import uasyncio as asyncio
COLORS_RGB = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255),
    (255, 255, 255), (255, 0, 255),
    (255, 255, 0), (0, 255, 255),
] 

COLORS = [16711680, 65280, 255, 16777215, 16711935, 16776960, 65535]

PATERN = ["ABBABAABBAABABBA",
          "AAAAABBAABBAAAAA",
          "BBBBBAABBAABBBBB",
          "ABBAABBAABBAABBA",
          "AAAABBBBAAAABBBB",
          "AXXAXXXXXXXXAXXA",
          "XXXXXAAXXAAXXXXX",
          "XXAXAAAXXXAXXAXX"]

class ZenAutomate:
    def __init__(self, input_obj, time_step=1):
        self.input_obj = input_obj
        self.time_step = time_step
        black = [0] * self.input_obj.NB_LEDS
        self.buffer_scenes = black[:]
        self.buffer_scintillement = black[:]
        self.buffer_mirroirRun = black[:]
        self.buffer = black[:]
        self.buffer_start_scenes = black[:]
        self.pin_running_alone = Pin(13, Pin.IN, Pin.PULL_UP)
        self.pin_starting = Pin(12, Pin.IN, Pin.PULL_UP)
        self.pin_mirroir = Pin(11, Pin.IN, Pin.PULL_UP)
      
    def rvb_to_dec(color):
        return (color[0] << 16) + (color[1] << 8) + color[2]
        
    def force(self, a,b):
        return a if any(c != 0 for c in a) else b

    def mix(self, a, b):
        # Vérifie que les deux buffers ont la bonne taille
        size = self.input_obj.NB_LEDS
        if len(a) != size:
            a = [0] * size
        if len(b) != size:
            b = [0] * size

        res = []
        for color_a, color_b in zip(a, b):
            # Extraire les composantes RGB
            a_r = (color_a >> 16) & 0xFF
            a_g = (color_a >> 8) & 0xFF
            a_b = color_a & 0xFF

            b_r = (color_b >> 16) & 0xFF
            b_g = (color_b >> 8) & 0xFF
            b_b = color_b & 0xFF

            # Mélange RGB (valeurs max)
            res_r = max(a_r, b_r)
            res_g = max(a_g, b_g)
            res_b = max(a_b, b_b)

            # Recompose en valeur décimale
            mixed_color = (res_r << 16) + (res_g << 8) + res_b
            res.append(mixed_color)
        return res


            
    async def fadeblock(self, block, color_initial, color_final,steps, duration):
        mytime = duration / steps
        for step in range(steps+1):
            t = 1 - step / steps
            color_compute = self.mixpixcoef(color_initial, color_final,t)    
            #print(str(t) + " " + str(color_compute))    
            self.buffer_scintillement[block.indices[0]:block.indices[0] + block.size] = [color_compute]*block.size
            await asyncio.sleep(mytime)

    async def demo(self, buffer_scenes):
        print("prg demo ZenAutomate lancé")
        while True:
            buffer_scenes[:] = self.input_obj.set_all((0,0,0))
            color1 = random.choice(COLORS_RGB)
            #color2 = random.choice(COLORS_RGB)
            await self.input_obj.prg_4x4_sympa(color1 = "RAND", color2=(0,0,0), step_on=100, duration_on = 20, buffer_scenes=buffer_scenes, delay=5)
    
    async def scintillementBlock(self):
        while True:
            trouve = False
            while not(trouve):
                block = random.choice(self.input_obj.blocks)
                trouve = not(block.active_scene)
            block.active_scene = True
            color = random.choice(COLORS_RGB)
            print("no color")
             #color=
            step_on = 20
            duration_on = random.uniform(0, 3)
            on = random.uniform(1, 20)
            step_off = 40
            duration_off=random.uniform(1, 10)
            off=0
            
            
            await self.fadeblock(block,0, rvb_to_dec(color),step_on,duration_on)
            await asyncio.sleep(on)
            await self.fadeblock(block, rvb_to_dec(color), 0,step_off,duration_off)
            await asyncio.sleep(off)
            block.active_scene = False
    
    async def random_scintillement(self):
        while True:
            color = random.choice(COLORS_RGB)
            await self.scintillementBlock()
    
    async def mirroirRun(self, time_step = 1, color = (-1,-1,-1)):
        print("prg ZenAutomate mirroirRun lancé")
        mysize = 9
        while True:
            res = []
            self.buffer_mirroirRun =  res
            color = random.choice(COLORS)
            for i in range(mysize):
                frame = [0]*mysize*4
                frame[i] = color
                frame[18-i-1] = color
                frame[18+i] = color
                frame[36-i-1] = color
                self.buffer_mirroirRun = [0] * 40 + frame + [0] * 80
                await asyncio.sleep(time_step)
            
            await asyncio.sleep(time_step)

    async def show(self, time_step = 1):
        print("SHOW START")
        while True:
            self.buffer[:] = self.mix(self.buffer_start_scenes,self.mix(self.buffer_mirroirRun ,self.force(self.buffer_scenes,self.buffer_scintillement)))
            # print("Compute Buffer" + str(self.buffer))
            self.input_obj.leds.pixels = array.array("I", self.buffer)
            self.input_obj.show()
            await asyncio.sleep(time_step)
            

    async def scene_controller(self):
        """
        Gère les scènes dynamiquement selon les états GPIO
        """
        active_tasks = {}

        while True:
            # Nettoyage des tâches terminées
            
            self.running_alone = self.starting = self.mirroir = True
            self.running_alone = False
            to_remove = [key for key, task in active_tasks.items() if task.done()]
            for key in to_remove:
                del active_tasks[key]

            # running_alone
            if self.running_alone and "random_scint" not in active_tasks:
                task = asyncio.create_task(self.random_scintillement())
                active_tasks["random_scint"] = task

            # starting
            if self.starting and "demo" not in active_tasks:
                task = asyncio.create_task(self.demo(
                    self.buffer_start_scenes))
                active_tasks["demo"] = task

            # mirroir
            if self.mirroir and "mirroir" not in active_tasks:
                task = asyncio.create_task(self.mirroirRun(1))
                active_tasks["mirroir"] = task

            await asyncio.sleep(0.2)


    async def monitor_switches(self, delay_ms=100):
        """
        Met à jour les variables selon les GPIO (toutes les `delay_ms`)
        """
        while True:
            self.running_alone = self.pin_running_alone.value() == 0
            #print(self.pin_running_alone.value())
            self.starting = self.pin_starting.value() == 0
            self.mirroir = self.pin_mirroir.value() == 0
            await asyncio.sleep_ms(delay_ms)


    async def run(self):
        print("ZenAutomate lancé")
        print(f"[{self.input_obj.name}] cycle...prg run()")
        # Lancer la surveillance des GPIO
        asyncio.create_task(self.monitor_switches())
        tasks = []
        # Tâches dynamiques réactives
        tasks.append(asyncio.create_task(self.scene_controller()))
        tasks.append(asyncio.create_task(self.show(0.05)))
        await asyncio.gather(*tasks)