---
title: Making Fish Shell Smile
date: 2018-01-12
programming/languages:
- Fish
programming/topics:
- Command line
- Dotfiles
- Shell Scripting
---
When working in a shell, from time to time, I need to know if a command succeeded or failed. Sometimes, it's easy:

```fish
$ make noise

make: *** No rule to make target `noise'.  Stop.
```

Sometimes, less so:

```fish
$ grep frog podcasts.json > podcasts-about-frogs.txt
```

Since, alas, I don't have any podcasts about frogs, that command would fail silently. But that's fixable!

```fish
$ grep frog podcasts.json > podcasts-about-frogs.txt

$ # Bash/Zsh
$ echo $?
1

$ # Fish
$ echo $status
1
```

<!--more-->

A bit annoying, but functional. We can do better though. My current shell of choice is [Fish](https://fishshell.com/). I have a few different things available on my prompt, including if the last command succeeded or failed:

```fish
><> ^_^ jp@neptune {git master} ~/Projects/blog
$ false


><> ;_; jp@neptune {git master} ~/Projects/blog
$
```

Things to note:

- A cute ascii art fish `><>`, just because
- A happy (`^_^`) or sad (`;_;`) face depending on the last command
- My current username (`jp`) and hostname (`neptune`)
- If we're in a [git repo](https://git-scm.com/), the current branch
- The current directory

Fish renders the prompt by calling the function `fish_prompt`, which can be found at `~/.config/fish/functions/fish_prompt.fish`:

First, render the fish and capture the `$status` (so future commands in this function don't confuse it):

```fish
function fish_prompt
    set last_status $status
    printf "\n><> "
```

Then, we'll render either a smiley or sad face based on the last command:

```fish
    # Different status if the last command was successful
    if test $last_status -eq 0
        set_color green
        printf "^_^ "
    else
        set_color red
        printf ";_; "
    end
```

As an added bonus, the face is either green or red, which honestly I'm more likely to notice at a glance than the picture itself. It's much easier (IMO) to implement colors in Fish than in Bash with command sequences.

Next up, the current machine:

```fish
    # Where am I (current user, machine, git, and path)
    set_color purple
    printf (whoami)
    set_color white
    printf "@"
    set_color yellow
    printf (hostname -s)
```

And then git status, but only if we're currently in a git repo:

```fish
    # Git status
    set git_branch (git rev-parse --abbrev-ref HEAD ^ /dev/null)
    if test "$git_branch" != ""
        set_color white
        printf " {"
        set_color cyan
        printf "git $git_branch"
        set_color white
        printf "}"
    end
```

This specifically checks to see if the `$git_branch` returns anything. If not, it just skips this section.

Then, the current directory:

```fish
    set_color green
    printf " %s" (string replace $HOME '~' (pwd))
```

This also replaces my home directory with `~`, which is fairly standard and makes paths shorter (although with a two character username, this isn't an issue on most systems).

Finally, close off the prompt on the next line:

```fish
    # Actual prompt
    set_color white
    printf "\n\$ "
end
```

Probably start off a holy war with my two line prompt, but it's been working great for me, so ... that's what I use. :smile:

Here it is in all it's colorful color:

{{< figure src="/embeds/2018/fish-smile.png" >}}

As an added bonus, I like to have one extra empty line after the prompt and before the command output (as you may have noticed). You can do that by defining another function:

```fish
function whitespace_after_prompt --on-event fish_preexec
    printf "\n"
end
```

I have this in my main Fish config file (`~/.config/fish/config.fish`), but it could theoretically be in a function file as well.

And that's it. The entire function (and the rest of my configs) are available [on GitHub](https://github.com/jpverkamp/dotfiles/blob/master/fish/functions/fish_prompt.fish) if you're so interested. If you'd rather [Zsh](https://www.zsh.org/) (which I used prior to Fish), my config for a very similar prompt is still available [on GitHub as well](https://github.com/jpverkamp/dotfiles/blob/master/zsh.d/20-prompt.zsh).
