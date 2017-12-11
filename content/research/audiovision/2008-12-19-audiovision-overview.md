---
title: AudioVision Overview
date: 2008-12-19 08:05:02
programming/languages:
- C and C++
programming/topics:
- Vision
---
I am taking an independent study course this winter in Image Recognition / Computer Vision. The primary goal of my independent study is to look into determining depth information from video feed(s) in real time and then representing that depth information using a 3D audio map (headphones).

<!--more-->

My initial goal for the visual half of the project is to use the <a href="http://make3d.stanford.edu/">Make3D</a> project from Standford to create the depth maps from a single webcam and to use another (undetermined) third party library to generate the 3D audio landscape.

The current idea for the audio half is to represent the visual world in a low resolution audio map. A set of m by n points will be placed in a half circle in the audio space around the listener's head ranging from left to right and from top to bottom. Closer objects will be represented with higher volumes, further with quieter ones.