#!/usr/bin/env python3
"""Generate the minimal Apple device tree for the UMS512 XNU entry stage."""
from pathlib import Path
import argparse
import os
import struct
import zlib


def prop(name, data):
    return struct.pack("<32sI", name.encode(), len(data)) + data + bytes(-len(data) % 4)


def node(name, properties=(), children=()):
    entries = [("name", name.encode() + b"\0"), *properties]
    return struct.pack("<II", len(entries), len(children)) + b"".join(
        prop(key, value) for key, value in entries
    ) + b"".join(children)


def nvram():
    def header(name, size):
        raw = bytearray(struct.pack("<BBH12s", 0x70, 0, size // 16, name))
        checksum = sum(raw)
        while checksum > 255:
            checksum = (checksum & 255) + (checksum >> 8)
        raw[1] = checksum
        return raw

    image = bytearray(8192)
    image[:16] = header(b"nvram", 32)
    image[32:48] = header(b"common", 16 + 2048)
    free = 32 + 16 + 2048
    image[free:free + 16] = header(b"free", len(image) - free)
    struct.pack_into("<I", image, 16, zlib.adler32(image[20:]))
    return [
        ("nvram-bank-size", struct.pack("<I", len(image))),
        ("nvram-bank-count", struct.pack("<I", 1)),
        ("nvram-current-bank", struct.pack("<I", 0)),
        ("nvram-proxy-data", bytes(image)),
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dram-size", type=lambda x: int(x, 0), required=True)
    parser.add_argument("--owned-memory-size", type=lambda x: int(x, 0))
    parser.add_argument("--cpu-regs", default="0,0x100,0x200,0x300,0x400,0x500,0x600,0x700")
    args = parser.parse_args()

    cpus = [int(value, 0) for value in args.cpu_regs.split(",")]
    if not cpus or cpus[0] != 0 or len(cpus) > 8 or len(set(cpus)) != len(cpus):
        parser.error("--cpu-regs must start at 0 and contain up to eight unique MPIDRs")
    if args.owned_memory_size and (args.owned_memory_size < 0x10000000 or args.owned_memory_size % 0x200000):
        parser.error("--owned-memory-size must be 2 MiB aligned and at least 256 MiB")

    cpu_nodes = [
        node(f"cpu{index}", [
            ("state", (b"running" if index == 0 else b"waiting") + b"\0"),
            ("reg", struct.pack("<I", value)),
            ("device_type", b"cpu\0"),
            # Keep one homogeneous CPU model in the ADT. The T610YP has a
            # heterogeneous A75/A55 topology, but this XNU port follows the
            # existing bring-up convention and exposes the A55 model to the
            # CPU/platform code for every enabled MPIDR.
            ("compatible", b"arm,cortex-a55\0"),
            ("clock-frequency", struct.pack("<I", 1800000000)),
            ("timebase-frequency", struct.pack("<I", 26000000)),
        ]) for index, value in enumerate(cpus)
    ]
    chosen = [
        ("osenvironment", b"main\0"),
        ("dram-base", struct.pack("<Q", 0x80000000)),
        ("dram-size", struct.pack("<Q", args.dram_size)),
        ("crypto-hash-method", b"sha2-384\0"),
        ("amfi-only-platform-code", struct.pack("<I", 1)),
        *([("darwinboot-memory-size", struct.pack("<Q", args.owned_memory_size))]
          if args.owned_memory_size else []),
        *nvram(),
    ]
    children = [
        node("memory-map", [("TrustCache", bytes(16))]),
        node("manifest-properties"),
    ]
    tree = node("device-tree", [
        ("model", b"t610yp\0"),
        ("compatible", b"sprd,ums512\0sprd,sharkl5pro\0"),
        ("#address-cells", struct.pack("<I", 2)),
        ("#size-cells", struct.pack("<I", 2)),
    ], [
        node("chosen", chosen, children),
        node("cpus", children=cpu_nodes),
        node("psci", [("compatible", b"arm,psci-1.0\0"), ("method", b"smc\0")]),
        node("defaults", [("sleep-disabled", struct.pack("<I", 1))]),
        node("options"),
        node("product", [
            ("product-name", b"Unisoc T610YP\0"),
            ("model", b"sprd,t610yp\0"),
        ]),
        node("arm-io", [
            ("device_type", b"arm-io\0"),
            ("#address-cells", struct.pack("<I", 2)),
            ("#size-cells", struct.pack("<I", 2)),
            ("ranges", struct.pack("<QQQ", 0, 0x12000000, 0x5F000000)),
        ], [
            node("intc", [
                ("compatible", b"arm,gic-v3\0"),
                ("reg", struct.pack("<4Q", 0, 0x20000, 0x40000, 0x100000)),
                ("redistributor-stride", struct.pack("<Q", 0x20000)),
            ]),
        ]),
    ])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(tree)
    print(f"t610yp ADT: {len(tree)} bytes, dram={args.dram_size:#x}, cpus={len(cpus)}")


if __name__ == "__main__":
    main()
