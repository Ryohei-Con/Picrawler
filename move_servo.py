import gpiozero  # https://gpiozero.readthedocs.io/en/latest/installing.html
from gpiozero import OutputDevice, InputDevice, Button
from time import sleep
import subprocess

from smbus2 import SMBus
import math


# ピンのリセット
class Pin:
    _dict = {
        "MCU_RST": 5
    }
    def __init__(self, pin, mode="out"):
        if isinstance(pin, str):
            self.pin_num = self._dict[pin]
            self.pin_name = pin
        elif isinstance(pin, int):
            self.pin_num = pin
            self.pin_name = {i for i in self._dict if self._dict[i] == pin}
        else:
            print(f"pin should be in {self._dict.keys()}.\n But you put {pin}")

        self.setup(mode)

    def setup(self, mode):
        if mode == "out":
            self.gpio = OutputDevice(self.pin_num)
        elif mode == "in":
            self.gpio = InputDevice(self.pin_num)
        else:
            print(f"mode should be 'in' or 'out'. ")

    def value(self, value):
        if value == 1:
            self.gpio.on()
            return value
        elif value == 0:
            self.gpio.off()
            return value
        else:
            print(f"value should be 0 or 1.\n But you put {value}.")

    def on(self):
        return self.value(1)
    
    def off(self):
        return self.value(0)

def reset_mcu():
    reset_pin = Pin("MCU_RST")
    reset_pin.off()
    sleep(0.1)
    reset_pin.on()
    sleep(0.1)


# サーボを動かす
def run_command(cmd):
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    result = p.stdout.read().decode("utf-8")
    status = p.poll()
    return status, result


timer = [{"arr": 1} for _ in range(7)]

class I2C:
    RETRY = 5

    def __init__(self, address=None, bus=1):
        self._bus = bus
        self._smbus = SMBus(self._bus)
        # TODO: addressについての初期化
        if isinstance(address, str):
            self.address = address
        elif isinstance(address, list):
            connected_devices = self.scan()
            print(f"{connected_devices=}")
            for addr in address:
                if addr in connected_devices:
                    self.address = addr
                    break
            else:
                self.address = address[0]
    
    def scan(self):
        addresses = []
        cmd = f"i2cdetect -y {self._bus}"
        _, result = run_command(cmd)
        addresses_cands = result.split("\n")[1:]
        for _addrs in addresses_cands:
            if _addrs == "":
                continue
            tmp_addresses = _addrs.split(":")[1].strip().split(" ")
            for _addr in tmp_addresses:
                if _addr != "--":
                    addresses.append(int(_addr, 16))
        if not addresses:
            print("No device is connected. ")
        return addresses

    def write(self, data: list):
        if len(data) == 3:
            reg = data[0]
            write_data = (data[2] << 8) + data[1]
            self._write_word_data(reg, write_data)
            print(f"write_data: [0X{reg:02X}], [0X{write_data:02X}]")

    def _write_word_data(self, reg, write_data):
        self._smbus.write_word_data(self.address, reg, write_data)

class PWM(I2C):
    # レジスタのアドレス

    # channel register prefix
    REG_CHN = 0x20
    # Prescaler and Period register prefix
    REG_PSC = 0x40
    REG_PSC2 = 0x50
    REG_ARR = 0X44
    REG_ARR2 = 0x54
    
    # ラズパイハットのアドレス
    ADDR = [0x14, 0x15, 0x16]
    # クロック周波数
    CLOCK = 72000000.0

    def __init__(self, channel, address=None):
        if address is None:
            super().__init__(self.ADDR)
        else:
            super().__init__(address)

        if isinstance(channel, str):
            if channel.startswith(("p", "P")):
                channel = int(channel[1:])
            else:
                raise ValueError(f"channel must be in the form of P0 ~ P19 not {channel}")
        if isinstance(channel, int):
            if channel > 19 or channel < 0:
                raise ValueError(f"channel must be between 0 and 19 not {channel}")
        self.channel = channel
        
        if channel < 16:
            self.timer_index = int(channel / 4)
        elif channel == 16 or channel == 17:
            self.timer_index = 4
        elif channel == 18:
            self.timer_index = 5
        elif channel == 19:
            self.timer_index = 6
        self._pulse_width = 0
        self.freq(50)


    def freq(self, freq=None):
        if freq is None:
            return self._freq
        self._freq = int(freq)  
        result_pa = []
        result_acc = []
        st = int(math.sqrt(self.CLOCK / self._freq))
        st -= 5
        for psc in range(st, st+10):
            arr = int(self.CLOCK / self._freq / psc)
            result_pa.append([psc, arr])
            acc = abs(self._freq - self.CLOCK / psc / arr)
            result_acc.append(acc)

        i = result_acc.index(min(result_acc))
        psc = result_pa[i][0]
        arr = result_pa[i][1]
        self.prescaler(psc)
        self.period(arr)
    
    def prescaler(self, psc: float):
        """
        Set/get prescaler, leave blank to get prescaler
        """
        if psc is None:
            return self._prescaler
        else:
            self._prescaler = round(psc)
            self._freq = self.CLOCK / self._prescaler / timer[self.timer_index]["arr"]
            if self.timer_index < 4:
                reg = self.REG_PSC + self.timer_index
            else:
                reg = self.REG_PSC2 + self.timer_index - 4
            self._i2c_write(reg, self._prescaler - 1)

    def period(self, arr: float):
        global timer
        if arr is None:
            return timer[self.timer_index]["arr"]
        else:
            timer[self.timer_index]["arr"] = round(arr)
            self._freq = self.CLOCK / self._prescaler / timer[self.timer_index]["arr"]
            
            if self.timer_index < 4:
                reg = self.REG_ARR + self.timer_index
            else:
                reg = self.REG_ARR2 + self.timer_index - 4
            self._i2c_write(reg, timer[self.timer_index]["arr"])
        

    def pulse_width(self, pulse_width=None):
        if pulse_width is None:
            return self._pulse_width
        else:
            self._pulse_width = pulse_width
            reg = self.REG_CHN + self.channel
            self._i2c_write(reg, self._pulse_width)

    def _i2c_write(self, reg, value):
        value_h = value >> 8
        value_t = value & 0xff
        self.write([reg, value_h, value_t])


class Servo(PWM):
    # 単位はμs
    MAX_PW = 2500
    MIN_PW = 500
    
    # i2c通信に使う定数
    FREQ = 50
    PERIOD = 4095

    def __init__(self, channel, address=None):
        super().__init__(channel, address)
        self.period(self.PERIOD)
        prescaler = self.CLOCK / self.FREQ / self.PERIOD
        self.prescaler(prescaler)

    def angle(self, angle):
        if angle > 90:
            angle = 90
        elif angle < -90:
            angle = -90

        pulse_width_time = self.map_pwt(angle)
        self.pulse_width_time(pulse_width_time)
        
    def map_pwt(self, angle):
        '''
        一次関数の形でpulse width timeを計算する
        '''
        MIN_IN = -90
        MAX_IN = 90
        pwt = (angle - MIN_IN) * ((self.MAX_PW - self.MIN_PW) / (MAX_IN - MIN_IN)) + self.MIN_PW
        return pwt
    
    def pulse_width_time(self, pulse_width_time):
        if pulse_width_time > self.MAX_PW:
            pulse_width_time = self.MAX_PW
        elif pulse_width_time < self.MIN_PW:
            pulse_width_time = self.MIN_PW
        
        pulse_width_rate = pulse_width_time / 20000
        value = int(pulse_width_rate * self.PERIOD)
        print(f"{value=}")
        self.pulse_width(value)

def move_servo(channel):
    servo = Servo(channel)
    servo.angle(50)
    sleep(0.5)
    servo.angle(channel)
    sleep(0.5)


if __name__ == "__main__":
    reset_mcu()
    sleep(0.2)
    move_servo(3)
