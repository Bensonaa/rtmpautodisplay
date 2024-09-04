#!/bin/bash

# Update package list and upgrade all packages
sudo apt-get update
sudo apt-get upgrade -y

# Install necessary packages
sudo apt-get install -y ffmpeg feh xorg xserver-xorg xinit

# Ensure the autostart directory exists
mkdir -p /home/pi/.config/autostart

# Create a desktop entry for autostart
cat <<EOL > /home/pi/.config/autostart/stream.desktop
[Desktop Entry]
Type=Application
Name=Stream Manager
Exec=/usr/bin/python3 /home/pi/rtmpautodisplay/stream.py
StartupNotify=false
EOL

# Move the desktop entry to the autostart directory
mv stream.desktop /home/pi/.config/autostart/

echo "Installation complete. The script will autostart after the Raspbian desktop loads. Please reboot."
