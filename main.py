import time

class chip8:
    memory = [0] * 4096
    display = [0] * 64 * 32
    pc = 512
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

        hex_opcode = hex(opcode)

        if opcode == 0x0000:
            pass
        elif opcode == 0x00E0:
            self.display = [0] * 64 * 32
            self.paint()
        elif hex_opcode[2] == 'a':  # aXXX
            self.i = opcode & 0x0FFF
        elif hex_opcode[2] == '6':  # 6XXX
            self.registers[(opcode & 0x0F00) >> 8] = opcode & 0x00FF
        elif hex_opcode[2] == 'd':  # DXYN
            x = self.registers[(opcode & 0x0F00) >> 8]
            y = self.registers[(opcode & 0x00F0) >> 4]
            n = opcode & 0x000F
            
            self.registers[0xF] = 0
            for y_line in range(0, n):
                pixel = self.memory[self.i + y_line]
                for x_line in range(0, 8):
                    if (pixel & (0x80 >> x_line)) != 0:
                        if self.display[(x + x_line + (y + y_line * 64))] == 1:
                            self.registers[0xF] = 1
                        self.display[(x + x_line + (y + y_line * 64))] ^= 1

            self.paint()

            return
        else:
            print("Unknown opcode: " + self.asm())

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


def main():
    c8 = chip8('roms/IBM Logo.ch8')
    while True:
        c8.step()
        time.sleep(0.1)


if __name__ == '__main__':
    main()
