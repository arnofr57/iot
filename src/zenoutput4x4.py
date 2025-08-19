import random
from src import ws2812b
from src import LEDBlock2 as LEDBlock

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
 
    def full(self, patern, color1, color2):
        #patern = "XXAXAAAXXXAXXAXX"
        print("full patern " + patern + str(color1) + str(color2))
        res = []
        block = 0
        if color1=="RAND":
            color1 = random.choice(COLORS_RGB)
        if color2:
            if color2 == "RAND":
                color2 = random.choice(COLORS_RGB)
                print("color2")
                for car in patern:
                    if car == "A":
                        a = [self.rvb_to_dec(color1)] * self.blocks[block].size
                    elif car == "B":
                        a = [self.rvb_to_dec(color2)] * self.blocks[block].size
                    elif car == "X":
                        a = [0] * self.blocks[block].size
                    res = res + a  
                    block += 1
            else:
                for car in patern:
                    if car == "A":
                        a = [self.rvb_to_dec(color1)] * self.blocks[block].size
                    elif car == "B":
                        a = [self.rvb_to_dec(color2)] * self.blocks[block].size
                    elif car == "X":
                        a = [0] * self.blocks[block].size
                    res = res + a  
                    block += 1
            print(res)
            
        return res;
        
    def show(self):
        self.leds.show()