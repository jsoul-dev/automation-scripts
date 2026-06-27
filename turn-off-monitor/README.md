# Turn Off Monitor

A very simple script to instantly put your monitors to sleep without putting the entire computer to sleep.

## Version
Current Version: **1.0.0**

## Overview
This script uses a one-line PowerShell command calling native Windows APIs (`SendMessage` with `0xF170`) to immediately trigger the display power-off state. 

This is incredibly useful if you want to turn off your screens (e.g., when leaving your desk, going to sleep, or running a background task overnight) without waiting for the Windows idle timer to kick in, and without physically pressing the power buttons on multiple monitors.

## Usage

1. Run `turn-off-monitor.bat`.
2. Your screens will immediately turn off. 
3. Simply move your mouse or press any key on your keyboard to wake them back up.
