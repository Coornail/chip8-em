import time
import sys
import random


class chip8:
    memory = [0] * 4096
    display = [0] * 64 * 32
    pc = 0x200
    i = 0
    stack = []
    delay_timer = 0
    sound_timer = 0
    registers = [0] * 16

    def __init__(self, rom):
        self.load_rom(rom)

    def load_rom(self, rom):
        with open(rom, 'rb') as f:
            rm = f.read()
            for i in range(len(rm)):
                self.memory[512+i] = rm[i]

    def run(self):
        while True:
            self.step()

    def step(self):
        opcode = self.decode()

        if opcode == 0x0000:
            print("Warning: 0x0000 instruction")
            pass
        elif opcode == 0x00E0:
            self.display = [0] * 64 * 32
            self.paint()
        elif opcode == 0x00EE:
            self.pc = self.stack.pop()
        elif opcode & 0xF000 == 0x1000:
            self.pc = opcode & 0x0FFF
        elif opcode & 0xF000 == 0x2000:
            self.stack.append(self.pc)
            self.pc = opcode & 0x0FFF
        elif opcode & 0xF000 == 0x3000:
            if opcode & 0x00FF == self.registers[(opcode & 0x0F00) >> 8]:
                self.pc += 2
        elif opcode & 0xF000 == 0x4000:
            if opcode & 0x00FF != self.registers[(opcode & 0x0F00) >> 8]:
                self.pc += 2
        elif opcode & 0xF00F == 0x5000:
            if self.registers[(opcode & 0x0F00) >> 8] == self.registers[(opcode & 0x00F0) >> 4]:
                self.pc += 2
        elif opcode & 0xF000 == 0x6000:
            self.registers[(opcode & 0x0F00) >> 8] = opcode & 0x00FF
        elif opcode & 0xF000 == 0x7000:
            target = (opcode & 0x0F00) >> 8
            self.registers[target] += opcode & 0x00FF
            if self.registers[target] > 255:
                self.registers[target] = self.registers[target] - 256
        elif opcode & 0xF00F == 0x8000:
            self.registers[(opcode & 0x0F00) >>
                           8] = self.registers[(opcode & 0x00F0) >> 4]
        elif opcode & 0xF00F == 0x8001:
            self.registers[(opcode & 0x0F00) >>
                           8] |= self.registers[(opcode & 0x00F0) >> 4]
        elif opcode & 0xF00F == 0x8002:
            self.registers[(opcode & 0x0F00) >>
                           8] &= self.registers[(opcode & 0x00F0) >> 4]
        elif opcode & 0xF00F == 0x8003:
            self.registers[(opcode & 0x0F00) >>
                           8] ^= self.registers[(opcode & 0x00F0) >> 4]
        elif opcode & 0xF00F == 0x8004:
            sum = self.registers[(opcode & 0x0F00) >> 8] + \
                self.registers[(opcode & 0x00F0) >> 4]
            if sum > 1 << 8:
                self.registers[0xF] = 1
                sum %= 1 << 8
            else:
                self.registers[0xF] = 0
            self.registers[(opcode & 0x0F00) >> 8] = sum
        elif opcode & 0xF00F == 0x8005:
            sum = self.registers[(opcode & 0x0F00) >> 8] - \
                self.registers[(opcode & 0x00F0) >> 4]
            if sum < 0:
                self.registers[0xF] = 0
            else:
                self.registers[0xF] = 1
            self.registers[(opcode & 0x0F00) >> 8] = sum
        elif opcode & 0xF00F == 0x8006:
            least_significant = self.registers[(opcode & 0x0F00) >> 8] & 0x000F
            self.registers[(opcode & 0x0F00) >> 8] = self.registers[(
                opcode & 0x00F0) >> 4] >> 1
            self.registers[0xF] = least_significant
        elif opcode & 0xF00F == 0x800E:
            most_significant = self.registers[(opcode & 0x0F00) >> 8] & 0xF000
            self.registers[(opcode & 0x0F00) >> 8] = self.registers[(
                opcode & 0x00F0) >> 4] << 1
            self.registers[0xF] = most_significant
        elif opcode & 0xF00F == 0x9000:
            if self.registers[(opcode & 0x0F00) >> 8] != self.registers[(opcode & 0x00F0) >> 4]:
                self.pc += 2
        elif opcode & 0xF000 == 0xA000:
            self.i = opcode & 0x0FFF
        elif opcode & 0xF000 == 0xB000:
            self.pc = opcode & 0x0FFF + self.registers[0x0]
        elif opcode & 0xF000 == 0xC000:
            self.registers[0x0F00 >> 8] = random.randint(
                0, 255) & (opcode & 0x00FF)
        elif opcode & 0xF000 == 0xD000:
            x = self.registers[(opcode & 0x0F00) >> 8]
            y = self.registers[(opcode & 0x00F0) >> 4]
            n = opcode & 0x000F

            self.registers[0xF] = 0
            for y_line in range(0, n):
                pixel = self.memory[self.i + y_line]
                for x_line in range(0, 8):
                    if (pixel & (0x80 >> x_line)) != 0:
                        if self.display[x + x_line + ((y + y_line) * 64)] == 1:
                            self.registers[0xF] = 1
                        self.display[x + x_line + ((y + y_line) * 64)] ^= 1

            self.paint()

        elif opcode & 0xF0FF == 0xF01E:
            self.i += self.registers[opcode & 0x0F00 >> 8]
        elif opcode & 0xF0FF == 0xF055:
            for i in range(self.registers[0x0F00 >> 8]):
                self.memory[self.i + i] = self.registers[i]
        elif opcode & 0xF0FF == 0xF065:
            for i in range(self.registers[0x0F00 >> 8]):
                self.registers[i] = self.i + i
            self.i += 16 + 1
        else:
            print("Unknown opcode: " + self.asm())
            # exit()

        self.pc = (self.pc + 2 % 4096)

    def decode(self):
        return self.memory[self.pc] << 8 | self.memory[self.pc + 1]

    def __str__(self) -> str:
        return 'inst: {0} [pc: {1}]\nmemory: {2}'.format(self.asm(), self.pc, self.memory)

    def asm(self):
        return "[" + hex(self.memory[self.pc]) + " " + hex(self.memory[self.pc+1]) + "]"

    def paint(self):
        # Clear screen
        print(chr(27) + "[2J")

        print(" " + "_"*64)
        for y in range(0, 32):
            print('|', end='')
            for x in range(0, 64):
                print(' ' if self.display[y * 64 + x] == 0 else '█', end='')
            print('|')
        print(" " + "_"*64)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: main.py <rom>")
        sys.exit(1)

    c8 = chip8(sys.argv[1])
    while True:
        c8.step()
        time.sleep(0.05)
