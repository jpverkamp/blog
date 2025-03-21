---
title: Automatically uploading files
date: 2016-06-03
programming/languages:
- Python
---
Quick post today. I was working on a website where I have a live server running the code on another machine. I wanted to write a quick script that would copy any files I changed to the remote machine. This is something you can do automatically in most IDEs, but I wanted something both a bit lighter weight and to have the excuse to write something myself.

<!--more-->

Basically, I'm going to wrap <a href="https://fsnotify.org/">fsnotify</a> with a quick queue that can keep track of files as they're changed and upload them in order.

First, the functionality that can run an arbitrary command (at least one that returns a list of filenames) and put any files found into a queue (we'll see why in a moment):

```python
sync_queue = queue.Queue()

def sync_command(command):
    process = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE)
    for line in process.stdout:
        for file in line.decode().strip().split():
            sync_queue.put(file)
```

And then the other half--a thread that can take those files off the queue and automatically upload them to a remote server:

```python
def do_sync():
    while True:
        path = sync_queue.get()
        local_path = path.replace(local_directory, '').lstrip('/')
        remote_path = remote_directory.rstrip('/') + '/' + local_path

        print('[{} remaining] {} ... '.format(sync_queue.qsize(), local_path), end = '')
        sys.stdout.flush()

        subprocess.check_call('scp "{local_path}" "{remote_host}:{remote_path}"'.format(
            local_path = local_path,
            remote_host = remote_host,
            remote_path = remote_path
        ), shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

        print('done')

# Start up the sync thread
sync_thread = threading.Thread(target = do_sync)
sync_thread.daemon = True
sync_thread.start()
```

And that's all we need. We can run a trio of commands to automatically sync any changes that we've made on a `git` branch plus any we make going forward:

```python
# Sync any differences on the current branch (first changed, then new files)
sync_command('git diff --name-only master')
sync_command('git ls-files --others --exclude-standard')

# Sync any changes to files as they happen
sync_command('fswatch -r -e ".git" .')
```

And that's it. `fswatch` really does most of the work, but it's a nice wrapper that will continually sync files until you tell it to quit.

It's useful enough that I already put it in my `dotfiles` repo: <a href="https://github.com/jpverkamp/dotfiles/blob/master/bin/sync">sync</a>.
