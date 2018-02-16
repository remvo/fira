import os


def get_serial_port_list():
    output = os.popen('python -m serial.tools.list_ports', 'r')
    serials = output.read()
    return serials.split()
