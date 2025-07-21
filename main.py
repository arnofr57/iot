from machine import Pin
import uasyncio as asyncio
import array
import random
from src import LEDBlock2 as LEDBlock
COLORS_RGB = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255),
    #(255, 255, 255), (255, 0, 255),
    #(255, 255, 0), (0, 255, 255),
]

COLORS = [16711680, 65280, 255, ] #16777215, 16711935, 16776960, 65535]
PATERN = ["ABBABAABBAABABBA",
          "AAAAABBAABBAAAAA",
          "BBBBBAABBAABBBBB",
          "ABBAABBAABBAABBA",
          "AAAABBBBAAAABBBB",
          "AXXAXXXXXXXXAXXA",
          "XXXXXAAXXAAXXXXX"]

PATERN_TEST_AB = ["AB"]
          

import ws2812b    
class ZenOutput:
    def __init__(self, name):
        self.name = name
        #print("ZenOutput créé avec le nom :", name)
    def rvb_to_dec(self, color):
        return (color[0] << 16) + (color[1] << 8) + color[2]


class ZenOutput4x4(ZenOutput):
    def __init__(self, LED_PIN = 28):
        self.blocks = []
        current_index = 0
        self.LED_PIN = LED_PIN
        self.name = "4x4"
        self.composition = [LEDBlock.Block8LED, LEDBlock.Block8LED, LEDBlock.Block8LED, LEDBlock.Block8LED,
                        LEDBlock.Block8LED, LEDBlock.BlockMiroirInfini, LEDBlock.Block8LED, LEDBlock.Block8LED,
                        LEDBlock.Block8LED, LEDBlock.Block8LED, LEDBlock.Block8LED, LEDBlock.Block8LED,
                        LEDBlock.Block8LED, LEDBlock.Block8LED, LEDBlock.Block8LED, LEDBlock.Block8LED,]
        
        #self.composition = [LEDBlock.Block8LED, LEDBlock.Block8LED]
        for cls in self.composition:
            block = cls(current_index)
            self.blocks.append(block)
            current_index += block.size
            if isinstance(block, LEDBlock.BlockMiroirInfini):
                miroir = block
        # initialisation du buffer & LEDs
        self.NB_LEDS = sum(b.size for b in self.blocks)
        #print(self.NB_LEDS)
        buffer = [(0,0,0)] * self.NB_LEDS
        self.leds = ws2812b.ws2812b(self.NB_LEDS, 0, LED_PIN)
        self.leds.fill(0,0,0)
        self.show()
 
    def full(self, patern = "ABBABAABBAABABBA", color1 =(255,255,255), color2=(255,255,255)):
        print("full patern " + patern + str(color1) + str(color2))
        res = []
        block = 0
        for car in patern:
            if car == "A":
                a = [self.rvb_to_dec(color1)] * self.blocks[block].size
            elif car == "B":
                a = [self.rvb_to_dec(color2)] * self.blocks[block].size
            elif car == "X":
                a = [0] * self.blocks[block].size
            res = res + a  
            block += 1
        return res;
        
    def show(self):
        self.leds.show()

class ZenAutomate:
    def __init__(self, input_obj, time_step=1):
        self.input_obj = input_obj
        self.time_step = time_step
        black = [0] * self.input_obj.NB_LEDS
        self.buffer_scenes = black[:]
        self.buffer_scintillement = black[:]
        self.buffer_mirroirRun = black[:]
        self.buffer = black[:]
        
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

    def set_all(self, color):
        res = []
        #print(color)
        b = self.input_obj.leds.pixels
        #print(len(b))
        for i in range(0,len(b)):
            a = self.input_obj.rvb_to_dec(color)
            #print(a)
            res.append(a)
        return res
    
    def mixpixcoef(self, color_a, color_b, coef):
        # Extraire RGB de color_a
        a_r = (color_a >> 16) & 0xFF
        a_g = (color_a >> 8) & 0xFF
        a_b = color_a & 0xFF

        # Extraire RGB de color_b
        b_r = (color_b >> 16) & 0xFF
        b_g = (color_b >> 8) & 0xFF
        b_b = color_b & 0xFF

        # Mélange linéaire des composantes (interpolation)
        res_r = int(a_r * coef + b_r * (1 - coef))
        res_g = int(a_g * coef + b_g * (1 - coef))
        res_b = int(a_b * coef + b_b * (1 - coef))

        # Recomposer en couleur 24 bits
        mixed_color = (res_r << 16) + (res_g << 8) + res_b
        return mixed_color


    def mixcoef(self, a, b, coef):
        size = self.input_obj.NB_LEDS
        if len(a) != size:
            a = [0] * size
        if len(b) != size:
            b = [0] * size

        return [self.mixpixcoef(ca, cb, coef) for ca, cb in zip(a, b)]
    

    async def run(self):
        print("ZenAutomate lancé")
        #while True:
        print(f"[{self.input_obj.name}] cycle...prg ")
        asyncio.create_task(automate_main.scenes(20))
        asyncio.create_task(automate_main.scintillement(60))
        asyncio.create_task(automate_main.mirroirRun(1))
        asyncio.create_task(automate_main.show(0.1))
        
        #await asyncio.sleep(self.time_step)
            
    async def show(self, time_step = 1):
        print("SHOW START")
        while True:
            #print("Compute Buffer" + str(self.buffer))
            self.buffer = self.mix(self.buffer_mirroirRun ,self.force(self.buffer_scenes,self.buffer_scintillement)) 
            #print("SHOW" + str(self.buffer))
            self.input_obj.leds.pixels = array.array("I", self.buffer)
            self.input_obj.show()
            await asyncio.sleep(time_step)    

    def mixscenecoef(self, res_initial, res_final,t):
        res = []
        if t == 0 :
            res = res_final
        elif t == 1:
            res = res_initial
        else:   
            for color_a, color_b in zip(res_initial, res_final):
                res_calcul = self.mixpixcoef(color_a, color_b,t)
                res.append(res_calcul)
                    #print("compute" + str(len(res)) + " " +str(res))
                #print(res)
        return res
                

    async def scenes(self, time_step = 1):
        print("prg1 ZenAutomate lancé")
        while True:
            print(f"[{self.input_obj.name}] cycle     prg i")
            res_initial = list(self.input_obj.leds.pixels)
            print("initial")
            print(res_initial)
            print("final")
            res_final = self.input_obj.full(random.choice(PATERN), random.choice(COLORS_RGB), random.choice(COLORS_RGB))
            #res_final = self.input_obj.full(random.choice(PATERN),(0,0,255), (255,0,0))
            #res_final = self.input_obj.full(random.choice(PATERN_TEST_AB),random.choice(COLORS_RGB), random.choice(COLORS_RGB))

            print(res_final)
            
            steps = 10
            print("deburt_fade")
            for step in range(steps+1):
                t = step / steps 
                #print("t " + str(t))
                res = []
                res = self.mixscenecoef(res_initial, res_final,1-t)
                #print(res)
                self.buffer_scenes =  res
                await asyncio.sleep(0.1)
            
            print("on wait 3s")
            await asyncio.sleep(3)
          
            steps = 50
            res_initial = res
            res_final = self.set_all((0,0,0))
            print("on descend_le fade")
            for step in range(steps+1):
                t = step / steps
                # print("t " + str(t))
                res = []
                res = self.mixscenecoef(res_initial, res_final,1-t)
                #print(res)
                self.buffer_scenes =  res
                await asyncio.sleep(0.1)
            print("on wait 3s")
            
            
            self.buffer_scenes = self.set_all((0,0,0))
            await asyncio.sleep(8)
            
            #res = self.input_obj.full("XXXXXAXXXXXXXXXX", (255,255,255), random.choice(COLORS_RGB))
            
        
    
    async def scintillement(self, time_step = 1):
        print("prg ZenAutomate scintillement lancé")
        while True:
            res = [] #self.input_obj.full(random.choice(PATERN), random.choice(COLORS_RGB), random.choice(COLORS_RGB))
            #res = self.input_obj.full("XXXXXAXXXXXXXXXX", (255,255,255), random.choice(COLORS_RGB))
            self.buffer_scintillement =  res
            print(f"[{self.input_obj.name}] cycle  TODO   prg scintillement")    
            await asyncio.sleep(time_step)
    
    async def mirroirRun(self, time_step = 1, color = (-1,-1,-1)):
        print("prg ZenAutomate mirroirRun lancé")
        mysize = 9
        
        while True:
            res = [] #self.input_obj.full(random.choice(PATERN), random.choice(COLORS_RGB), random.choice(COLORS_RGB))
            #res = self.input_obj.full("XXXXXAXXXXXXXXXX", (255,255,255), random.choice(COLORS_RGB))
            self.buffer_mirroirRun =  res
            #if color == (-1,-1,-1):
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
            print(f"[{self.input_obj.name}] cycle end prg mirroirrun ")    

# Création des objets
arnaudmeuble = ZenOutput4x4()
automate_main = ZenAutomate(arnaudmeuble)

# Lancement de la boucle principale
async def main():
    asyncio.create_task(automate_main.run())
    await asyncio.sleep(3660)
    #print("Fin du programme")

asyncio.run(main())
