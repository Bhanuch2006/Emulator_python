import pygame
import sys
MEMORY_SIZE = 4096
DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32
REGISTER_COUNT = 16
STACK_SIZE = 16
PROGRAM_START = 0x200
FONTSET_START = 0x000
FONTSET_SIZE = 80
CLOCK_SPEED = 500  
class Chip8:
    def __init__(self):
        self.memory = [0] * MEMORY_SIZE
        self.V = [0] * REGISTER_COUNT    
        self.I = 0         
        self.pc = PROGRAM_START 
        self.stack = [0] * STACK_SIZE    
        self.sp = 0                   
        self.delay_timer = 0        
        self.sound_timer = 0         
        self.display = [[0] * DISPLAY_WIDTH for _ in range(DISPLAY_HEIGHT)]  
        self.keys = [0] * 16            

        fontset = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,  
            0x20, 0x60, 0x20, 0x20, 0x70,  
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  
            0x90, 0x90, 0xF0, 0x10, 0x10,  
            0xF0, 0x80, 0xF0, 0x10, 0xF0,  
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  
            0xF0, 0x10, 0x20, 0x40, 0x40,  
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  
            0xF0, 0x90, 0xF0, 0x90, 0x90,  
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  
            0xF0, 0x80, 0x80, 0x80, 0xF0,  
            0xE0, 0x90, 0x90, 0x90, 0xE0,  
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  
            0xF0, 0x80, 0xF0, 0x80, 0x80   
        ]
        self.memory[FONTSET_START:FONTSET_START + FONTSET_SIZE] = fontset

    def load_rom(self, rom_path):
        with open(rom_path, "rb") as f:
            rom_data = f.read()
            for i, byte in enumerate(rom_data):
                self.memory[PROGRAM_START + i] = byte

    def fetch_opcode(self):
        opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
        self.pc += 2
        return opcode

    def execute_opcode(self, opcode):
        op = (opcode & 0xF000) >> 12
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        n = opcode & 0x000F
        nn = opcode & 0x00FF
        nnn = opcode & 0x0FFF

        if op == 0x0:
            if opcode == 0x00E0:  
                self.display = [[0] * DISPLAY_WIDTH for _ in range(DISPLAY_HEIGHT)]
            elif opcode == 0x00EE:  
                self.sp -= 1
                self.pc = self.stack[self.sp]
        elif op == 0x3: 
            if self.V[x] == nn:
                self.pc += 2
        elif op == 0x6:  
            self.V[x] = nn
        elif op == 0x7:  
            self.V[x] = (self.V[x] + nn) & 0xFF
        elif op == 0x8: 
            if n == 0x0:  
                self.V[x] = self.V[y]
            elif n == 0x1:
                self.V[x] |= self.V[y]
            elif n == 0x2:  
                self.V[x] &= self.V[y]
            elif n == 0x3:  
                self.V[x] ^= self.V[y]
            elif n == 0x4:  
                self.V[0xF] = 1 if self.V[x] + self.V[y] > 0xFF else 0
                self.V[x] = (self.V[x] + self.V[y]) & 0xFF
        elif op == 0x9:  
            if self.V[x] != self.V[y]:
                self.pc += 2
        elif op == 0xA:  
            self.I = nnn
        elif op == 0xB:  
            self.pc = nnn + self.V[0]
        elif op == 0xC:  
            self.V[x] = (pygame.time.get_ticks() % 256) & nn
        elif op == 0xD:  
            x_pos = self.V[x] % DISPLAY_WIDTH
            y_pos = self.V[y] % DISPLAY_HEIGHT
            self.V[0xF] = 0
            for row in range(n):
                sprite_byte = self.memory[self.I + row]
                for col in range(8):
                    if (sprite_byte & (0x80 >> col)) != 0:
                        if self.display[(y_pos + row) % DISPLAY_HEIGHT][(x_pos + col) % DISPLAY_WIDTH] == 1:
                            self.V[0xF] = 1
                        self.display[(y_pos + row) % DISPLAY_HEIGHT][(x_pos + col) % DISPLAY_WIDTH] ^= 1
        elif op == 0xE:  
            if nn == 0x9E: 
                if self.keys[self.V[x]]:
                    self.pc += 2
            elif nn == 0xA1:  
                if not self.keys[self.V[x]]:
                    self.pc += 2
        elif op == 0xF:  
            if nn == 0x07:  
                self.V[x] = self.delay_timer
            elif nn == 0x0A:
                key_pressed = False
                while not key_pressed:
                    for event in pygame.event.get():
                        if event.type == pygame.KEYDOWN:
                            for i, key in enumerate(self.keys):
                                if event.key == key:
                                    self.V[x] = i
                                    key_pressed = True
            elif nn == 0x15:  
                self.delay_timer = self.V[x]
            elif nn == 0x18:  
                self.sound_timer = self.V[x]
            elif nn == 0x1E:  
                self.I += self.V[x]
            elif nn == 0x29:  
                self.I = FONTSET_START + (self.V[x] * 5)
            elif nn == 0x33: 
                self.memory[self.I] = self.V[x] // 100
                self.memory[self.I + 1] = (self.V[x] % 100) // 10
                self.memory[self.I + 2] = self.V[x] % 10
            elif nn == 0x55: 
                for i in range(x + 1):
                    self.memory[self.I + i] = self.V[i]
            elif nn == 0x65: 
                for i in range(x + 1):
                    self.V[i] = self.memory[self.I + i]

    def cycle(self):
        opcode = self.fetch_opcode()
        self.execute_opcode(opcode)
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1

pygame.init()
screen = pygame.display.set_mode((DISPLAY_WIDTH * 10, DISPLAY_HEIGHT * 10))  
clock = pygame.time.Clock()

chip8 = Chip8()
chip8.load_rom("Pong.ch8") 

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    chip8.cycle()
    screen.fill((0, 0, 0))
    for y in range(DISPLAY_HEIGHT):
        for x in range(DISPLAY_WIDTH):
            if chip8.display[y][x]:
                pygame.draw.rect(screen, (255, 255, 255), (x * 10, y * 10, 10, 10))

    pygame.display.flip()
    clock.tick(CLOCK_SPEED)  