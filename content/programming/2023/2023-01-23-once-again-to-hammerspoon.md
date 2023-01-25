---
title: "Once Again, to Hammerspoon"
date: 2023-01-23
programming/languages:
- Lua
programming/topics:
- Dotfiles
- Window Managers
- Productivity
---
Why oh why doesn't macOS have a more powerful window manager...

Once upon a time, I moved from primarily Windows to primarily (at the time) OSX. I missed Aerospace--the ability to use Win+Left/Right to snap windows to half the screen--so I wrote a fix: {{<crosslink "Duplicating AeroSnap on OSX with Hammerspoon">}}. 

Since then, I eventually discovered and moved to [Magnet](https://magnet.crowdcafe.com/) and all was well. 

But more recently, I've been wanting two things:

- a bit more control (once again), to define more arbitrary sizes and keystrokes
- the ability to automatically arrange windows to various [Mission Control](https://support.apple.com/en-us/HT204100) Spaces

And what a journey it's been...

{{< toc >}}

<!--more-->

## What I tried

Not really. Mostly, I sent out a call for what other options there were and tried them out:

* [Spectacle](https://www.spectacleapp.com/) - discontinued 
* [Divvy](https://apps.apple.com/us/app/divvy-window-manager/id413857545?mt=12) - works pretty well, especially for automatically tiling and grid layout, although having to specify the grid with the mouse is suboptimal
* [yabai](https://github.com/koekeishiya/yabai) - requires disabling [SIP](https://support.apple.com/en-us/HT204899), is CLI :+1: but needs another tool for keyboard shortcuts :-1:
* [i3](https://i3wm.org/) / [awesome](https://awesomewm.org/) - automatic tiling; I don't think I'm quite ready for this yet, perhaps another day?
* [Rectangle](https://rectangleapp.com/) - follow up to Spectacle, really is pretty much the same thing as Magnet
* [Rectangle Pro](https://rectangleapp.com/pro) - it's... a separate app? but with "Arrange an entire workspace of apps with just one shortcut." this might do exactly what I want

But finally (for the time being), I came back to [Hammerspoon](https://www.hammerspoon.org/).

What can I say, I'm a tinkerer at heart. Sometimes to my own detriment, I like to be able to take a sane set of defaults and then tweak them how I want. Hammerspoon more or less gives me that. 

So, let's approach my goals. 

## Pushing windows around

First, to snap windows, I implemented a few functions in `~/.hammerspoon/functions/push.lua`:

```lua
-- Move a window to the given coordinates
-- top/left/width/height as a percent of the screen
-- window (optional) the window to move, defaults to the focused window
function push(params)
  local window = params["window"] or hs.window.focusedWindow()
  local windowFrame = window:frame()
  local screen = window:screen()
  local screenFrame = screen:frame()

  local moved = false
  function cas(old, new)
    if old ~= new then 
      moved = true
    end
    return new
  end

  windowFrame.x = cas(windowFrame.x, screenFrame.x + (screenFrame.w * (params["left"] or 0)))
  windowFrame.y = cas(windowFrame.y, screenFrame.y + (screenFrame.h * (params["top"] or 0)))
  windowFrame.w = cas(windowFrame.w, screenFrame.w * (params["width"] or 1))
  windowFrame.h = cas(windowFrame.h, screenFrame.h * (params["height"] or 1))

  window:setFrame(windowFrame)
  return moved
end

function thunk_push(params)
  function thunk()
    push(params)
  end
  return thunk
end

function grid(cell)
  hs.grid.set(hs.window.focusedWindow(), cell)
  return true
end

function thunk_grid(cell) 
  function thunk()
    grid(cell)
  end
  return thunk
end
```

The goal here is to take a table that can contain `top`, `left`, `width`, and/or `height` as numbers 0 to 1 and then apply those to the current window, defaulting `left` and `top` to 0 and `width` and `height` to 1. So if I want a window on the right half, that's `{left: 1/2, width: 1/2}`. Easy enough. `thunk_push` is a wrapper around that that will take the arguments up and wrap them in a {{<wikipedia "thunk">}}--a function with no parameters. 

With that, I can add a bunch of my keybindings to `~/.hammerspoon/keys.lua`:

```lua
-- ⌘ ⌃ ⌥ ⇧

-- show grid
hs.hotkey.bind("⌘⇧", "g",     hs.grid.show)

-- full screens
hs.hotkey.bind("⌘⇧", "up",    thunk_push{width=1, height=1})
hs.hotkey.bind("⌘⇧", "down",  thunk_push{top=1/8, left=1/8, width=3/4, height=3/4})
  
-- half screens
function thunk_left_or_move()
    if not push{left=0, width=1/2} then
        local window = hs.window.focusedWindow()
        local screen = window:screen():previous()
        window:moveToScreen(screen)

        push{left=1/2, width=1/2}
    end
end    
 
function thunk_right_or_move()
    if not push{left=1/2, width=1/2} then
        local window = hs.window.focusedWindow()
        local screen = window:screen():next()
        window:moveToScreen(screen)

        push{left=0, width=1/2}
    end
end

hs.hotkey.bind("⌘⇧", "left",  thunk_left_or_move)
hs.hotkey.bind("⌘⇧", "right", thunk_right_or_move)
hs.hotkey.bind("⌘⇧", "pad8",  thunk_push{height=1/2})
hs.hotkey.bind("⌘⇧", "pad2",  thunk_push{top=1/2, height=1/2})

-- third screens
hs.hotkey.bind("⌘⇧", "pad4",  thunk_push{width=2/3})
hs.hotkey.bind("⌘⇧", "pad6",  thunk_push{width=2/3, left=1/3})

hs.hotkey.bind("⌘⇧", "pad7",  thunk_push{top=0, left=0, width=1/3, height=1/2})
hs.hotkey.bind("⌘⇧", "pad9",  thunk_push{top=0, left=2/3, width=1/3, height=1/2})
hs.hotkey.bind("⌘⇧", "pad1",  thunk_push{top=1/2, left=0, width=1/3, height=1/2})
hs.hotkey.bind("⌘⇧", "pad3",  thunk_push{top=1/2, left=2/3, width=1/3, height=1/2})
```

We'll come back to `⌘⇧ g`. But otherwise, all the rest of them move windows with `⌘⇧` plus a key:

- `left` - move a window to the left half of the screen, if it's already there, move to the previous screen (the right half of it)
- `right` - the same, but right and then the next screen
- `up` - maximize
- `down` - partial center; I originally had this restore windows to what they were before Hammerspoon took over, but I haven't re-implemented that yet
- `numpad`:
  - `4` / `6` - take up the left / right two thirds of the window (to be used with the other keys) 
  - `7` / `9` / `1` / `3` - take up the top left, top right, bottom left, or bottom right third (left/right) of the screen and half (top/bottom); basically so I can tile one big and two small windows

And that's really it. So back to `⌘⇧ g`. That does this:

{{< figure src="/embeds/2023/hammerspoon-grid.png" >}}

Then hit the two keys (top left and bottom right) and the window will snap to that. So I can center 2/3, full height a window with `⌘⇧ g, w, g`. Or set a window to the right 2/3 with ``⌘⇧ g, e, h`. That ... is pretty cool. The specific size of the grid I have defined in `init.lua`, which we'll come back to. 

## Sending windows to the correct screen/desktop

Okay. Now, the second and harder problem. I want to be able to send my windows to specific screens. When my Mac reboots, it restores all of the windows, but has a tendency to just put them wherever. When I use a KVM to switch monitors, sometimes things get scrambled. There's theoretically a 'lock to desktop' option... but I cannot for the life of me get it to work. 

So... how do we do that? 

Well, the [hs.window](https://www.hammerspoon.org/docs/hs.window.html) namespace can list all windows with `hs.window.list`... but that's slow. Instead, what you want is to make an `hs.window.filter` over all windows. Then you can actually subscribe to events on it, specifically `windowCreated` and `windowDestroyed`. I'll use that to keep a local copy of `allWindows` that are opened. 

Second, I now have a `window`, but that doesn't completely help. I need the `window:application():name()` to get the name of the application running (a la `Firefox`) but also `window:title()` for the specific title of specific windows. And unfortunately, there's no built in way (specifically for Firefox) to title windows, so I needed the [Window Titler](https://addons.mozilla.org/en-US/firefox/addon/window-titler/) extension. Oy. Anyways, that's enough to allow me to select a specific window by application, title, or both. 

Third and finally, [hs.spaces](https://www.hammerspoon.org/docs/hs.spaces.html). That will give the ability to control macOS Spaces. It's mentioned in the doc that this is experimental and uses private APIs that Apple could easily change... which I suppose is why most window managers don't seem able to do this. But on the other hand... it does work. So that's pretty cool!

As a side note, they do mention that they looked at the [Yobai](https://github.com/koekeishiya/yabai) source, so despite the note about SIP, that's a good sign I believe. 

Specifically though, I use `hs.screen.find(screenQuery)` to get one of my screens (a monitor) by the type of monitor (luckily one of mine is LG and the other DELL) then `hs.spaces.allSpaces()` with that ID to list all spaces on that screen. That `table` is in order but with IDs created in the order the desktops were created, so rather than directly use the ID, I count through that list and get the ID. 

All that gives me 

And finally, here's the end result, `~/.hammerspoon/functions/rehome.lua`

```lua
windowFilter = hs.window.filter.new()
windowFilter:setDefaultFilter{}
windowFilter:setSortOrder(hs.window.filter.sortByFocusedLast)

-- Keep a local copy of all windows
allWindows = {}
for _, window in pairs(windowFilter:getWindows()) do 
  allWindows[window:id()] = window
end

windowFilter:subscribe("windowCreated", function(window, name, event)
  print("window created", window)
  allWindows[window:id()] = window
end)

windowFilter:subscribe("windowDestroyed", function(window, name, event)
  print("window destroyed", window)
  allWindows[window:id()] = nil
end)

function rehome(windowQuery, screenQuery, spaceIndex, pushArgs)
  for id, w in pairs(allWindows) do
    local name = w:application():name() .. " - " .. w:title()
    if name ~= nil and name:find(windowQuery) then 
      window = w
    end
  end

  if window == nil then
    print("[ERROR in rehome] Window now found", windowQuery)
    return
  end

  local screen = hs.screen.find(screenQuery)
  if screen == nil then
    print("[ERROR in rehome] Screen now found", screenQuery)
    return
  end

  local spaceIDs = hs.spaces.allSpaces()[screen:getUUID()]
  if spaceIndex > #spaceIDs then
    print("[ERROR in rehome] spaceIndex too large", spaceIndex, ">", #spaceIDs)
    return
  end
  local spaceID = spaceIDs[spaceIndex]
  local spaceName = hs.spaces.missionControlSpaceNames()[screen:getUUID()][spaceID]

  print("Moving", window, "to", spaceID, "=", spaceName, "on", screen)
  hs.spaces.moveWindowToSpace(window, spaceID)
  
  if pushArgs ~= nil then
    pushArgs["window"] = window
    push(pushArgs)
  end
end
```

That lets me do something like this:

```lua
rehome("Firefox:Main",  "LG",   3, {left=1/3, width=2/3})
```

That means, take the window with `Firefox:Main` in the title and put it on the `LG` monitor in the 3rd desktop on that screen. After that, call `push` (see above) to move it to the right 2/3 of the screen. 

Nice. Put a few of those together, `~/.hammerspoon/layout.lua`:

```lua
if hs.host.names()[1]:lower():find("mercury") then
    -- Left monitor: LG HDR
    rehome("Firefox:Main",  "LG",   3, {left=1/3, width=2/3})
    rehome("Obsidian",      "LG",   3, {width=1/3, height=1/2})
    rehome("todo",          "LG",   3, {width=1/3, height=1/2, top=1/2})

    -- Right monitor: DELL 
    rehome("Mail",          "DELL", 1)
    rehome("Bitwarden",     "DELL", 1)
    rehome("Cryptomator",   "DELL", 1)

    rehome("Calendar",      "DELL", 2, {width=1, height=1})

    rehome("Firefox:Media", "DELL", 3, {width=1/2})
    rehome("Slack",         "DELL", 3, {left=1/2, width=1/2, height=1/2})
    rehome("Messages",      "DELL", 3, {top=1/2, left=1/2, width=1/2, height=1/2})
end
```

And away we go. 

Firefox, Obsidian, and 'todo' (a VSCode window with my todo workspace open) on one monitor in thirds. On the other, a few background windows (Mail/[Bitwarden](https://bitwarden.com/)/[Cryptomator](https://cryptomator.org/)) moved out of the way, Calendar on the second monitor full screen, and another Firefox (for YouTube etc)/Slack/Messages on the smaller `Dell` monitor. Pretty cool, no? 

I do have this set right now to my computer's hostname (`mercury`) so I can define layouts for more than one machine, but for now, that's all I need. 

## Pulling it all together (init.lua)

And finally, the core/main function that sets this all up, `~/.hammerspoon/init.lua`:

```lua
hs.grid.MARGINX = 0
hs.grid.MARGINY = 0
hs.grid.GRIDWIDTH = 6
hs.grid.GRIDHEIGHT = 2

require "functions/push"
require "functions/rehome"

require "keys"
require "layout"
```

That's where we define the grid, load the two functions mentioned earlier and then add keybindings and a default layout. That's really it. Pretty cool, no? 

Is it perfect? Nah. Does it do exactly what I need? For now, absolutely!

If you like what you see, do let me know. If you have any tricks, absolutely let me know! I'll probably go trolling for Hammerspoon dotfiles at some point (and need to push my to git), but for the moment, this already does everything Magnet did only better. 

Onward!

## One small caveat: next()

Originally, I had a `next` function to match with `push` for moving to the "`next`" monitor. Turns out... `next` is [built in to Lua iterators](https://www.lua.org/manual/2.4/node31.html). 

That... actually managed to crash the built in macOS display manager and make me log in a few times, likely because I ended up causing an infinite loop. Cool {{<wikipedia footgun>}}, yo. 

## Useful docs

Here are the parts of the Hammerspoon docs I used (their docs are for the most part really good):

* [hs.grid](https://www.hammerspoon.org/docs/hs.grid.html)
* [hs.window](https://www.hammerspoon.org/docs/hs.window.html)
* [hs.screen](https://www.hammerspoon.org/docs/hs.screen.html)
* [hs.spaces](https://www.hammerspoon.org/docs/hs.spaces.html)

