---
title: AnnGram - New GUI
date: 2010-01-28 05:05:36
programming/languages:
- .NET
- C#
programming/topics:
- Computational Linguistics
- Natural Language Processing
- Neural Networks
- Research
---
The old GUI framework just wasn't working out (so far as adding new features went).  So, long story short, I've switched GUI layout.

<!--more-->

**Documents Tab**

{{< figure src="/embeds/2010/new-gui-1.png" >}}

Here's the new document's tab.  As you can see, it still has the ability to add documents and authors (with the same features as earlier), but the logic to do so is now separate from the other functionality.  One neat feature of the new layout is that all of the documents are stored in a SQLite database when closing the program.  This way, you don't have to reload the documents every time you start the program.

**Cosine Similarity**

{{< figure src="/embeds/2010/new-gui-2.png" >}}

Cosine similarity has been split to its own tab with the logic separated from the document panel.  Currently, it can only compare documents (not authors), but I'm working on adding that functionality back in for future use.

**Self-Organizing Map**

Space for the new feature that I'm currently implementing: Self-Organizing Maps!