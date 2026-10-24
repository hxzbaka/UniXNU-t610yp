# T610YP bring-up notes

## Component boundaries

`edk2-sprd` is the firmware port. Its existing UMS512 platform already maps
the T610YP memory layout, initializes the `0x70100000` debug UART, exposes GOP,
and builds the `Platform/YEPEN/ums512/t610yp/t610yp.dsc` board.

`UniXNU` supplies the build driver, UniXNU UEFI application, DarwinBoot and the
generic XNU modules. `UniXNU-t610yp` supplies only board data and the first
bring-up configuration.

`DeviceTree/t610w.dts` is the Linux FDT from the vendor kernel. It is useful
for verifying physical addresses and CPU topology:

| Item | Value |
| --- | --- |
| SoC | `sprd,ums512` / sharkl5pro |
| UART used by `/chosen/stdout-path` | `0x70100000` |
| second UART | `0x70000000` |
| GICv3 distributor | `0x12000000` |
| GICv3 redistributors | `0x12040000` |
| CPUs | 2x Cortex-A75 and 6x Cortex-A55; ADT exposes all eight MPIDRs with the A55-compatible XNU model |
| DRAM base | `0x80000000` |
| UEFI architectural timer frequency | `26 MHz` |

XNU does not consume this FDT directly. `scripts/make-t610yp-adt.py` emits the
Apple node encoding consumed by `ArmDTPlatform` and DarwinBoot. The first ADT
contains only `/chosen`, `/cpus`, `/psci`, `/defaults`, `/options`, `/product`
and `/arm-io/intc`; adding storage or display nodes before their drivers exist
would create misleading probe failures.

## First hardware milestone

Use the existing UEFI menu and select the UniXNU payload. The expected order
of useful evidence is:

1. `UNIXNU:` firmware and configuration messages on the `0x70100000` UART.
2. `DARWINBOOT:` allocation, handoff and `exiting boot services`.
3. XNU output enabled by `-v serial=3 debug=0x14e`.
4. A platform or driver panic identifying the next missing service.

The screen path is available from the existing EDK II GOP, but UART is the
authoritative first channel. `boot-progress=1` is enabled as a fallback once
the kernel maps the framebuffer.

## Firmware integration

The ordinary `edk2-sprd` checkout is modified directly for this board. Its
T610YP DSC/FDF includes UniXNU and DarwinBoot, and its native build script
adds the package roots from `Common/UniXNU` and `Common/DarwinBoot`.
`UniXNU-t610yp` only supplies the board description, ADT generator, kernel
defconfig and Unixnu build inputs.

`edk2-sprd/Resources/Configs/t610yp.toml` supplies the FD base/size and boot
image parameters used by the firmware and BootShim steps.

