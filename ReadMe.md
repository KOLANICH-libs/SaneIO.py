SaneIO.py [![Unlicensed work](https://raw.githubusercontent.com/unlicense/unlicense.org/master/static/favicon.png)](https://unlicense.org/)
=========
~~[wheel (GHA via `nightly.link`)](https://nightly.link/KOLANICH-libs/SaneIO.py/workflows/CI/master/SaneIO-0.CI-py3-none-any.whl)~~
~~[![GitHub Actions](https://github.com/KOLANICH-libs/SaneIO.py/workflows/CI/badge.svg)](https://github.com/KOLANICH-libs/SaneIO.py/actions/)~~
![N∅ hard dependencies](https://shields.io/badge/-N∅_Ъ_deps!-0F0)
[![Libraries.io Status](https://img.shields.io/librariesio/github/KOLANICH-libs/SaneIO.py.svg)](https://libraries.io/github/KOLANICH-libs/SaneIO.py)
[![Code style: antiflash](https://img.shields.io/badge/code%20style-antiflash-FFF.svg)](https://codeberg.org/KOLANICH-tools/antiflash.py)

A very simplified and limited IO framework.

1. It is simple to use. It comes at cost.
	1. Count of callback funtions is minimized.
	2. Every object MUST inherit certain classes.
	3. Batteries included.

2. It is "portable" in the sense the ports of this framework to other languages and platforms should keep the same structure, allowing the programs using it be ported more easily.
	1. The core is decoupled from concrete implementations.
	2. Upper level protocols are "Sans-IO". They don't depend on concrete IO implementations. Instead they depend on the interfaces provided by the framework.
	3. Composition over inheritance -> can be ported C and Rust support

3. It is composable. The structure is a stack of objects.
	* Wanna change the protocol in the stack? Just replace the layer object!
	* Wanna access the same server using both TCP and UART? Just add a mux!
	* Wanna access multiple upper layer protocols over the same low-level protocol (i.e. TCP)? Again, just add a mux!
