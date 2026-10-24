# UniXNU T610YP

Bring-up tree for the Unisoc UMS512 / SharkL5Pro T610YP board.

The first milestone is XNU `8796.141.3` entering the kernel with logs on the
Spreadtrum UART and framebuffer handoff supplied by DarwinBoot. The initial
defconfig deliberately excludes eMMC, UFS, GPU and mobile-display archives.

## Local build inputs

`feeds.toml` points at the local checkout:

`D:/ubuntu2404/rootfs/home/hxzbaka/edk2/xnu-xnu-8796.141.3`

This keeps source qualification separate from any XNU source tree edits.

## Bring-up configuration

- UART: `0x70100000`, polled mode, firmware clock/baud preserved
- framebuffer: supplied through DarwinBoot `PE_video`, expected base `0x9e000000`
- GICD: `0x12000000`
- GICR: `0x12040000`, stride `0x20000`
- architectural timer PPIs: 13, 14, 11, 10
- CPU topology: six Cortex-A55 cores and two Cortex-A75 cores

Use `configs/t610yp_defconfig` for the first kernel-entry build. eMMC support
will be added only after the UART/framebuffer/XNU entry path is stable.

