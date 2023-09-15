---
title: AnnGram - Ideas for improvement
date: 2010-01-15 05:05:30
programming/languages:
- .NET
- C#
programming/topics:
- Computational Linguistics
- Natural Language Processing
- Neural Networks
- Research
---
After my meeting yesterday with my thesis advisers, I have a number of new ideas to try to improve the efficiency of the neural networks.  The most promising of those are described below.

**Sliding window**

The first idea was to replace the idea of applying the most common frequencies directly with a sliding window (almost a directly analogue to the nGrams themselves).  The best way that we could come up to implent this would be to give the neural networks some sort of memory which brought up recurring networks (see below).

<!--more-->

**[[wiki:NETtalk (artificial neural network)|NETtalk]]()**

From Wikipedia:

*NETtalk is perhaps the best known artificial neural network. It is the result of research carried out in the mid 1980s by Terrence Sejnowski and Charles Rosenberg. The intent behind NETtalk was to construct simplified models that might shed light on the complexity of learning human level cognitive tasks, and their implementation as a connectionist model that could also learn to perform a comparable task.*

I've looked into NETtalk and, while it is a really neat concept, I do not know how directly related it is to the project at hand.  Essentially, NETtalk was designed to apply neural networks to mimicking human speech.  It's actually very interesting to listen to the neural network progressing from what is essentially gibberish to intelligible speech.  I've included a link to the audio below:

From <a href="http://www.cnl.salk.edu/ParallelNetsPronounce/index.php">Salk Institute</a>:

<a href="http://www.cnl.salk.edu/ParallelNetsPronounce/nettalk.mp3">NETtalk</a>

If you are interested, you also can <a href="http://www.cnl.salk.edu/ParallelNetsPronounce/ParallelNetsPronounce-TJSejnowski.pdf">read the original report</a>.

**[[wiki:Self-organizing map|Self-ordering maps]]()**

From Wikipedia:

*A self-organizing map (SOM) or self-organizing feature map (SOFM) is a type of artificial neural network that is trained using unsupervised learning to produce a low-dimensional (typically two-dimensional), discretized representation of the input space of the training samples, called a map. Self-organizing maps are different from other artificial neural networks in the sense that they use a neighborhood function to preserve the topological properties of the input space.*

Self-ordering maps are interesting because they are already cropping up in more than one of the frameworks that I was looking through.  The basic idea is that you start with a field of essentially random seeming data and apply the neural network to it.  As the neural network learns, the data organizes into cohesive patterns.  I'm not exactly sure how the idea could be applied directly, but I did have one idea.  Perhaps the same concept from earlier (the vector of common nGram frequencies) for a great number of documents could be set out in a multi-dimensional space and a self-ordering map could be applied directly.  It's something that I'll have to look into.

**[[wiki:Recurrent neural network|Recurring networks]]()**

From Wikipedia:

*A recurrent neural network (RNN) is a class of neural network where connections between units form a directed cycle. This creates an internal state of the network which allows it to exhibit dynamic temporal behavior.*

*Recurrent neural networks must be approached differently from feedforward neural networks, both when analyzing their behavior and training them. Recurrent neural networks can also behave chaotically. Usually, dynamical systems theory is used to model and analyze them. While a feedforward network propagates data linearly from input to output, recurrent networks (RN) also propagate data from later processing stages to earlier stages.*

This seems to be the most useful of all of the links that I've checked so far.  As mentioned earlier under the idea of a sliding window, neural networks with memory would be a radically different alternative to the most common frequency vectors.  Essentially, the neural network receives input as the document is being scanned and some of the nodes will loop back.  In that way, the network can perceive ordering information as well as frequency information and improve its efficiency.  It's definitely something worth looking into if my current branch of exploration proves not to be optimal.

<a href="http://www.cs.waikato.ac.nz/ml/weka/">** Weka**</a>

Weka is a collection of data mining software written in Java and released under the <a href="http://www.gnu.org/licenses/gpl.html">GPL</a>.  While data mining and document classification are closely related fields, I do not see anything that directly relates to AnnGram here.  Perhaps later in the project, I will take a closer look.
**NETtalk** is perhaps the best known [[wiki:artificial neural network]](). It is the result of research carried out in the mid 1980s by [[wiki:Terrence Sejnowski]]() and Charles Rosenberg. The intent behind NETtalk was to construct simplified models that might shed light on the complexity of learning human level cognitive tasks, and their implementation as a connectionist model that could also learn to perform a comparable task.