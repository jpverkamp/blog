---
title: Markov Random Text
date: 2006-12-14 04:55:11
programming/languages:
- Java
---
This is work from my first Winter quarter at <a title="Rose-Hulman Institute of Technology" href="http://www.rose-hulman.edu/">Rose-Hulman Institute of Technology</a>. Basically, we were to use [[wiki:Markov chain|Markov chains]]() to generate a semi-random text that statistically matches an input text. The short version is that you calculate for each sequence of words of a given length (the chain length) what the possible next words are from the given text, each with a given probability. Then you use that to generate a new text, randomly choosing each new word from the aforementioned probabilities. It's really fun to play with and I've got a half dozen or so examples to show you.

<!--more-->

The three parameters are the file name of a plain text file to use as the input, the chain length, and the maximum number of words to output. (If the Markov chain hits a state where there are no more possibilities, it will end early. This should only happen if it generates the end of the text and the last few words are unique.)

(An executable JAR file also containing the source code is available at the end of this post.)

First let's start with the default chain length at 2, with text from the Book of Genesis.

`java -jar markov.jar genesis.txt 2 100`

> In the selfsame day entered Noah, and to every fowl after his mother's death. Then Isaac sowed in that he said, I seek my brethren: tell me, that I shall say, Let us make man in the day of my affliction. And the name of that famine following; for it was well watered every where, before the LORD hath blessed thee since my coming: and now nothing will be servants unto Pharaoh: What God is with you, that I may set mine eyes upon him. And the land of Edom. And he heard that I spake unto me, and fled, ...

We don't even get to the third word before the Markov chains decide to wonder off and talk about Noah instead of the creation of the Earth (and what's with those fowl?) so let's try it again with a chain length of 4:

`java -jar markov.jar genesis.txt 4 100`

> In the beginning God created the heaven and the earth. And it shall come to pass, when Pharaoh shall call you, and shall say, What is your occupation? That ye shall say, Thy servants' trade hath been about cattle from our youth even until now, both we, and also our fathers. They said morever unto Pharaoh, For to sojourn in the land are we come; for thy servants have no pasture for their flocks; for the famine is sore in the land of Shinar. Out of that land went forth Asshur, and builded Nineveh, and the city Rehoboth, and Calah, ...

It manages to stay on target well enough for a sentence, but once you've gotten that far all bets are off and it starts talking about the Pharaoh. Perhaps we should turn it up even more, say to a chain length of 10?

`java -jar markov.jar genesis.txt 10 100`

> In the beginning God created the heaven and the earth. And the earth was without form, and void; and darkness was upon the face of the deep. And the Spirit of God moved upon the face of the waters. And God said, Let there be light: and there was light. And God saw the light, that it was good: and God divided the light from the darkness. And God called the light Day, and the darkness he called Night. And the evening and the morning were the first day. And God said, Let there be a firmament in the midst ...

It turns out that there aren't that many duplicated sequences of length 10, at least not in the first 100 words. But what if we were to go the other way and turn the length down to 1? This means that each word only has to follow a single other word, so it's much more likely to be gibberish.

`java -jar markov.jar genesis.txt 1 100`

> In the flock will serve me in the youngest is with their ears; and with him, and gave each man unto him down unto thy loins; And they separated from thence; that he blessed them: so it unto a daughter of the top may bury thy soul of Israel bowed down his garments in the breasts, and Phichol the tent, at the Hittite, and all that thou shalt thou shouldest say, Drink, my son Jacob. So Jacob stole away my life also of the LORD said to all their wives with my father called the vine was Rachel. Leah went ...

Yeah, that went all of the place, just as expected. So what if we feed in a different sort of text? What about Shakespeare's famous *To Be or Not To Be* speech from Hamlet?

`java -jar markov.jar to-be.txt 2 150`

> To be, or not to be: that is the question: Whether 'tis nobler in the mind to suffer The slings and arrows of outrageous fortune, Or to take arms against a sea of troubles, And by opposing end them? To die: to sleep; To sleep: perchance to dream: ay, there's the rub; For in that sleep of death what dreams may come When we have Than fly to others that we know not of? Thus conscience does make cowards of us all; And thus the native hue of resolution Is sicklied o'er with the pale cast of thought, And enterprises of great pith and moment With this regard their currents turn awry, And lose the name of action. - Soft you now! The fair Ophelia! Nymph, in thy orisons Be all my sins remember'd.

This one actually stopped and much more quickly than the original work did (I wanted to show an example of the algorithm terminating early). Still, it isn't really that much stranger than the original text. What about something completely different in The Wizard of Oz?

`java -jar markov.jar oz.txt 2 100`

> Dorothy lived in Kansas, where I came at once. I am glad of it, for it sounded queer to hear a deep roll of blue at the bottom. The sides were so brilliant in color they almost stood upon the raft and held Toto tightly lest he should awaken; and the Lion sadly. "What makes you a coward?" asked Dorothy, looking at him in surprise. But, seeing they were drawn out of the Munchkins. He was clothed all in an unfriendly way at the river the swift current swept the raft through the soft, fresh grass; and it is very ...

Hmm, perhaps the outcome of someone trying to summarize the [[wiki:Dark Side of the Rainbow]]()?

Anyways, that's more than enough examples for now, so why don't you take it for a spin. Download it, try it out. The JAR contains the source code as well, so if you want to tweak the code, feel free.

**Download:** [markov.jar](/embeds/2006/markov.jar)
