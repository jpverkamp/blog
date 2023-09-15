---
title: An optimal alphabetizing cipher
date: 2013-01-25 19:45:37
programming/languages:
- Racket
- Scheme
programming/sources:
- Daily Programmer
programming/topics:
- Cryptography
---
Here is <a href="http://www.reddit.com/r/dailyprogrammer/comments/178vsz/012513_challenge_118_hard_alphabetizing_cipher/" title="Challenge #118 [Hard] Alphabetizing cipher">today's /r/dailyprogramming challenge</a>: Generate a simple substitution cipher such that the maximum number of words in a given dictionary of six letter words (there are 7,260 of them) are encoded as strings in alphabetical order.

<!--more-->

For example, if you have the key `jfbqpwcvuamozhilgrxtkndesy`, `a` would may to `j`, `b` to `f` and so on. Thus the word `bakery` would become `fjmprs` (which is alphabetical). It turns out that of the given <a href="http://pastebin.com/9aFn1r27" title="7,260 words with six letters each">7,260 word list</a>, exactly 60 would evaluate to alphabetical orderings. So the score for that cipher key could be thought of as 60. The goal? Find the highest scoring cipher key.

If you'd like to follow along, you can download the entire code <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/alphabetizing-cipher.rkt" title="alphabetizing cipher source on GitHub">from GitHub</a>.

To start with, we want a few utility functions to generate the ciphers from a key and to score them. This is one place where a functional language shines as you can write a function to generate ciphers that returns another function that does the encoding:

```scheme
; create an encoding function from a key
(define (make-cipher key)
  (lambda (plaintext)
    (build-string
     (string-length plaintext)
     (lambda (i)
       (string-ref key (- (char->integer (string-ref plaintext i)) 97))))))
```

Likewise, it's very straight forward to read in the entire word list, to test if a string is sorted, and to score a cipher over and entire word list.

```scheme
; load a word list to score from
(define fn "word-list.txt")
(define word-list
  (with-input-from-file fn
    (lambda () (for/list ([word (in-lines)]) word))))

; test if a word is sorted
(define (word-sorted? word)
  (andmap 
   (lambda (i) (char<=? (string-ref word i) (string-ref word (+ i 1))))
   (range (- (string-length word) 1))))

; score a cipher
(define (score-cipher cipher)
  (for/sum ([word (in-list word-list)])
    (if (word-sorted? (cipher word)) 1 0)))
```

To make sure that things are working well, we can test the provided sample cipher:

```scheme
> (define test-encode (make-cipher "jfbqpwcvuamozhilgrxtkndesy"))
> (test-encode "bakery")
"fjmprs"
> (score-cipher test-encode)
60
```

Everything is as it should be. 

Next, we start getting into solutions. As of the writing, several people on the original thread have found solutions with scores of 474 (over 100 unique solutions), so it seems that's the score to beat (if it's even possible; there's not actually a known solution to the problem). So I'm justing going to throw a few things out there and see what sticks.

* * *

My first idea was to just start with some random solution and repeatedly mutate it (by swapping two random letters, a sort of [[wiki:Monte Carlo algorithm]]()). If the new solution is better, keep it. If not, try again. It turns out that the code for that is pretty straight forward, although I did add some code that after a given number of seconds have passed without a new solution we'll just random start over. Basically, I was seeing a lot of dead ends that it couldn't get out of even with the maximum number of swaps (10).

```scheme
; solve via random swapping
(define (solve/monte-carlo [guess (random-key)]
                           [score -inf.0]
                           [timeout 10]
                           [timer (current-seconds)])

  ; generate a new guess by swapping up to 10 pairs
  (define new-guess (string-copy guess))
  (for ([i (in-range (+ (random 10) 1))])
    (string-swap! new-guess (random 26) (random 26)))
  (define new-score (score-key new-guess))

  ; if we have a new best, report it
  (cond
    [(> (- (current-seconds) timer) timeout)
     (printf "timeout\n")
     (solve/monte-carlo (random-key) -inf.0 timeout (current-seconds))]
    [(> new-score score)
     (printf "~a (~a)\n" new-guess new-score)
     (solve/monte-carlo new-guess new-score timeout (current-seconds))]
    [else
     (solve/monte-carlo guess score timeout timer)]))
```

And here's a sample run of that (with default arguments):

```scheme
> (solve/monte-carlo)
svpakuqixjtmngdbrywozehlcf (9)
svkapgyxijtmqudbrnwozehlcf (27)
svbkopyxinteqldajrwgzmhucf (48)
... 23 lines cut ...
kacyxdwgtbvelufspjzminhrqo (353)
kacyxbwgtdvelufspjzminhrqo (354)
kacyxbwftdvelugspjzminhrqo (369)
timeout
vknreomstqpwihjfgxydczlaub (14)
vkngtomreqpwicjfzxydbslauh (45)
deogtnvrmqpwickxafyjbslzuh (53)
... 35 lines cut ...
jbdvtapenirfgohczuyqmslwxk (402)
jbdvtapenirfgohczuyqkslwxm (404)
jbdvtapenhrfgoiczuyqkslwxm (411)
timeout
rsfykdbjaepmczwnoihxtgulvq (4)
ysfrkdtjaepmczwnoihxbgulvq (5)
ysfmkctjaeprdzwnoihxbgulvq (7)
... 39 lines cut ...
madxvesgqfuhbrickwztnolpyj (430)
kadxvesgqfuhbricmwztnolpyj (435)
kadxvesgqfuhbricmwztnojpyl (451)
timeout
...
```

Basically, it's finding some decently good solutions pretty quickly. (Since the timeout is 10 seconds, each step cannot take longer than that. In actuality, they're only taking a few seconds each to get stuck.) Leave it running long enough and you can find some pretty nice solutions:

```scheme
; found solutions: 

; solve/monte-carlo
; iacxvdreofugkphbtwzsjlmqyn (440)
; hcawtqpemyrkbnfduvzsilgjxo (385)
; hbrxucsenftdmogavwzqipjlyk (425)
; idpwuamrkbqfelgczvyojthnxs (448)
```

But still, nothing reaching even the known optimal case yet.

* * *

My second idea was to directly implement a [[wiki:Hill climbing|hill-climbing solution]](), always greedily choosing the best single step (if there is one). Basically, given a single solution try all 351 (choose one of 26 positions for `i` and a position after that for `j`) possible swaps. If there's a better one, recur on that. If not, shake up the current solution using a method similar to the one used in the `solve/monte-carlo` method.

```scheme
; solve via direct hill climbing
(define (solve/hill-climbing [guess (random-key)]
                             [score -inf.0]
                             [overall-guess guess]
                             [overall-score score])

  ; try every possible single swap
  (define-values (new-guess new-score)
    (for*/fold ([guess guess]
                [score score])
               ([i (in-range 26)]
                [j (in-range i 26)])
      (define new-guess (string-swap guess i j))
      (define new-score (score-key new-guess))
      (if (> new-score score)
          (values new-guess new-score)
          (values guess score))))

  ; update the overall best (will actually print next round)
  (define-values (new-overall-guess new-overall-score)
    (if (>= new-score overall-score)
        (values new-guess new-score)
        (values overall-guess overall-score)))

  ; print out local best values and best overall
  (cond
    [(equal? guess new-guess)
     (printf "local maximum, shuffling\n")
     (for ([i (in-range (+ (random 6) 4))])
       (string-swap! guess (random 26) (random 26)))
     (define new-score (score-key new-guess))
     (printf "~a (~a)  \toverall: ~a (~a)\n" new-guess new-score overall-guess overall-score) 
     (solve/hill-climbing new-guess new-score new-overall-guess new-overall-score)]
    [else
     (printf "~a (~a)  \toverall: ~a (~a)\n" new-guess new-score overall-guess overall-score) 
     (solve/hill-climbing new-guess new-score new-overall-guess new-overall-score)]))
```

It turns out that there are a lot of local maximums for this sort of solution. Just about every time, the new solution will go 2-4 rounds and find a position that can't be improved with a single swap. Here's an example run (yes, the overall output does lag by one, but that doesn't really matter in the long run):

```scheme
> (solve/hill-climbing)
dbawvnpclotefmgisxzqhkjuyr (322)        overall: wlrqujtcmeifhdgpykzaxbsvno (-inf.0)
hdsxvauflcteiogbmwzqnkjpyr (413)        overall: dbawvnpclotefmgisxzqhkjuyr (322)
jdcxvauflgtesohbmwzqnpikyr (432)        overall: hdsxvauflcteiogbmwzqnkjpyr (413)
jdcxvauflgtepohbmwzqnsikyr (433)        overall: jdcxvauflgtesohbmwzqnpikyr (432)
jdcxvauflgteophbmwzqnsikyr (435)        overall: jdcxvauflgtepohbmwzqnsikyr (433)
local maximum, shuffling
ueixvqmflgtdophbjzwkrscayn (43)         overall: ueixvqmflgtdophbjzwkrscayn (435)
idswvfeuoctgaphbjxzqlnkmyr (432)        overall: ueixvqmflgtdophbjzwkrscayn (435)
kdsxvcueoftgaphbjwzqlnimyr (443)        overall: ueixvqmflgtdophbjzwkrscayn (435)
jdsxvcueoftgaphbkwzqlnimyr (447)        overall: kdsxvcueoftgaphbjwzqlnimyr (443)
local maximum, shuffling
jpsbocuegfdvatqxzwnhlkimyr (12)         overall: jpsbocuegfdvatqxzwnhlkimyr (447)
qnarubtdpexcjsfkgvzwhoimyl (252)        overall: jpsbocuegfdvatqxzwnhlkimyr (447)
fnaxubtdrpqcjsekgvzwhoimyl (328)        overall: jpsbocuegfdvatqxzwnhlkimyr (447)
local maximum, shuffling
...
```

So this time we haven't gotten an 'optimal solution' but in other runs I have:

```scheme
; found solutions: 

; solve/hill-climbing
; jdrxvasuobtegphcfwzqknimyl (470)
; ibsxvaruoetfdpgclwzqmnhkyj (470)
; kjpxvuqioesdfngcawzrtmhlyb (473)
; iarzkcfjotudepgbswxqvmhlyn (474)
```

It also works much more quickly. In general, I've gotten to a 474 solution in only a few minutes, although it's never yet gone past that.

* * *

Finally, I have a partial solution. I was wondering if you could optimize the problem specifically for the given 7,260 words rather than trying to solve it in general (as both of the current algorithms will do). To do this, I constructed a 26x26 matrix that shows how often one letter follows another in a word. What we would want to do with that is solve a maximization problem, essentially finding a maximum path through this matrix. It's a bit more complicated than that though as we aren't directly dealing with the words, we're dealing with their encoded forms. I didn't actually make it beyond that point (and all of the solutions that I found with what I did have were *terrible*, with scores hovering around 30 or lower). Still, I think the idea has some merit.

Here's what I have to construct the matrix if anyone feels like working from here:

```scheme
; solve using matrix math
; TODO: unfinished
(define (solve/matrix-math)
  ; count how many times each letter should be after each letter
  (define m
    (for/vector ([i (in-range 26)])
      (for/vector ([i (in-range 26)])
        0)))

  ; increment a cell in that matrix
  (define (@ i j)
    (vector-ref (vector-ref m i) j))
  (define (++ i j)
    (vector-set! (vector-ref m i) j (+ 1 (@ i j))))

  ; add all of the words
  (for* ([word (in-list word-list)]
         [i (in-range (string-length word))]
         [j (in-range i (string-length word))])
    (++ (- (char->integer (string-ref word i)) 97)
        (- (char->integer (string-ref word j)) 97)))

  ; reset diagonal
  (for ([i (in-range 26)])
    (vector-set! (vector-ref m i) i 0))

  m)
```

If you convert that into an HTML table, you'd see values something like this:

<style type="text/css">table#example-matrix tr td { font-size: 6px; margin: 0; padding: 0; }</style>
<table id="example-matrix"><tr><td>0</td><td>141</td><td>335</td><td>603</td><td>1396</td><td>81</td><td>333</td><td>227</td><td>761</td><td>14</td><td>264</td><td>735</td><td>325</td><td>875</td><td>397</td><td>200</td><td>19</td><td>899</td><td>1222</td><td>663</td><td>315</td><td>145</td><td>114</td><td>61</td><td>365</td><td>68</td></tr><tr><td>328</td><td>0</td><td>81</td><td>197</td><td>536</td><td>21</td><td>105</td><td>76</td><td>278</td><td>7</td><td>73</td><td>300</td><td>60</td><td>209</td><td>266</td><td>26</td><td>5</td><td>340</td><td>395</td><td>185</td><td>206</td><td>9</td><td>51</td><td>14</td><td>131</td><td>24</td></tr><tr><td>452</td><td>53</td><td>0</td><td>220</td><td>765</td><td>25</td><td>74</td><td>330</td><td>309</td><td>2</td><td>235</td><td>292</td><td>130</td><td>265</td><td>418</td><td>130</td><td>12</td><td>437</td><td>542</td><td>296</td><td>219</td><td>49</td><td>38</td><td>15</td><td>178</td><td>16</td></tr><tr><td>232</td><td>35</td><td>81</td><td>0</td><td>515</td><td>25</td><td>120</td><td>41</td><td>280</td><td>5</td><td>46</td><td>160</td><td>89</td><td>191</td><td>212</td><td>48</td><td>1</td><td>279</td><td>421</td><td>168</td><td>123</td><td>30</td><td>35</td><td>10</td><td>128</td><td>11</td></tr><tr><td>510</td><td>76</td><td>197</td><td>898</td><td>0</td><td>54</td><td>137</td><td>126</td><td>427</td><td>5</td><td>60</td><td>457</td><td>182</td><td>554</td><td>296</td><td>118</td><td>6</td><td>1052</td><td>1301</td><td>570</td><td>160</td><td>37</td><td>55</td><td>64</td><td>323</td><td>19</td></tr><tr><td>189</td><td>18</td><td>61</td><td>120</td><td>311</td><td>0</td><td>61</td><td>38</td><td>198</td><td>5</td><td>37</td><td>243</td><td>66</td><td>115</td><td>153</td><td>5</td><td>3</td><td>216</td><td>222</td><td>162</td><td>138</td><td>11</td><td>16</td><td>19</td><td>107</td><td>14</td></tr><tr><td>248</td><td>29</td><td>33</td><td>139</td><td>513</td><td>20</td><td>0</td><td>105</td><td>207</td><td>1</td><td>7</td><td>206</td><td>79</td><td>178</td><td>203</td><td>37</td><td>0</td><td>254</td><td>394</td><td>181</td><td>133</td><td>23</td><td>23</td><td>1</td><td>108</td><td>18</td></tr><tr><td>338</td><td>29</td><td>54</td><td>193</td><td>552</td><td>17</td><td>60</td><td>0</td><td>284</td><td>5</td><td>82</td><td>196</td><td>114</td><td>208</td><td>272</td><td>57</td><td>0</td><td>313</td><td>388</td><td>159</td><td>112</td><td>27</td><td>36</td><td>11</td><td>163</td><td>15</td></tr><tr><td>362</td><td>63</td><td>346</td><td>457</td><td>1194</td><td>76</td><td>445</td><td>189</td><td>0</td><td>10</td><td>164</td><td>504</td><td>233</td><td>997</td><td>261</td><td>128</td><td>14</td><td>512</td><td>1040</td><td>535</td><td>141</td><td>73</td><td>17</td><td>42</td><td>240</td><td>32</td></tr><tr><td>57</td><td>10</td><td>16</td><td>32</td><td>89</td><td>2</td><td>22</td><td>7</td><td>61</td><td>0</td><td>25</td><td>36</td><td>15</td><td>48</td><td>55</td><td>14</td><td>0</td><td>47</td><td>63</td><td>36</td><td>59</td><td>3</td><td>6</td><td>3</td><td>17</td><td>1</td></tr><tr><td>72</td><td>9</td><td>9</td><td>132</td><td>405</td><td>9</td><td>38</td><td>32</td><td>137</td><td>3</td><td>0</td><td>82</td><td>19</td><td>104</td><td>47</td><td>19</td><td>0</td><td>137</td><td>206</td><td>63</td><td>36</td><td>11</td><td>2</td><td>4</td><td>114</td><td>3</td></tr><tr><td>472</td><td>35</td><td>143</td><td>371</td><td>1075</td><td>36</td><td>157</td><td>99</td><td>468</td><td>1</td><td>126</td><td>0</td><td>166</td><td>366</td><td>316</td><td>81</td><td>8</td><td>351</td><td>705</td><td>353</td><td>247</td><td>70</td><td>43</td><td>30</td><td>361</td><td>25</td></tr><tr><td>350</td><td>132</td><td>104</td><td>181</td><td>577</td><td>13</td><td>78</td><td>71</td><td>347</td><td>7</td><td>60</td><td>242</td><td>0</td><td>273</td><td>240</td><td>145</td><td>6</td><td>232</td><td>474</td><td>192</td><td>164</td><td>15</td><td>12</td><td>14</td><td>143</td><td>13</td></tr><tr><td>268</td><td>30</td><td>191</td><td>354</td><td>786</td><td>38</td><td>451</td><td>97</td><td>272</td><td>8</td><td>153</td><td>249</td><td>91</td><td>0</td><td>219</td><td>46</td><td>4</td><td>310</td><td>696</td><td>368</td><td>138</td><td>30</td><td>36</td><td>20</td><td>207</td><td>19</td></tr><tr><td>403</td><td>107</td><td>198</td><td>443</td><td>1043</td><td>43</td><td>246</td><td>152</td><td>534</td><td>8</td><td>138</td><td>449</td><td>211</td><td>661</td><td>0</td><td>147</td><td>10</td><td>660</td><td>992</td><td>461</td><td>372</td><td>87</td><td>167</td><td>54</td><td>241</td><td>34</td></tr><tr><td>340</td><td>20</td><td>121</td><td>209</td><td>607</td><td>18</td><td>89</td><td>135</td><td>387</td><td>3</td><td>68</td><td>280</td><td>52</td><td>293</td><td>295</td><td>0</td><td>5</td><td>366</td><td>422</td><td>277</td><td>153</td><td>22</td><td>27</td><td>21</td><td>161</td><td>12</td></tr><tr><td>38</td><td>0</td><td>7</td><td>6</td><td>56</td><td>0</td><td>3</td><td>8</td><td>40</td><td>0</td><td>10</td><td>8</td><td>3</td><td>19</td><td>13</td><td>1</td><td>0</td><td>26</td><td>34</td><td>31</td><td>102</td><td>2</td><td>2</td><td>0</td><td>8</td><td>3</td></tr><tr><td>626</td><td>113</td><td>205</td><td>423</td><td>1030</td><td>60</td><td>208</td><td>171</td><td>677</td><td>6</td><td>140</td><td>365</td><td>225</td><td>498</td><td>444</td><td>160</td><td>9</td><td>0</td><td>1073</td><td>424</td><td>255</td><td>77</td><td>75</td><td>24</td><td>335</td><td>32</td></tr><tr><td>398</td><td>40</td><td>179</td><td>292</td><td>808</td><td>33</td><td>108</td><td>285</td><td>389</td><td>3</td><td>126</td><td>311</td><td>130</td><td>296</td><td>277</td><td>170</td><td>17</td><td>409</td><td>0</td><td>523</td><td>179</td><td>55</td><td>69</td><td>24</td><td>240</td><td>13</td></tr><tr><td>362</td><td>43</td><td>145</td><td>221</td><td>783</td><td>21</td><td>106</td><td>257</td><td>407</td><td>1</td><td>88</td><td>258</td><td>103</td><td>288</td><td>333</td><td>88</td><td>3</td><td>501</td><td>619</td><td>0</td><td>152</td><td>20</td><td>52</td><td>24</td><td>255</td><td>23</td></tr><tr><td>305</td><td>107</td><td>189</td><td>332</td><td>791</td><td>31</td><td>190</td><td>141</td><td>378</td><td>6</td><td>145</td><td>382</td><td>222</td><td>459</td><td>140</td><td>186</td><td>2</td><td>463</td><td>724</td><td>442</td><td>0</td><td>30</td><td>32</td><td>21</td><td>175</td><td>24</td></tr><tr><td>100</td><td>5</td><td>21</td><td>49</td><td>306</td><td>2</td><td>32</td><td>10</td><td>154</td><td>0</td><td>4</td><td>87</td><td>14</td><td>90</td><td>92</td><td>8</td><td>0</td><td>138</td><td>192</td><td>70</td><td>41</td><td>0</td><td>7</td><td>9</td><td>39</td><td>4</td></tr><tr><td>172</td><td>7</td><td>28</td><td>132</td><td>335</td><td>16</td><td>71</td><td>93</td><td>204</td><td>0</td><td>46</td><td>119</td><td>33</td><td>158</td><td>57</td><td>36</td><td>0</td><td>195</td><td>198</td><td>91</td><td>23</td><td>22</td><td>0</td><td>4</td><td>92</td><td>6</td></tr><tr><td>23</td><td>1</td><td>12</td><td>13</td><td>56</td><td>1</td><td>13</td><td>2</td><td>55</td><td>0</td><td>1</td><td>22</td><td>4</td><td>36</td><td>25</td><td>7</td><td>0</td><td>25</td><td>60</td><td>30</td><td>9</td><td>1</td><td>0</td><td>0</td><td>20</td><td>0</td></tr><tr><td>94</td><td>12</td><td>36</td><td>67</td><td>171</td><td>2</td><td>55</td><td>34</td><td>114</td><td>0</td><td>19</td><td>84</td><td>54</td><td>132</td><td>101</td><td>46</td><td>1</td><td>94</td><td>190</td><td>63</td><td>32</td><td>6</td><td>17</td><td>10</td><td>0</td><td>2</td></tr><tr><td>38</td><td>7</td><td>11</td><td>25</td><td>111</td><td>3</td><td>18</td><td>9</td><td>67</td><td>1</td><td>5</td><td>28</td><td>10</td><td>46</td><td>47</td><td>4</td><td>0</td><td>39</td><td>73</td><td>19</td><td>9</td><td>1</td><td>0</td><td>0</td><td>33</td><td>0</td></tr></table>

(Yes it's tiny.)

Basically, they're pretty chaotic at first glance, but there are definite pockets of both higher and lower values.

If I get some more time, I'll see what more I can do with this solution, but for now, that's what I have. 

Well that's all I have for now. Like always, the entire code (which will also be updated if I work more on this) is availble on GitHub:
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/alphabetizing-cipher.rkt" title="alphabetizing cipher source on GitHub">alphabetizing cipher source</a>

**Edit 28 Jan 2013:**

An idea I've been working on is to generate a graph of pairwise compatible words (any word that doesn't have *a* before *b* in one word and *b* before *a* in the other). If we can find that, the [[wiki:Maximal clique|maximum clique]]() should (theoretically) be the exact set of words generated by an optimal cipher.

Unfortunately, finding the maximum clique of a graph is NP-hard. And with a 7260 node dense graph with quite a lot of maximal yet non-maximum cliques, it takes a really long time to run. I've been running the [[wiki:Bron-Kerbosch algorithm|Bron-Kerbosch algorithm]]() (with pivot) on it since last night, but the largest clique so far is only 44 items. It still hasn't gone beyond cliques that have to include the first three words.

Does anyone have any thoughts? Is there anything that would have to be added to the definition of compatible? words to make it work? Any quicker way to find maximum cliques?

(Here's a copy of the graph in the <a href="http://logic.pdmi.ras.ru/~basolver/dimacs.html" title="DIMACS format">binary DIMACS format</a> if it would be helpful: <a href="http://jverkamp.com/temp/graph.b.clq" title="Binary DIMACS format of pairwise compatible words">graph.b.clq</a>, 3.1 mb)

**Edit 31 Jan 2013:**

Still running, although the best clique so far is only 49 nodes. I doubt this will complete while I still have access to the machine it's running on, but I guess there's no harm in letting it go.