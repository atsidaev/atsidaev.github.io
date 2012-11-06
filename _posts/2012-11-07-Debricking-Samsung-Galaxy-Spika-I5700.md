---
layout: post
tags: [ unbrick, i5700, openocd, jtag, embedded ]
---
After human-related mistakes during flashing process, I become an owner of a brick named "Samsung Galaxy Spica (I5700)".
Visually the brick was complete: no reaction on power button, no reaction on charger, 
no reaction on attempts to enter the Download mode again.
But after some research I managed to restore it to the fully working state.

You'll need Linux box and little soldering skill. Linux is needed for the openocd JTAG bridge. I have no idea
if it works in Windows as well, never tried. As an adapter I used my old self-made LPT Wiggler JTAG.

## JTAG adapter
First, you'll need JTAG adapter. The easiest to solder one contains only DB-25M connector (LPT male), 
4 x 100 Ohm resistors and wires. Scheme attached:

![Simpliest JTAG scheme](/images/2012-11-07/jtag.jpg)

Then you need to unglue sticker under the battery and solder JTAG adapter directly to pads. 
You need to solder only TDI, TDO, TMS, TCK (AP_JTAG_DI, AP_JTAG_DO, AP_JTAG_TMS and AP_JTAG_TCK 
on the image below), other signals are optional. 

![I5700 JTAG pinout](/images/2012-11-07/i5700pinout.jpg)

You may solder GND pad too but it's much easier to connect micro-usb cable to Spica - 
this will connect phone GND with GND of the PC.

Surely you can use any other JTAG adapter, just change openocd compilation settings and config file.

## Setting up openocd

Now we need to install openocd. Get it from your distro repository or build from sources:

1. Get latest sources from http://sourceforge.net/projects/openocd/files/openocd/ (I used 0.6.1)
2. Untar and enter directory
3. execute './configure --enable-parport'
4. execute 'make && make install'

Create file i5700.cfg with following contents:

```
gdb_port 3333
gdb_breakpoint_override hard
gdb_memory_map enable
gdb_flash_program enable

interface parport
parport_cable chameleon
reset_config none
adapter_khz 5
```

Now test the connection. Put the battery on it's place 
(it may be hard to fixate because of soldered wires, use the duct tape :) )
Run

```bash
sudo openocd -f i5700.cfg -f /usr/share/openocd/scripts/target/samsung_s3c6410.cfg
```
sudo is needed because LPT port cannot be accessed by regular user in most of distros.

You should see something like

```
Open On-Chip Debugger 0.6.1 (2012-11-06-02:19)
Licensed under GNU GPL v2
For bug reports, read
	http://openocd.sourceforge.net/doc/doxygen/bugs.html
force hard breakpoints
Warn : Adapter driver 'parport' did not declare which transports it allows; assuming legacy JTAG-only
Info : only one transport option; autoselect 'jtag'
none separate
adapter speed: 5 kHz
adapter_nsrst_delay: 500
jtag_ntrst_delay: 500
trst_and_srst separate srst_gates_jtag trst_push_pull srst_open_drain
Info : clock speed 5 kHz
Info : JTAG tap: s3c6410.etb tap/device found: 0x2b900f0f (mfg: 0x787, part: 0xb900, ver: 0x2)
Info : JTAG tap: s3c6410.cpu tap/device found: 0x07b76f0f (mfg: 0x787, part: 0x7b76, ver: 0x0)
Info : found ARM1176
Info : s3c6410.cpu: hardware has 6 breakpoints, 2 watchpoints
Warn : ETMv2+ support is incomplete
Info : ETM v3.2
```

If no, check soldering. Also, you can lower speed (adapter_khz parameter of config file).

## Setting up GDB

Ok, we can connect to phone. Now we need to get gdb and assembler for arm processor. 
Have no idea if this can be found in any distro's repos. Let's build it from sources.

```bash
wget http://ftp.gnu.org/gnu/gdb/gdb-7.5.tar.gz
tar zxf gdb-7.5.tar.gz
cd gdb-7.5
./configure --target=armv6zk-unknown-linux-gnueabi --program-prefix=armv6zk-unknown-linux-gnueabi-
make
make install

wget http://ftp.gnu.org/gnu/binutils/binutils-2.23.tar.gz
tar zxf binutils-2.23.tar.gz
cd binutils-2.23
./configure --target=armv6zk-unknown-linux-gnueabi --program-prefix=armv6zk-unknown-linux-gnueabi-
make
make install
```

Note that I write "make install" only as example of easiest way to install just compiled software.
I recommend to deal with 'checkinstall' utility and use it instead.

## Unbricking

Now get [flasher and bootloaders by tom3q](https://cloud.mail.ru/public/SCsR/ZCe9yQQKT). Unzip them to clean directory.
Edit Makefile, change "CPP=$(CROSS_COMPILE)cpp" to "CPP=cpp" - we did not compiled gcc for arm,
so we do not have armv6zk-unknown-linux-gnueabi-cpp.

Run

```bash
make
mv flasher.bin flasher_sbl.bin
```

Then open flasher.S with your favorite text editor and comment 
Sbl-specific lines (lines 66-67), and uncomment Pbl-specific (61-62)

```
make
mv flasher.bin flasher_pbl.bin
```

LPT Jtag is very sloooooow, so download of boot.bin will take around 10 minutes. 
I split boot.bin into 16 smaller download blocks to avoid gdb (or openocd) synchronization errors. 
Create file boot.restore

```
restore boot.bin binary 0x50000000 0x0 0x2000
restore boot.bin binary 0x50000000 0x2000 0x4000
restore boot.bin binary 0x50000000 0x4000 0x6000
restore boot.bin binary 0x50000000 0x6000 0x8000
restore boot.bin binary 0x50000000 0x8000 0xA000
restore boot.bin binary 0x50000000 0xA000 0xC000
restore boot.bin binary 0x50000000 0xC000 0xE000
restore boot.bin binary 0x50000000 0xE000 0x10000
restore boot.bin binary 0x50000000 0x10000 0x12000
restore boot.bin binary 0x50000000 0x12000 0x14000
restore boot.bin binary 0x50000000 0x14000 0x16000
restore boot.bin binary 0x50000000 0x16000 0x18000
restore boot.bin binary 0x50000000 0x18000 0x1A000
restore boot.bin binary 0x50000000 0x1A000 0x1C000
restore boot.bin binary 0x50000000 0x1C000 0x1E000
restore boot.bin binary 0x50000000 0x1E000 0x20000
```

Now everything is ready to perform flashing.
Run openocd as described above.
Run

```bash
# armv6zk-unknown-linux-gnueabi-gdb
(gdb) target remote localhost:3333
(gdb) set remotetimeout 25
(gdb) monitor reset halt
(gdb) source boot.restore
... a lot of "Restoring binary" messages comes here...
(gdb) restore flasher_pbl.bin binary 0x51000000
(gdb) b *0x51000108 <-------- specify here correct address of last command of compiled program, in your case it can be different.
(gdb) jump *0x51000000
```

After last command you'll get

```
Continuing at 0x51000000.

Breakpoint 1, 0x51000108 in ?? ()
```

That's all, remove the battery, disconnect LPT, put battery back and try to turn the phone on. 
In my case it started to charging and entering VolDown+Camera+PowerOn download mode.
If your phone still bricked than you should repeat last steps for Sbl.bin bootloader.

Sbl.restore:

```
restore Sbl.bin binary 0x50000000 0x0 0x2000
restore Sbl.bin binary 0x50002000 0x2000 0x4000
restore Sbl.bin binary 0x50004000 0x4000 0x6000
restore Sbl.bin binary 0x50006000 0x6000 0x8000
restore Sbl.bin binary 0x50008000 0x8000 0xA000
restore Sbl.bin binary 0x5000A000 0xA000 0xC000
restore Sbl.bin binary 0x5000C000 0xC000 0xE000
restore Sbl.bin binary 0x5000E000 0xE000 0x10000
restore Sbl.bin binary 0x50010000 0x10000 0x12000
restore Sbl.bin binary 0x50012000 0x12000 0x14000
restore Sbl.bin binary 0x50014000 0x14000 0x16000
restore Sbl.bin binary 0x50016000 0x16000 0x18000
restore Sbl.bin binary 0x50018000 0x18000 0x1A000
restore Sbl.bin binary 0x5001A000 0x1A000 0x1C000
restore Sbl.bin binary 0x5001C000 0x1C000 0x1E000
restore Sbl.bin binary 0x5001E000 0x1E000 0x20000
restore Sbl.bin binary 0x50020000 0x20000 0x22000
restore Sbl.bin binary 0x50022000 0x22000 0x24000
restore Sbl.bin binary 0x50024000 0x24000 0x26000
restore Sbl.bin binary 0x50026000 0x26000 0x28000
restore Sbl.bin binary 0x50028000 0x28000 0x2A000
restore Sbl.bin binary 0x5002A000 0x2A000 0x2C000
restore Sbl.bin binary 0x5002C000 0x2C000 0x2E000
restore Sbl.bin binary 0x5002E000 0x2E000 0x30000
restore Sbl.bin binary 0x50030000 0x30000 0x32000
restore Sbl.bin binary 0x50032000 0x32000 0x34000
restore Sbl.bin binary 0x50034000 0x34000 0x36000
restore Sbl.bin binary 0x50036000 0x36000 0x38000
restore Sbl.bin binary 0x50038000 0x38000 0x3A000
restore Sbl.bin binary 0x5003A000 0x3A000 0x3C000
restore Sbl.bin binary 0x5003C000 0x3C000 0x3E000
restore Sbl.bin binary 0x5003E000 0x3E000 0x40000
restore Sbl.bin binary 0x50040000 0x40000 0x42000
restore Sbl.bin binary 0x50042000 0x42000 0x44000
restore Sbl.bin binary 0x50044000 0x44000 0x46000
restore Sbl.bin binary 0x50046000 0x46000 0x48000
restore Sbl.bin binary 0x50048000 0x48000 0x4A000
restore Sbl.bin binary 0x5004A000 0x4A000 0x4C000
restore Sbl.bin binary 0x5004C000 0x4C000 0x4E000
restore Sbl.bin binary 0x5004E000 0x4E000 0x50000
restore Sbl.bin binary 0x50050000 0x50000 0x52000
restore Sbl.bin binary 0x50052000 0x52000 0x54000
restore Sbl.bin binary 0x50054000 0x54000 0x56000
restore Sbl.bin binary 0x50056000 0x56000 0x58000
restore Sbl.bin binary 0x50058000 0x58000 0x5A000
restore Sbl.bin binary 0x5005A000 0x5A000 0x5C000
restore Sbl.bin binary 0x5005C000 0x5C000 0x5E000
restore Sbl.bin binary 0x5005E000 0x5E000 0x60000
restore Sbl.bin binary 0x50060000 0x60000 0x62000
restore Sbl.bin binary 0x50062000 0x62000 0x64000
restore Sbl.bin binary 0x50064000 0x64000 0x66000
restore Sbl.bin binary 0x50066000 0x66000 0x68000
restore Sbl.bin binary 0x50068000 0x68000 0x6A000
restore Sbl.bin binary 0x5006A000 0x6A000 0x6C000
restore Sbl.bin binary 0x5006C000 0x6C000 0x6E000
restore Sbl.bin binary 0x5006E000 0x6E000 0x70000
restore Sbl.bin binary 0x50070000 0x70000 0x72000
restore Sbl.bin binary 0x50072000 0x72000 0x74000
restore Sbl.bin binary 0x50074000 0x74000 0x76000
restore Sbl.bin binary 0x50076000 0x76000 0x78000
restore Sbl.bin binary 0x50078000 0x78000 0x7A000
restore Sbl.bin binary 0x5007A000 0x7A000 0x7C000
restore Sbl.bin binary 0x5007C000 0x7C000 0x7E000
restore Sbl.bin binary 0x5007E000 0x7E000 0x80000
```

And use flasher_sbl.bin file instead of flasher_pbl.bin

Good luck, hope this helps somebody.

Thanks to [tom3q @ samdroid forum](http://forum.samdroid.net/f63/totally-bricked-when-downgrading-there-jtag-pinout-service-manual-buy-new-5439/#post164545&e=16829830) for the low-level download code and Spica JTAG pinout image.
