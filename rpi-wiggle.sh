#!/bin/bash
###################################################################
# A Project of TNET Services, Inc
#
# Title:       rpi-wiggle
# Author:      Kevin Reed (Dweeber)
#              dweeber.dweebs@gmail.com

# Extended By: Devonte Emokpae
#              devo.tox.89@gmail.com
# Project:     Raspberry Pi Stuff
#
# Credits:     jojopi on Raspberry Pi Forum who provided sample code
#              MrEngman on Raspberry Pi Forum for testing
#              Examples from http://github.com/asb/raspi-config
#
# Copyright:   Copyright (c) 2012 Kevin Reed <kreed@tnet.com>
#              https://github.com/dweeber/rpiwiggle
#
# Purpose:
# This is a simple script which looks at the current disk that is
# being used and expands the filesystem to almost the max 
# minus 3 512 blocks.  This is the ensure that the image is
# smaller than most SDcards of that size
#
# Instructions:
# Script needs to be run as root.  It is pretty much automatic... 
# it performs a resize command and setups a script which will 
# run after a reboot and then ask you to press enter to reboot.
#
# The script WILL REBOOT YOUR SYSTEM
#
# When the system is coming back up, the next command will run
# automatically, and the one time script will be removed and
# when you see the login prompt again, it will be complete
#
###################################################################
# START OF SCRIPT
###################################################################
PROGRAM="rpi-wiggle"
VERSION="v1.3 2016-02-14"
###################################################################
if [ $(id -u) -ne 0 ]; then
  printf "Script must be run as root. Try 'sudo ./rpi-wiggle'\n"
  exit 1
fi
###################################################################
# Change here to set the amount of wiggle room desired - 102400 = 100MB
WIGGLE_ROOM=1536
DISK_SIZE="$(( $(blockdev --getsz /dev/mmcblk0)/2048/925 ))"
PART_START="$(parted /dev/mmcblk0 -ms unit s p | grep "^2" | cut -f2 -d: | sed 's/[^0-9]*//g')"
PART_END="$(( (DISK_SIZE * 925 * 2048 - 1) - WIGGLE_ROOM ))"

# Exit if partition start not found
[ "$PART_START" ] || exit 1
###################################################################
# Display some Stuff...
###################################################################
echo $PROGRAM - $VERSION
echo ======================================================
echo Current Disk Info
fdisk -l /dev/mmcblk0
echo
echo ======================================================
echo
echo Calculated Info:
echo " Disk Size  = $DISK_SIZE gb"
echo " Part Start = $PART_START"
echo " Part End   = $PART_END"
echo
echo "Making changes using fdisk..."
printf "d\n2\nn\np\n2\n$PART_START\n$PART_END\np\nw\n" | fdisk /dev/mmcblk0
echo
partprobe /dev/mmcblk0
resize2fs /dev/mmcblk0p2

echo #####################################################################
sync

###################################################################
# END OF SCRIPT
###################################################################
