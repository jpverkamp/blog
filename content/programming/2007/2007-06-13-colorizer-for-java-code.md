---
title: Colorizer for Java code
date: 2007-06-13 04:55:28
programming/languages:
- Java
---
Another project we had during my first Winter quarter at <a title="Rose-Hulman Institute of Technology" href="http://www.rose-hulman.edu/">Rose-Hulman</a> was to use a {{< wikipedia "finite state machine" >}} to colorize / perform {{< wikipedia "syntax highlighting" >}} on Java source code. It's easy enough as there are really 3 special cases that we are looking for (strings, comments, and keywords) and we only need 9 states to recognize them all (at least in my implementation).

<!--more-->

All together, we have the following states and transitions:

* If State = `NORMAL`
  * If you read " then output buffer (as `keyword` or `normal`) and State = `STRING`
  * If you read / then output buffer (as `keyword` or `normal`) and State = `NORMAL_SAW_SLASH`
  * If you read ' then output buffer (as `keyword` or `normal`) and State = `NORMAL_CHAR`
      * Otherwise, buffer characters until we see a non-letter; on a non-letter:
  * If the buffer contains a keyword, output as a `keyword`
      * Otherwise, output as `normal`

* If State = `NORMAL_CHAR`
  * If you read \ then State = `NORMAL_CHAR_ESCAPE`
  * If you read ' then output buffer as `normal` and State = `NORMAL` (yes, character literals can be more than one character long, we aren't validating the input)
      * Otherwise, add the character to the buffer

* If State = `NORMAL_CHAR_ESCAPE`
  * Add the character to the buffer and State = `NORMAL_CHAR`

* If State = `STRING`
  * If you read \ then State = `STRING_SAW_BACKSLASH`
  * If you read " then output buffer as `string` and State = `NORMAL`
      * Otherwise, add the character to the buffer

* If State = `STRING_SAW_BACKSLASH`
  * Add the character to the buffer and State = `STRING`

* If State = `NORMAL_SAW_SLASH`
  * If you read / then State = `COMMENT_LINE`
  * If you read * then State = `COMMENT_BLOCK`
      * Otherwise, State = `NORMAL`

* If State = `COMMENT_LINE`
  * If you read \n then output buffer as `comment` and State = `NORMAL`

* If State = `COMMENT_BLOCK`
  * If you read * then State = `COMMENT_BLOCK_SAW_STAR`
      * Otherwise, add the character to the buffer

* If State = `COMMENT_BLOCK_SAW_STAR`
  * If you read / then output buffer as `comment` and State = `NORMAL`
  * If you read * then add the character to the buffer
      * Otherwise, add the character to the buffer and State = `COMMENT_BLOCK`

Perhaps it's not perfect and it can definitely do some strange things on non-valid Java code, but it seems to work well enough. Here's an example on a short HelloWorld program:

```java
/**
 * This HelloWorld program simply prints "Hello World!"
 * to the console when it is run.
 */
class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello World!"); // Display the string.
    }
}
```

All nice and rendered, that looks something like this:

<style type="text/css">
    .syntax * { font-family: monospace; }
    .string { color: red; }
    .comment { color: green; }
    .keyword { color: blue; }
</style>

<pre class="syntax"><span class="comment">/**
 * This HelloWorld program simply prints "Hello World!"
 * to the console when it is run.
 */</span><span class="keyword">
class</span> HelloWorld {
   <span class="keyword"> public</span><span class="keyword"> static</span><span class="keyword"> void</span> main(String[] args) {
        System.out.println(<span class="string">"Hello World!"</span>); <span class="comment">// Display the string.</span>
    }
}
</pre>

Well, that's all I've got. If you want to take the code for a spin, you can download it below. To run it, just type `java -jar colorize.jar HelloWorld` (for example, note the lack of an extension on the parameter). The source code is included in the JAR, so if you feel like modifying it, go for it.

**Download:** {{< figure src="/embeds/2007/colorize.jar" >}}
