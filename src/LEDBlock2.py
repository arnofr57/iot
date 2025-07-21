import uasyncio as asyncio


# === Classe de base LEDBlock ===
class LEDBlock:
    def __init__(self, indices):
        self.indices = indices
        self.size = len(indices)

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




