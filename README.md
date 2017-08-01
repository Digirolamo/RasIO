# RasIO
Allows easy adding of IO expander chips to a Raspberry Pi via the I2c interface.

##Dependencies
- [python-smbus](https://launchpad.net/ubuntu/vivid/+package/python-smbus)
- [i2c-tools](https://launchpad.net/ubuntu/+source/i2c-tools/3.1.1-1)

##Supported Chips
- [mcp23017](http://ww1.microchip.com/downloads/en/DeviceDoc/21952b.pdf)

Here is an example:


    >>> from rasio import PinControler
    >>> control = PinControler()
    >>> control.add_mcp(0x20)
