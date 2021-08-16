
class chip8:
    memory = [0] * 4096
    display = [0] * 64 * 32
    pc = 0
    i = 0
    stack = []
    delay_timer = 0
    sound_timer = 0
    registers = [0] * 16

    def __init__(self, rom):
        self.load_rom(rom)

    def load_rom(self, rom):
        with open(rom, 'rb') as f:
            self.memory = f.read()

    def run(self):
        while True:
            self.step()

    def step(self):
        self.asm()
        opcode, operands = self.decode()

        if opcode == 0x0010:
            self.pc = operands

        self.pc = (self.pc + 1 % 4096)

    def decode(self):
        nh = self.memory[self.pc] & 0x0F
        nl = self.memory[self.pc] >> 4 & 0x0F
        return (nh, nl)

    def __str__(self) -> str:
        return '[pc: {0}]'.format(self.pc)

    def asm(self):
        nh, nl = self.decode()
        print("[" + hex(nh) + " " + hex(nl) + "]")

    def paint(self):
        # Clear screen
        print(chr(27) + "[2J")

        for y in range(0, 32):
            print('|', end='')
            for x in range(0, 64):
                print(' ' if self.display[y * 64 + x] == 0 else '#', end='')
            print('|')


def main():
    c8 = chip8('roms/test_opcode.ch8')
    c8.step()
    c8.step()
    print(c8)
    pass


if __name__ == '__main__':
    main()
