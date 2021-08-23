import time
import sys
import random
import math
import curses


font_faces = [
    0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
    0x20, 0x60, 0x20, 0x20, 0x70,  # 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
    0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
    0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
    0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
    0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
    0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
    0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
    0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
    0xF0, 0x80, 0xF0, 0x80, 0x80   # F
]


class chip8:
    memory = [0] * 4096
    display = [0] * 64 * 32
    pc = 0x200
    i = 0
    stack = []
    delay_timer = 0
    sound_timer = 0
    registers = [0] * 16
    stdscr = None

    keymap = {
        49: 0, 50: 1, 51: 2, 52: 3,
        113: 4, 119: 5, 101: 6, 114: 7,
        97: 8, 115: 9, 100: 10, 102: 11,
        122: 12, 104: 13, 120: 14, 99: 15,
    }

    debug = []

    def __init__(self, rom):
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)

        self.main_window = self.stdscr.subwin(33, 65, 0, 0)
        self.main_window.nodelay(1)
        self.main_window.border(1)

        self.load_rom(rom)

    def load_rom(self, rom):
        with open(rom, 'rb') as f:
            rm = f.read()
            for i in range(len(rm)):
                self.memory[512+i] = rm[i]

        for i in range(len(font_faces)):
            self.memory[0x050 + i] = font_faces[i]

    def run(self):
        while True:
            self.step()

    def getX(self, opcode):
        return (opcode & 0x0F00) >> 8

    def getXXX(self, opcode):
        return opcode & 0x0FFF

    def getY(self, opcode):
        return (opcode & 0x00F0) >> 4

    def step(self):
        opcode = self.decode()

        if opcode == 0x0000:
            print("Warning: 0x0000 instruction")
            pass
        elif opcode == 0x00E0:
            """Clear the screen"""
            self.display = [0] * 64 * 32
            self.paint()
        elif opcode == 0x00EE:
            """Return from a subroutine"""
            self.pc = self.stack.pop()
        elif opcode & 0xF000 == 0x1000:
            """Jump to address NNN"""
            self.pc = self.getXXX(opcode) - 2
        elif opcode & 0xF000 == 0x2000:
            """Execute subroutine starting at address NNN"""
            self.stack.append(self.pc)
            self.pc = self.getXXX(opcode) - 2
        elif opcode & 0xF000 == 0x3000:
            """Skip the following instruction if the value of register VX equals NN"""
            if opcode & 0x00FF == self.registers[self.getX(opcode)]:
                self.pc += 2 & 0xFFF
        elif opcode & 0xF000 == 0x4000:
            """Skip the following instruction if the value of register VX is not equal to NN"""
            if opcode & 0x00FF != self.registers[self.getX(opcode)]:
                self.pc += 2 & 0xFFF
        elif opcode & 0xF00F == 0x5000:
            if self.registers[self.getX(opcode)] == self.registers[self.getY(opcode)]:
                self.pc += 2 & 0xFFF
        elif opcode & 0xF000 == 0x6000:
            self.registers[self.getX(opcode)] = opcode & 0x00FF
        elif opcode & 0xF000 == 0x7000:
            target = self.getX(opcode)
            self.registers[target] += opcode & 0x00FF
            if self.registers[target] > 255:
                self.registers[target] = self.registers[target] - 256
        elif opcode & 0xF00F == 0x8000:
            self.registers[self.getX(
                opcode)] = self.registers[self.getY(opcode)]
        elif opcode & 0xF00F == 0x8001:
            self.registers[self.getX(
                opcode)] |= self.registers[self.getY(opcode)]
        elif opcode & 0xF00F == 0x8002:
            self.registers[self.getX(
                opcode)] &= self.registers[self.getY(opcode)]
        elif opcode & 0xF00F == 0x8003:
            self.registers[self.getX(
                opcode)] ^= self.registers[self.getY(opcode)]
        elif opcode & 0xF00F == 0x8004:
            sum = self.registers[self.getX(
                opcode)] + self.registers[self.getY(opcode)]
            if sum > 1 << 8:
                self.registers[0xF] = 1
                sum %= 1 << 8
            else:
                self.registers[0xF] = 0
            self.registers[self.getX(opcode)] = sum
        elif opcode & 0xF00F == 0x8005:
            sum = self.registers[self.getX(
                opcode)] - self.registers[self.getY(opcode)]
            if sum < 0:
                self.registers[0xF] = 0
                sum = sum + 256
            else:
                self.registers[0xF] = 1
            self.registers[self.getX(opcode)] = sum
        elif opcode & 0xF00F == 0x8006:
            x = self.getX(opcode) & 0xFFFF
            self.registers[0xF] = self.registers[x] & 0x1
            self.registers[x] = self.registers[x] >> 1
        elif opcode & 0xF00F == 0x8007:
            sum = self.registers[self.getY(
                opcode)] - self.registers[self.getX(opcode)]
            if sum < 0:
                self.registers[0xF] = 0
            else:
                self.registers[0xF] = 1
            self.registers[self.getX(opcode)] = sum
            pass
        elif opcode & 0xF00F == 0x800E:
            x = self.getX(opcode)
            most_significant = self.registers[x] & 0x1000
            self.registers[x] = self.registers[x] << 1
            if self.registers[x] > 255:
                self.registers[x] -= 256
            self.registers[0xF] = most_significant
        elif opcode & 0xF00F == 0x9000:
            if self.registers[self.getX(opcode)] != self.registers[self.getY(opcode)]:
                self.pc += 2 & 0xFFF
        elif opcode & 0xF0FF == 0xF029:
            self.i = self.registers[self.getX(opcode)] * 5
        elif opcode & 0xF000 == 0xA000:
            self.i = opcode & 0x0FFF
        elif opcode & 0xF000 == 0xB000:
            self.pc = self.getXXX(opcode) + self.registers[0x0]
        elif opcode & 0xF000 == 0xC000:
            self.registers[self.getX(opcode)] = random.randint(
                0, 255) & (opcode & 0x00FF)
        elif opcode & 0xF000 == 0xD000:
            x = self.registers[self.getX(opcode)]
            y = self.registers[self.getY(opcode)]
            n = opcode & 0x000F

            self.registers[0xF] = 0
            for y_line in range(0, n):
                pixel = self.memory[self.i + y_line]
                for x_line in range(0, 8):
                    if (pixel & (0x80 >> x_line)) != 0:
                        pos = ((x + x_line) % 64) + \
                            ((y + y_line) * 64) % (64*32)
                        if self.display[pos] == 1:
                            self.registers[0xF] = 1
                        self.display[pos] ^= 1

            self.paint()
        elif opcode & 0xF0FF == 0xE0A1:
            ch = self.main_window.getch()
            if ch == -1 or ch not in self.keymap or self.registers[self.getX(opcode)] != self.keymap[ch]:
                self.pc += 2 & 0xFFF
        elif opcode & 0xF0FF == 0xF01E:
            self.i += self.registers[self.getX(opcode)]
        elif opcode & 0xF0FF == 0xF033:
            num = self.registers[self.getX(opcode)]
            self.memory[self.i] = math.floor(num / 100)
            self.memory[self.i + 1] = math.floor(num / 10) % 10
            self.memory[self.i + 2] = num % 10
        elif opcode & 0xF0FF == 0xF055:
            for i in range(self.getX(opcode) + 1):
                self.memory[self.i + i] = self.registers[i]
            self.i += self.getX(opcode) + 1
        elif opcode & 0xF0FF == 0xF065:
            for i in range(self.getX(opcode) + 1):
                self.registers[i] = self.memory[self.i + i]
            self.i += self.getX(opcode) + 1
        elif opcode & 0xF0FF == 0xF00A:
            while self.main_window.getch() == -1:
                pass
        else:
            self.debug.append("Unknown opcode: " + self.asm())

        self.pc += 2 & 0xFFF

    def decode(self):
        return self.memory[self.pc] << 8 | self.memory[self.pc + 1]

    def __str__(self) -> str:
        return 'inst: {0} [pc: {1}]\nmemory: {2}'.format(self.asm(), self.pc, self.memory)

    def asm(self):
        return "[" + hex(self.memory[self.pc]) + " " + hex(self.memory[self.pc+1]) + "]"

    def paint(self):
        self.main_window.clear()
        for y in range(0, 32):
            for x in range(0, 64):
                self.main_window.addch(
                    y, x, '█' if self.display[x + y * 64] else ' ')

        # Draw debug
        debug_window = self.stdscr.subwin(1, 65)

        debug_scroll = 0
        if len(self.debug) > 30:
            debug_scroll = len(self.debug) - 30
        for i in self.debug[debug_scroll:]:
            debug_window.addstr(i + "\n")

        # Draw registers
        registers_window = self.stdscr.subwin(32, 65)
        registers_window.border(0)
        for i in range(len(self.registers)):
            registers_window.addstr(
                str(i) + ":\t" + hex(self.registers[i]) + "\t" + str(self.registers[i]) + "\n")

        registers_window.addstr("i: " + str(self.i) + "\n")

        self.stdscr.refresh()
        time.sleep(1/60)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: main.py <rom>")
        sys.exit(1)

    c8 = chip8(sys.argv[1])
    while True:
        c8.step()
