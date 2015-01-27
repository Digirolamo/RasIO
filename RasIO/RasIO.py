import time, functools
import smbus

class PinControler(object):
    """Turns on and off pins connected through mcp23017 Chips.
    Add devices and you can set pins with pin numers.
    Converts to binary conveniently."""

    def __init__(self, output_bits=8, raspberry_pi_rev=2):
        self.bus = smbus.SMBus(raspberry_pi_rev - 1)
        self.pin_count = 0
        self.pin_to_binary_list = {}
        self.pin_to_index = {}
        self.pin_to_bus = {}
        self.mapped_pins = {}
        
    def setPin(self, pin_num, enable=True, update_device=True):
        """Turns a pin on or off based on the enable argument."""
        pin_num = self.__adjustPin(pin_num)
        binary_list = self.pin_to_binary_list[pin_num]
        index = self.pin_to_index[pin_num]
        binary_list[index] = unicode(int(enable))
        if update_device:
            self.__refreshPinBus(pin_num)

    def setPins(self, pin_num_list, enable):
        """Sets a list of pins to either a value, or a list of values.
        If enable is a list, it must have the same length as the pin_num_list."""
        pin_num_list = [self.__adjustPin(pin_num) for pin_num in pin_num_list]
        if isinstance(enable, bool):
            enable = [enable for e in pin_num_list]
        if len(enable) != len(pin_num_list):
            raise IndexError("enable list must be same length as pin_num_list")
        to_refresh_pins = []
        to_refresh_bus = []
        for num in range(len(enable)):
            pin_num, enable_value = pin_num_list[num], enable[num]
            self.setPin(pin_num, enable=enable_value, update_device=False)
            bus_write = self.pin_to_bus[pin_num]
            if bus_write not in to_refresh_bus:
                to_refresh_bus.append(bus_write)
                to_refresh_pins.append(pin_num)
        for pin in to_refresh_pins:
            self.__refreshPinBus(pin)
        
    def toggle(self, pin_num):
        """Toggles (turns off if on, on if off) a pin."""
        pin_num = self.__adjustPin(pin_num)
        binary_list = self.pin_to_binary_list[pin_num]
        index = self.pin_to_index[pin_num]
        enabled = bool(int(binary_list[index]))
        enable = enabled is False #logical opposite
        binary_list[index] = unicode(int(enable))
        self.__refreshPinBus(pin_num)
        
    def turnOff(self):
        """Sets all pins to an off state."""
        for pin_num in self.pin_to_bus:
            self.setPin(pin_num, enable=False, update_device=False) 
        for bus_write in set(self.pin_to_bus.values()):
            bus_write(0)

    def turnOn(self):
        """Sets all pins to an on state."""
        pins = [pin_num for pin_num in self.pin_to_bus.keys()]
        self.setPins(pins, True)
            
    def addChannels(self, device_address, io_address, olat_address, output_bits=8):
        """Adds an 8 channel bus with 8 pins."""
        self.bus.write_byte_data(device_address, io_address, 0)
        bus_write = functools.partial(self.bus.write_byte_data, device_address, olat_address)
        bus_write(0)
        binary_list = [u"0" for e in xrange(output_bits)]
        start = self.pin_count + 1
        for num, pin_num in enumerate(range(start, start + output_bits)):
            self.pin_to_bus[pin_num] = bus_write
            self.pin_to_binary_list[pin_num] = binary_list
            self.pin_to_index[pin_num] = -(num + 1)
            self.pin_count += 1

    def addMCP(self, address):
        """Adds a MCP23017 Device with all pins set as output"""
        IO_ADR_A, OUT_ADR_A = 0x00, 0x14
        IO_ADR_B, OUT_ADR_B = 0x01, 0x15
        self.addChannels(address, IO_ADR_A, OUT_ADR_A)
        self.addChannels(address, IO_ADR_B, OUT_ADR_B)

    def mapPinNum(self, actual_pin_num, mapping):
        """You can set a mapping for a pin sok
        When you call methods with a pin number it finds
        a different mapped pin."""
        self.mapped_pins[mapping] = actual_pin_num

    def clearMapping(self):
        """Removes all mapped pins."""
        self.mapped_pins.clear()

    def testAll(self):
        for num in range(len(self.pin_to_binary_list.keys())):
            num = num + 1
            self.setPin(num)
            time.sleep(.1)
            if num % 15 == 0:
                self.turnOff()
                time.sleep(1)
        self.turnOff()
        
    def __refreshPinBus(self, pin_num):
        """Writes the binnary to the bus"""
        bus_write = self.pin_to_bus[pin_num]
        binary_string = u"".join(bit for bit in self.pin_to_binary_list[pin_num])
        binary = int(binary_string, 2)
        bus_write(binary)

    def __adjustPin(self, pin_num):
        """Adjust the pin number if there is a mapping."""
        if pin_num in self.mapped_pins:
            pin_num = self.mapped_pins[pin_num]
        return pin_num
    
    def __del__(self):
        self.turnOff()
#Example
#control = PinControler()
#control.addMCP(0x20)
#control.addMCP(0x21)
#control.addMCP(0x22)
