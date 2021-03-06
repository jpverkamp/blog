---
title: Duplicating AeroSnap on OSX with Hammerspoon
date: 2016-02-08
programming/languages:
- Lua
programming/topics:
- Dotfiles
---
Relatively recently, I switched my last Windows machine over to OSX. For the most part, it's been great. One bit of functionality that I've been missing though is AeroSnap. Specifically the ability to use a keyboard shortcut to move windows to the left/right half of a monitor.

<!--more-->

For a while, <a href="https://www.boastr.net/">BetterTouchTool</a> provided that functionality for me, among it's many (many) other options. Unfortunately (for me, it's a good move for them), the author(s) of BetterTouchTool are now moving to a paid model. Since I use only a tiny fraction of the functionality, I decided to see if there were other options.

The first thing that I stumbled across was <a href="https://github.com/fikovnik/ShiftIt">ShiftIt</a>. It actually has exactly the functionality that I wanted and was configurable enough that I could tweak the keybindings to what my fingers already expected them to be. If you don't particularly want to tweak the functionality and just want AeroSnapesqe functionality, this is probably a good enough option.

Me though? I love to tweak things.

With unusually precient timing, Lifehacker posted an article about <a href="http://www.hammerspoon.org/">Hammerspoon</a>: <a href="http://lifehacker.com/hammerspoon-is-powerful-free-automation-tool-for-os-x-1757351485">Hammerspoon Is Powerful, Free Automation Tool for OS X</a>

Interesting.

After a bit of digging, I found that their <a href="http://www.hammerspoon.org/go/">Getting Started</a> document actually has an example that does exactly what I want to do: <a href="http://www.hammerspoon.org/go/#winresize">Window sizing</a> Shiny!

A bit of tweaking and this is what I ended up with:

### `.hammerspoon/init.lua`

Base code, handles reloading, locking, and loading modules

```lua
-- Reload hammerspoon configs
hs.hotkey.bind({"cmd", "ctrl"}, "R", function()
    hs.reload()
end)
hs.alert.show("Config loaded")

-- Lock
hs.hotkey.bind({"cmd", "ctrl"}, 'L', function()
    os.execute("open '/System/Library/Frameworks/ScreenSaver.framework/Versions/A/Resources/ScreenSaverEngine.app'")
end)

require('aerosnap')
```

The first is another example from their documentation of bind a keyboard shortcut to reloading the Hammerspoon documentation. The second is another keyboard shortcut I missed from Windows: the ability to lock the screen without logging out (the normal lock functionality disables networking and thus things like remote login).

### `.hammerspoon/aerosnap/init.lua`

```lua
-- Aerosnap helper functions to get and set current window parameters
function aerosnap_get_parameters()
    local window = hs.window.focusedWindow()
    local frame = window:frame()
    local screen = window:screen()
    local bounds = screen:frame()

    return window, frame, bounds
end

-- Aerosnap help to move a window to a specified position
function aerosnap_move_window(x, y, w, h)
    local window, frame, bounds = aerosnap_get_parameters()

    frame.x = x
    frame.y = y
    frame.w = w
    frame.h = h

    window:setFrame(frame)
end

-- Save the current window's position so we can restore it
function aerosnap_save_window()
    local window, frame, bounds = aerosnap_get_parameters()
    saved_window_sizes = saved_window_sizes or {}
    saved_window_sizes[window:id()] = {x = frame.x, y = frame.y, w = frame.w, h = frame.h}
end

-- Aerosnap move window to the left half
hs.hotkey.bind({"cmd", "ctrl"}, "Left", function()
    local window, frame, bounds = aerosnap_get_parameters()
    aerosnap_save_window()
    aerosnap_move_window(bounds.x, bounds.y, bounds.w / 2, bounds.h)
end)

-- Aerosnap move window to the right half
hs.hotkey.bind({"cmd", "ctrl"}, "Right", function()
    local window, frame, bounds = aerosnap_get_parameters()
    aerosnap_save_window()
    aerosnap_move_window(bounds.x + bounds.w / 2, bounds.y, bounds.w / 2, bounds.h)
end)

-- Aerosnap maximize current window, saving size to restore
hs.hotkey.bind({"cmd", "ctrl"}, "Up", function()
    local window, frame, bounds = aerosnap_get_parameters()
    aerosnap_save_window()
    aerosnap_move_window(bounds.x, bounds.y, bounds.w, bounds.h)
end)

-- Restore the last saved window configuration for a window (basically, a one level undo)
hs.hotkey.bind({"cmd", "ctrl"}, "Down", function()
    local window, frame, bounds = aerosnap_get_parameters()

    old_bounds = saved_window_sizes[window:id()]
    if old_bounds ~= nil then
        aerosnap_move_window(old_bounds.x, old_bounds.y, old_bounds.w, old_bounds.h)
        saved_window_sizes[window:id()] = nil
    end
end)
```

Basically, I took the same functionality that they had in the demo and factored out the functionality that gets the current window / sets the new sizes. The other interesting bit is the `aerosnap_save_window` function, which allows you to restore the size of a window you had just maximized. This does have something of a memory leak (in that it never clears up closed windows), but the amount should be small enough that it doesn't overly matter.

And that's it. My full configs are available in my dotfiles (if I make any further tweaks or add more functionality): <a href="https://github.com/jpverkamp/dotfiles/tree/master/hammerspoon">hammerspoon configs</a>

I'm looking forward to seeing what else I can do with Hammerspoon. You can get fairly extensive: <a href="https://github.com/tstirrat/hammerspoon-config">example Hammerspoon config</a>.

Also, if you want an alternative to Hammerspoon with what looks like a more modular approach, check out <a href="https://github.com/sdegutis/mjolnir">Mjolnir</a>. It appears that Hammerspoon is a fork of Mjolnir, so their configs are rather similar.
