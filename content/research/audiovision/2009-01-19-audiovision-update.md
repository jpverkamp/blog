---
title: AudioVision Update
date: 2009-01-19 05:05:26
programming/languages:
- .NET
- C and C++
- C#
- Python
programming/topics:
- Vision
slug: audiovision-update-2
---
Since deciding that I cannot use MATLAB because of the additional addons necessary to use webcams, I have been deciding between C# and Python as the next language to try. I've settled on Python for the time being, using <a href="http://videocapture.sourceforge.net/">VideoCapture</a> to connect to the webcams and <a href="http://numpy.scipy.org/">Numpy</a> to process the data. It turns out that Python + VideoCapture + Numpy is actually rather similar in functionality and syntax to MATLAB with its image processing library.

<!--more-->

So far, I've completed the code that would be necessary to connect to two webcams and produce a depth map from the collected data. I've tested the depth algorithm on a number of still images from stereo vision test sets and it appears to be working correctly. In addition, I have successfully connected to a single webcam using the VideoCapture library; however, I still cannot interface with two webcams at the same time. I believe this is an issue with the webcam drivers that I am using (both webcams are the same model) and I hope to resolve this issue soon.