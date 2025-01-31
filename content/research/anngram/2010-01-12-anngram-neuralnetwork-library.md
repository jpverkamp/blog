---
title: AnnGram - NeuralNetwork Library
date: 2010-01-12 05:05:54
programming/languages:
- .NET
- C#
programming/topics:
- Computational Linguistics
- Natural Language Processing
- Neural Networks
- Research
---
I've been looking for a good Neural Network library to use with the AnnGram project and so far I've come across a couple of possibilities:

<a href="http://franck.fleurey.free.fr/NeuralNetwork/">**C# Neural network library**</a>

The top link on Google was an aptly named C# Neural network library.  Overall, it looks clean and easy to use and is licensed under the <a href="http://www.gnu.org/licenses/gpl.html">GPL</a>, so should work well for my needs.   The framework has two types of training methods: genetic algorithms and backward propagation.  In addition, there are at least three different activation functions included: linear, signmoid, and heaviside functions.  The main problem with this framework is the spare documentation.  The only that I've been able to find so far is a generated API reference and a few examples (using their included GUI framework).

<!--more-->

**<a href="http://www.aforgenet.com/">AForge.Neuro</a>**

I've used the AForge framework before as part of my experiments with the <a href="http://blog.jverkamp.com/category/programming/audiovision/">AudioVision</a> project.  It's a strong framwork, much more complex and more powerful than the aforementioned library.  From this <a href="http://www.codeproject.com/KB/recipes/aforge_neuro.aspx">article on CodePlex</a>, the features of AForge.Neuro are pretty extensive.  There are two different architectures (the first library only had one) and six different learning methods (compared to two).  This also seems like a good match for the project, especially if it turns out I need the extra configuration options.

**<a href="http://neurondotnet.freehostia.com/">NeuronDotNet</a>**

Somewhere between the first two libraries, NeuronDotNet has the best documentation of the three with full tutorials on most of its functionality.  It has much of the same functionality as AForge.Neuro without the primary focus being elsewhere (AForge is primarily designed for image processing).  In addition, <a href="http://www.primaryobjects.com/CMS/Article105.aspx">this article on Primary Objects</a> gives further example source code--extremely helpful in development.

**Result**

Overall, I'm not sure exactly which library I will choose to use.  Mostly likely, I will switch at least once within the project as I become frustrated with my original choice.  In any case, I'll be sure to post my progress here.