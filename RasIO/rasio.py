"""A module to help add Raspberry Pi IO expander chips.

Examples:
    >>> from rasio import PinControler
    >>> control = PinControler()
    >>> control.add_mcp(0x20)
    >>> control.add_mcp(0x21)
    >>> control.add_mcp(0x22)

"""
from functools import partial
import time
import smbus

class PinControler(object):
    """Turns on and off pins connected through mcp23017 Chips.
    Add devices and you can set pins with pin numbers.
    Converts to binary conveniently."""

    def __init__(self, output_bits=8, raspberry_pi_rev=2):
        self.bus = smbus.SMBus(raspberry_pi_rev - 1)
        self.pin_count = 0
        self.pin_to_binary_list = {}
        self.pin_to_index = {}
        self.pin_to_bus = {}
        self.mapped_pins = {}

    def set_pin(self, pin_num, enable=True, update_device=True):
        """Turns a pin on or off based on the enable argument."""
        pin_num = self.__adjust_pin(pin_num)
        binary_list = self.pin_to_binary_list[pin_num]
        index = self.pin_to_index[pin_num]
        binary_list[index] = unicode(int(enable))
        if update_device:
            self.__refresh_pin_bus(pin_num)

    def set_pins(self, pin_num_list, enable):
        """Sets a list of pins to either a value, or a list of values.
        If enable is a list, it must have the same length as the pin_num_list."""
        pin_num_list = [self.__adjust_pin(pin_num) for pin_num in pin_num_list]
        if isinstance(enable, bool):
            enable = [enable for e in pin_num_list]
        if len(enable) != len(pin_num_list):
            raise IndexError("enable list must be same length as pin_num_list")
        to_refresh_pins = []
        to_refresh_bus = []
        for idx, enable_value in enumerate(enable):
            pin_num = pin_num_list[idx]
            self.set_pin(pin_num, enable=enable_value, update_device=False)
            bus_write = self.pin_to_bus[pin_num]
            if bus_write not in to_refresh_bus:
                to_refresh_bus.append(bus_write)
                to_refresh_pins.append(pin_num)
        for pin in to_refresh_pins:
            self.__refresh_pin_bus(pin)

    def toggle(self, pin_num):
        """Toggles (turns off if on, on if off) a pin."""
        pin_num = self.__adjust_pin(pin_num)
        binary_list = self.pin_to_binary_list[pin_num]
        index = self.pin_to_index[pin_num]
        enabled = bool(int(binary_list[index]))
        enable = enabled is False
        binary_list[index] = unicode(int(enable))
        self.__refresh_pin_bus(pin_num)

    def turn_off(self):
        """Sets all pins to an off state."""
        for pin_num in self.pin_to_bus:
            self.set_pin(pin_num, enable=False, update_device=False)
        for bus_write in set(self.pin_to_bus.values()):
            bus_write(0)

    def turn_on(self):
        """Sets all pins to an on state."""
        pins = [pin_num for pin_num in self.pin_to_bus.keys()]
        self.set_pins(pins, True)

    def add_channels(self, device_address, io_address, olat_address, output_bits=8):
        """Adds an 8 channel bus with 8 pins."""
        self.bus.write_byte_data(device_address, io_address, 0)
        bus_write = partial(self.bus.write_byte_data, device_address, olat_address)
        bus_write(0)
        binary_list = [u"0" for e in xrange(output_bits)]
        start = self.pin_count + 1
        for num, pin_num in enumerate(range(start, start + output_bits)):
            self.pin_to_bus[pin_num] = bus_write
            self.pin_to_binary_list[pin_num] = binary_list
            self.pin_to_index[pin_num] = -(num + 1)
            self.pin_count += 1

    def add_mcp(self, address):
        """Adds a MCP23017 Device with all pins set as output"""
        io_adr_a, out_adr_a = 0x00, 0x14
        io_adr_b, out_adr_b = 0x01, 0x15
        self.add_channels(address, io_adr_a, out_adr_a)
        self.add_channels(address, io_adr_b, out_adr_b)

    def map_pin_num(self, actual_pin_num, mapping):
        """You can set a mapping for a pin sok
        When you call methods with a pin number it finds
        a different mapped pin."""
        self.mapped_pins[mapping] = actual_pin_num

    def clear_mapping(self):
        """Removes all mapped pins."""
        self.mapped_pins.clear()

    def test_all(self):
        """Tests all of the output pins."""
        for num in range(len(self.pin_to_binary_list.keys())):
            num = num + 1
            self.set_pin(num)
            time.sleep(.1)
            if num % 15 == 0:
                self.turn_off()
                time.sleep(1)
        self.turn_off()

    def __refresh_pin_bus(self, pin_num):
        """Writes the binary to the bus"""
        bus_write = self.pin_to_bus[pin_num]
        binary_string = u"".join(bit for bit in self.pin_to_binary_list[pin_num])
        binary = int(binary_string, 2)
        bus_write(binary)

    def __adjust_pin(self, pin_num):
        """Adjust the pin number if there is a mapping."""
        if pin_num in self.mapped_pins:
            pin_num = self.mapped_pins[pin_num]
        return pin_num

    def __del__(self):
        self.turn_off()
