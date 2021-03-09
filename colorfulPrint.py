#!/usr/bin/env python3

from colorama import init, Fore, Back, Style


init()

COLOR_SET = (
    "BLACK", "RED", "GREEN", "YELLOW", 
    "BLUE", "MAGENTA", "CYAN", "WHITE", 
    "RESET"
)


def str_in_color(text, fcolor="RESET", bcolor="RESET"):
    fcolor = fcolor.upper()
    bcolor = bcolor.upper()
    if fcolor not in COLOR_SET:
        raise ValueError(f"Unknown colorama color '{fcolor}'. Use one of {COLOR_SET} instead.")
    elif bcolor not in COLOR_SET:
        raise ValueError(f"Unknown colorama color '{bcolor}'. Use one of {COLOR_SET} instead.")
    else:
        prefix = eval(f"Fore.{fcolor} + Back.{bcolor}")
        suffix = Style.RESET_ALL
        return prefix + str(text) + suffix


def str_in_forecolor(text, color):
    return str_in_color(text, fcolor=color)


def str_in_backcolor(text, color):
    return str_in_color(text, bcolor=color)


def print_in_red(text):
    return str_in_color(text, fcolor="RED")


def print_in_green(text):
    return str_in_color(text, fcolor="GREEN")


# function alias
print_warning = print_in_red
print_bingo = print_in_green


if __name__ == '__main__':
    # run test
    color_set = COLOR_SET[:-1]  # ignore "RESET"
    
    for fore in color_set:
        print("Forecolor in " + str_in_forecolor(fore, fore))
        
        back_list = [str_in_backcolor(back, back) for back in color_set]
        comp_list = [str_in_color(back, fore, back) for back in color_set]
        print("    Backcolor in", *back_list)
        print("    Composition ", *comp_list)
