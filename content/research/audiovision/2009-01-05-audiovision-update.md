---
title: AudioVision Update
date: 2009-01-05 08:05:51
programming/languages:
- C and C++
programming/topics:
- Vision
---
The original plan to use Make3D for the visual depth determination has mostly fallen through, partially because it has several dependencies that I cannot get to build correctly and partially because it is written in a combination of C and MATLAB. I have nothing against either of these languages; however, I do not have the addons necessary for MATLAB to connect to a webcam.

As such, I've decided to switch from a monocular vision algorithm to a more traditional stereo vision algorithm. I'm still looking for what new framework to use for the visual portion of the code.