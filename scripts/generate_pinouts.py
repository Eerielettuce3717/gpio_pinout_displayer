from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "pinouts.json"

NW = 10  # gpio name col width
CW = 7   # arduino 3-col width


def _rpi_row(left: str, lp: str, rp: str, right: str) -> str:
    return f"| {left[:NW]:<{NW}} | {lp:>2} || {rp:<2} | {right[:NW]:>{NW}} |"


def _rpi_border() -> str:
    n = len(_rpi_row("X" * NW, "00", "00", "X" * NW)) - 2
    return "+" + "-" * n + "+"


def _rpi_box(text: str) -> str:
    inner = len(_rpi_row("X" * NW, "00", "00", "X" * NW)) - 2
    t = text[: inner - 2]
    return "| " + t.center(inner - 2) + " |"


def _tri(c1: str, c2: str, c3: str) -> str:
    return f"| {c1[:CW]:^{CW}} | {c2[:CW]:^{CW}} | {c3[:CW]:^{CW}} |"


def _tri_border() -> str:
    n = len(_tri("", "", "")) - 2
    return "+" + "-" * n + "+"


def _box_line(text: str) -> str:
    inner = len(_tri("", "", "")) - 2
    t = text[: inner - 2]
    return "| " + t.center(inner - 2) + " |"


def insert_pin_gaps(lines: list[str]) -> list[str]:
    skip = ("LEFT", "RIGHT", "[USB", "[BAR", "[Micro", "[PWR", "DIGITAL", "ANALOG", "compact", "L-side")
    out: list[str] = []
    for i, line in enumerate(lines):
        out.append(line)
        if not line.startswith("|"):
            continue
        if any(k in line for k in skip):
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if nxt.startswith("|") and not any(k in nxt for k in skip):
            out.append("")
    return out

RPI40_ROWS = [
    ("3.3V", "01", "02", "5V", "P", "P"),
    ("SDA", "03", "04", "5V", "I", "P"),
    ("SCL", "05", "06", "GND", "I", "G"),
    ("GP4", "07", "08", "TX", "G", "U"),
    ("GND", "09", "10", "RX", "G", "U"),
    ("GP17", "11", "12", "GP18", "G", "P"),
    ("GP27", "13", "14", "GND", "G", "G"),
    ("GP22", "15", "16", "GP23", "G", "G"),
    ("3.3V", "17", "18", "GP24", "P", "G"),
    ("MOSI", "19", "20", "GND", "S", "G"),
    ("MISO", "21", "22", "GP25", "S", "G"),
    ("SCLK", "23", "24", "CE0", "S", "S"),
    ("GND", "25", "26", "CE1", "G", "S"),
    ("IDSD", "27", "28", "IDSC", "I", "I"),
    ("GP5", "29", "30", "GND", "G", "G"),
    ("GP6", "31", "32", "GP12", "G", "P"),
    ("GP13", "33", "34", "GND", "P", "G"),
    ("GP19", "35", "36", "GP16", "A", "G"),
    ("GP26", "37", "38", "GP20", "G", "A"),
    ("GND", "39", "40", "GP21", "G", "I"),
]

RPI40_ROWS_DETAIL = [
    ("3.3V", "01", "02", "5V", "power", "power"),
    ("GPIO2/SDA", "03", "04", "5V", "i2c", "power"),
    ("GPIO3/SCL", "05", "06", "GND", "i2c", "ground"),
    ("GPIO4", "07", "08", "GPIO14/TX", "gpio", "uart"),
    ("GND", "09", "10", "GPIO15/RX", "ground", "uart"),
    ("GPIO17", "11", "12", "GPIO18/PWM", "gpio", "pwm"),
    ("GPIO27", "13", "14", "GND", "gpio", "ground"),
    ("GPIO22", "15", "16", "GPIO23", "gpio", "gpio"),
    ("3.3V", "17", "18", "GPIO24", "power", "gpio"),
    ("GPIO10/MOSI", "19", "20", "GND", "spi", "ground"),
    ("GPIO9/MISO", "21", "22", "GPIO25", "spi", "gpio"),
    ("GPIO11/SCLK", "23", "24", "GPIO8/CE0", "spi", "spi"),
    ("GND", "25", "26", "GPIO7/CE1", "ground", "spi"),
    ("GPIO0/EEP", "27", "28", "GPIO1/EEP", "id", "id"),
    ("GPIO5", "29", "30", "GND", "gpio", "ground"),
    ("GPIO6", "31", "32", "GPIO12/PWM", "gpio", "pwm"),
    ("GPIO13/PWM", "33", "34", "GND", "pwm", "ground"),
    ("GPIO19/PCM", "35", "36", "GPIO16", "audio", "gpio"),
    ("GPIO26", "37", "38", "GPIO20/PCM", "gpio", "audio"),
    ("GND", "39", "40", "GPIO21/I2C", "ground", "i2c"),
]


def rpi40_ascii(model_name: str, subtitle: str, detailed: bool) -> list[str]:
    rows = RPI40_ROWS_DETAIL if detailed else RPI40_ROWS
    lines = [
        model_name,
        subtitle,
        _rpi_border(),
        _rpi_row("LEFT", "##", "##", "RIGHT"),
        _rpi_border(),
    ]
    for left, lp, rp, right, *_ in rows:
        lines.append(_rpi_row(left, lp, rp, right))
    lines.append(_rpi_border())
    if detailed:
        lines.extend(["Power=red GND=blk GPIO=grn", "Special: I2C UART SPI PWM"])
    else:
        lines.extend(["Legend: P=5V/3V G=GPIO", "       I=I2C U=UART S=SPI"])
    return lines


def arduino_uno_ascii(model_name: str, detailed: bool) -> list[str]:
    if detailed:
        rows = [
            ("VIN", "7-12V in", "PWR"),
            ("GND", "Ground", "GND"),
            ("5V", "5 Volt", "PWR"),
            ("3.3V", "3.3 Volt", "PWR"),
            ("RESET", "MCU reset", "CTL"),
            ("D0/RX", "UART RX", "UART"),
            ("D1/TX", "UART TX", "UART"),
            ("D2-D7", "Digital", "GPIO"),
            ("D8-D13", "Digital+SPI", "SPI"),
            ("A0-A3", "Analog in", "ADC"),
            ("A4/SDA", "I2C data", "I2C"),
            ("A5/SCL", "I2C clock", "I2C"),
        ]
        lines = [model_name, "Arduino Uno R3 pin map", _tri_border()]
        for pin, desc, kind in rows:
            lines.append(_tri(pin, desc, f"[{kind}]"))
        lines.append(_tri_border())
        return lines

    return [
        model_name,
        "ATmega328P · 14 digital · 6 analog",
        _tri_border(),
        _box_line("[USB]  [BAR]"),
        _tri_border(),
        _tri("0 RX", "8", "GND"),
        _tri("1 TX", "9~", "AREF"),
        _tri("2", "10~", "A0"),
        _tri("3~", "11~", "A1"),
        _tri("4", "12", "A2"),
        _tri("5~", "13", "A3"),
        _tri("6~", "GND", "A4"),
        _tri("7", "5V", "A5"),
        _tri_border(),
        "PWR: VIN 5V 3.3V GND",
        "~ = PWM   A4=SDA A5=SCL",
    ]


def arduino_nano_ascii(model_name: str, detailed: bool) -> list[str]:
    if detailed:
        rows = [
            ("D1/TX", "D0/RX"),
            ("D2", "GND"),
            ("D3~", "RESET"),
            ("D4", "5V"),
            ("D5~", "A7"),
            ("D6~", "A6"),
            ("D7", "A5/SCL"),
            ("D8", "A4/SDA"),
            ("D9~", "A3"),
            ("D10~", "A2"),
            ("D11~", "A1"),
            ("D12", "A0"),
            ("D13", "VIN"),
        ]
        lines = [model_name, "Arduino Nano (ATmega328)", _tri_border()]
        for left, right in rows:
            lines.append(_tri(left, "|", right))
        lines.append(_tri_border())
        lines.append("3.3V AREF on mini board")
        return lines
    rows = [
        ("D1 TX", "D0 RX"),
        ("D2", "GND"),
        ("D3~", "5V"),
        ("D4", "A0"),
        ("D5~", "A1"),
        ("D6~", "A2"),
        ("D7", "A3"),
        ("D8", "A4"),
        ("D9~", "A5"),
        ("D10~", "A6"),
        ("D11~", "A7"),
        ("D12", "VIN"),
    ]
    return [
        model_name,
        "Arduino Nano",
        _tri_border(),
        _box_line("[USB mini]"),
        _tri_border(),
        _tri("LEFT", "|", "RIGHT"),
        *[_tri(l, "|", r) for l, r in rows],
        _tri_border(),
        "A4=SDA  A5=SCL  ~=PWM",
    ]


def arduino_mega_ascii(model_name: str, detailed: bool) -> list[str]:
    if detailed:
        rows = [
            ("D0-D13", "Digital", "-"),
            ("D14-D21", "Ser3+I2C", "-"),
            ("D22-D53", "Digital", "-"),
            ("D50-D53", "SPI bus", "-"),
            ("A0-A15", "Analog", "-"),
        ]
        lines = [model_name, "Arduino Mega 2560", _tri_border()]
        for a, b, c in rows:
            lines.append(_tri(a, b, c))
        lines.append(_tri_border())
        lines.extend(["4x UART  SPI  I2C", "D20=SDA D21=SCL", "PWR: VIN 5V 3.3V"])
        return lines
    return [
        model_name,
        "Arduino Mega 2560",
        _tri_border(),
        _box_line("[USB] [PWR]"),
        _tri_border(),
        _box_line("54 DIGITAL"),
        _tri("D0 RX0", "...", "D13"),
        _tri("D14 TX3", "...", "D53 SS"),
        _tri_border(),
        _box_line("16 ANALOG A0-A15"),
        _tri_border(),
        "I2C: D20 SDA D21 SCL",
    ]


def arduino_micro_ascii(model_name: str, detailed: bool) -> list[str]:
    return [
        model_name,
        "Arduino Micro (32U4)",
        _tri_border(),
        _box_line("[Micro USB]"),
        _tri_border(),
        _box_line("D0-D13 + A0-A11"),
        _box_line("Native USB serial"),
        _box_line("5V 3.3V GND VIN"),
        _tri_border(),
        "Same layout as Leonardo" if detailed else "Compact board",
        "A4=SDA A5=SCL",
    ]


def arduino_leonardo_ascii(model_name: str, detailed: bool) -> list[str]:
    base = arduino_uno_ascii(model_name, detailed)
    base[1] = "Arduino Leonardo (32U4)"
    return base


def arduino_pro_mini_ascii(model_name: str, detailed: bool) -> list[str]:
    lines = arduino_nano_ascii(model_name, detailed)
    lines[1] = "Arduino Pro Mini"
    if not detailed:
        lines[3] = _box_line("(no USB - FTDI)")
    return lines


def arduino_zero_ascii(model_name: str, detailed: bool) -> list[str]:
    return [
        model_name,
        "Arduino Zero (SAMD21)",
        _tri_border(),
        _box_line("[Native USB]"),
        _tri_border(),
        _box_line("3.3V LOGIC ONLY"),
        _box_line("D0-D13 digital"),
        _box_line("A0-A10 analog"),
        _tri_border(),
        "DAC on A0" if detailed else "EDBG debugger",
        "I2C SDA/SCL dedicated",
    ]


def arduino_due_ascii(model_name: str, detailed: bool) -> list[str]:
    return [
        model_name,
        "Arduino Due (SAM3X)",
        _tri_border(),
        _box_line("[USB] [USB OTG]"),
        _tri_border(),
        _box_line("3.3V LOGIC ONLY"),
        _box_line("54 digital pins"),
        _box_line("12 analog A0-A11"),
        _box_line("2x DAC A0/A1"),
        _tri_border(),
        "Do NOT feed 5V to pins" if detailed else "96 MHz ARM",
    ]


def rpi_zero_ascii(model_name: str, variant: str, detailed: bool) -> list[str]:
    lines = rpi40_ascii(model_name, f"40-pin header · {variant}", detailed)
    lines[2:2] = [_rpi_border(), _rpi_box("[compact PCB]"), _rpi_border()]
    return lines


BOARDS: dict[str, dict] = {
    "Arduino-Uno": {
        "model_name": "Arduino Uno R3",
        "builder": lambda d: arduino_uno_ascii("Arduino Uno R3", d),
    },
    "Arduino-Nano": {
        "model_name": "Arduino Nano",
        "builder": lambda d: arduino_nano_ascii("Arduino Nano", d),
    },
    "Arduino-Mega": {
        "model_name": "Arduino Mega 2560",
        "builder": lambda d: arduino_mega_ascii("Arduino Mega 2560", d),
    },
    "Arduino-Micro": {
        "model_name": "Arduino Micro",
        "builder": lambda d: arduino_micro_ascii("Arduino Micro", d),
    },
    "Arduino-Leonardo": {
        "model_name": "Arduino Leonardo",
        "builder": lambda d: arduino_leonardo_ascii("Arduino Leonardo", d),
    },
    "Arduino-Pro-Mini": {
        "model_name": "Arduino Pro Mini",
        "builder": lambda d: arduino_pro_mini_ascii("Arduino Pro Mini", d),
    },
    "Arduino-Zero": {
        "model_name": "Arduino Zero",
        "builder": lambda d: arduino_zero_ascii("Arduino Zero", d),
    },
    "Arduino-Due": {
        "model_name": "Arduino Due",
        "builder": lambda d: arduino_due_ascii("Arduino Due", d),
    },
    "Raspberry Pi 5": {
        "model_name": "Raspberry Pi 5",
        "builder": lambda d: rpi40_ascii(
            "Raspberry Pi 5",
            "40-pin GPIO · PCIe · dual USB3",
            d,
        ),
    },
    "Raspberry-Pi-4-Model-B": {
        "model_name": "Raspberry Pi 4 Model B",
        "builder": lambda d: rpi40_ascii("Raspberry Pi 4 Model B", "40-pin GPIO · 3.3V logic", d),
    },
    "Raspberry-Pi-3-Model-B": {
        "model_name": "Raspberry Pi 3 Model B",
        "builder": lambda d: rpi40_ascii("Raspberry Pi 3 Model B", "40-pin GPIO · WiFi/BT", d),
    },
    "Raspberry-Pi-3-Model-B-": {
        "model_name": "Raspberry Pi 3 Model B+",
        "builder": lambda d: rpi40_ascii("Raspberry Pi 3 Model B+", "40-pin GPIO · PoE header", d),
    },
    "Raspberry-Pi-3-Model-A-": {
        "model_name": "Raspberry Pi 3 Model A+",
        "builder": lambda d: rpi40_ascii("Raspberry Pi 3 Model A+", "40-pin GPIO · compact", d),
    },
    "Raspberry-Pi-2-Model-B": {
        "model_name": "Raspberry Pi 2 Model B",
        "builder": lambda d: rpi40_ascii("Raspberry Pi 2 Model B", "40-pin GPIO · quad core", d),
    },
    "Raspberry-Pi-1-Model-B-": {
        "model_name": "Raspberry Pi 1 Model B+",
        "builder": lambda d: rpi40_ascii("Raspberry Pi 1 Model B+", "40-pin GPIO", d),
    },
    "Raspberry-Pi-1-Model-A-": {
        "model_name": "Raspberry Pi 1 Model A+",
        "builder": lambda d: rpi40_ascii("Raspberry Pi 1 Model A+", "40-pin GPIO · no RJ45", d),
    },
    "Raspberry-Pi-Zero": {
        "model_name": "Raspberry Pi Zero",
        "builder": lambda d: rpi_zero_ascii("Raspberry Pi Zero", "no wireless", d),
    },
    "Raspberry-Pi-Zero-W": {
        "model_name": "Raspberry Pi Zero W",
        "builder": lambda d: rpi_zero_ascii("Raspberry Pi Zero W", "WiFi + BT", d),
    },
    "Raspberry-Pi-Zero-WH": {
        "model_name": "Raspberry Pi Zero WH",
        "builder": lambda d: rpi_zero_ascii("Raspberry Pi Zero WH", "headers pre-soldered", d),
    },
    "Raspberry-Pi-Zero-2-W": {
        "model_name": "Raspberry Pi Zero 2 W",
        "builder": lambda d: rpi_zero_ascii("Raspberry Pi Zero 2 W", "quad core · WiFi", d),
    },
}


def main() -> None:
    payload = {"version": 1, "boards": {}}
    for class_id, spec in BOARDS.items():
        payload["boards"][class_id] = {
            "class_id": class_id,
            "model_name": spec["model_name"],
            "ascii": insert_pin_gaps(spec["builder"](False)),
            "ascii_detailed": insert_pin_gaps(spec["builder"](True)),
        }

    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
