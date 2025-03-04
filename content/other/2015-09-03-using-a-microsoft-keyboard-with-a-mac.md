---
title: Using a Microsoft keyboard with a Mac
date: 2015-09-03 14:00:49
---
I use a MacBook at work. It's nice, since it's Unix'y enough that I can work in the terminal yet works much better out of the box than Linux. On the downside, the keyboard is less than great for [[wiki:carpal tunnel syndrome]](). So instead, I've been using a <a href="http://smile.amazon.com/Microsoft-Natural-Ergonomic-Keyboard-4000/dp/B000A6PPOK/">Microsoft Ergonomic Keyboard</a>. Then though, you have the difference between Control/Windows/Alt keys and Control/Option/Command.

<!--more-->

First option, tweak the built in OS X keyboard settings:

{{< figure src="/embeds/2015/keyboard-settings.png" >}}

You have to make sure to choose the correct keyboard at the top, but once you have done so you can switch the Option and Command keys without problem (OS X thinks that Alt/Option is one key and the Windows key is Command). The downside to this solution is that every time you unplug the keyboard, the settings are removed. It looks like this has been a problem for <a href="https://discussions.apple.com/thread/2364069?threadID=2364069&tstart=0">a while...</a> So instead, we'll turn to third party tools.

Enter: <a href="https://pqrs.org/osx/karabiner/">Karabiner</a>. So far as keyboard options, it has everything and the kitchen sink. There are *far* more options than the previous version (KeyRemap4MacBook). Long story short, these are the three options that I was looking for:

{{< figure src="/embeds/2015/karabiner-settings.png" >}}


* Don't remap an internal keyboard - Change only the Microsoft keyboard, leave the Mac keyboard alone
* Command_L to Option_L (and vice versa) - swap the command and option keys (I never use the right side, although there are two more options to swap those)


And that's it. It's been working great, persisting through reboot (you have to enable it in the Users &amp; Groups > Login Items settings page) and unplugging the keyboard. If only OS X had this functionality built in...

Bonus round:

I user a drop down terminal (<a href="http://totalterminal.binaryage.com/">TotalTerminal</a>) all of the time. It's great for productivity, since I switch between the console and applications all of the time. For the keyboard shortcut, I want to use the Caps Lock key (who actually uses that to write in all caps?). Unfortunately, you cannot use the Caps Lock key directly. Enter <a href="https://pqrs.org/osx/karabiner/seil.html.en">Seil</a>, a sibling application to Karabiner (although why they're not unified is unclear):

{{< figure src="/embeds/2015/seil-settings.png" >}}

Change that one option (80 is F19, a key unlikely to be used by anything else; there's a list further down) and you're golden.

Edit: Ah ha. What I really wanted was to map my terminal to Caps Lock + A (so that I can use other keys for other applications in the future). I can map Caps Lock to Control, Option, or Command, so I have a few options:


* Control-A: Suboptimal, since Control-A is already used to go to the beginning of the line
* Option-A: Since I'm remapping Option/Command, this will behave differently on the internal and external keyboard
* Command-A: Used to select all text, so that doesn't work


Not so great.

Luckily, we do have an option. Remember how I was only mapping the *left* Control and Options earlier? We can use the right side! If we tell Seil to map Caps Lock to 61 (Right Option) and tell TotalTerminal to open on Option+A, that will do exactly what I expect on both the internal and external keyboard.

Victory!
