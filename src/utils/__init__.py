from .file_control import save_value, load_value
from .serial import get_serial_port_list
from .image import resize_image


def sublist(lst1, lst2):
    def get_all_in(one, another):
        for element in one:
            if element in another:
                yield element

    for x1, x2 in zip(get_all_in(lst1, lst2), get_all_in(lst2, lst1)):
        if x1 != x2:
            return False
    return True
