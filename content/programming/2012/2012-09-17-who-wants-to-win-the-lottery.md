---
title: Who wants to win the lottery?
date: 2012-09-17 14:00:59
programming/languages:
- JavaScript
programming/topics:
- Mathematics
---
So everyone would love to win the lottery right? Just think of what you could do if you had even $1 million dollars to spend. You could buy a dozen tacos a day at Taco Bell for the rest of your life. And your children's lives. And their children's lives. <a href="http://www.wolframalpha.com/input/?i=1+million+dollars+%2F+%2812+dollar+per+day%29+in+years" title="Wolfram Alpha: 1 million tacos">228 years</a> to be more precise. Or you could pay to send the entire family from <a href="http://www.amazon.com/gp/product/B0001EFTH4/ref=as_li_qf_sp_asin_il_tl?ie=UTF8&camp=1789&creative=9325&creativeASIN=B0001EFTH4&linkCode=as2&tag=jverkampcom-20" title="Amazon: Cheaper by the Dozen">Cheaper by the Dozen</a> to the average state university--even if they each took an <a href="http://www.wolframalpha.com/input/?i=%241+million+%2F+%2413%2C600+%2F+12" title="Wolfram Alpha: $1 million in tuition">additional two years</a> to graduate. And that's just for $1 million. Payouts are usually much higher than that...

So what's the catch?

(If you came here just for the Powerball simulation, it's down at the bottom of the page. <a href="http://blog.jverkamp.com/2012/09/17/who-wants-to-win-the-lottery/#lotteryGametime">Click here</a> to go straight there.)

<!--more-->

Glad you asked. It turns out that the catch is pretty straight forward. All you need to know is a little statistics. Or you could just go to the <a href="http://www.powerball.com/powerball/pb_prizes.asp" title="Powerball odds">Powerball website</a> (for example) and see what odds they've calculated for you. The chart below has the rough odds either for the standard $2 ticket or for the $5 PowerPlay ticket at $4 with tweaked payouts.


| Matching | Powerball? | Prize ($2 ticket) | Prize ($4 ticket)Odds |       Odds        |
|----------|------------|-------------------|-----------------------|-------------------|
|    5     |    Yes     |     JACKPOT!      |       JACKPOT!        | 1 in 175 million  |
|    5     |     No     |    $1 million     |      $2 million       |  1 in 5 million   |
|    4     |    Yes     |   $10 thousand    |     $40 thousand      | 1 in 648 thousand |
|    4     |     No     |       $100        |         $200          | 1 in 19 thousand  |
|    3     |    Yes     |       $100        |         $200          | 1 in 12 thousand  |
|    3     |     No     |        $7         |          $14          |     1 in 360      |
|    2     |    Yes     |        $7         |          $14          |     1 in 706      |
|    1     |    Yes     |        $4         |          $12          |     1 in 110      |
|    0     |    Yes     |        $4         |          $12          |      1 in 55      |


But what does that actually tell you? Well, quite a lot actually. If you take the odds of each chance of winning and multiply it by the payoff (less $2/$4 for the ticket), that will give you the [[wiki:expected value]]() for that payoff. For example, if you only consider the Powerball, the expected value would be:

{{< latex >}}(1/35)(2) + (34/35)(-2) \approx -1.88{{< /latex >}}

So every time you played (if only the Powerball counted) you'd be out an average of $1.88. You may win sometimes (1/35 of the time even), but overall, you'd lose more than you won. What would the payoff actually have to be for it to be a "fair" game--meaning that over time you'd neither make more or lose it?

{{< latex >}}(1/35)(x-2) + (34/35)(-2) \approx 0{{< /latex >}}

{{< inline-latex "x \approx 70" >}}

(Which really makes sense, as you have a flat 1/35 chance of winning and are paying $2 per game.)

But you might think that the other payoffs will even the odds out right? After all, they're all significantly higher payouts. Especially that Jackpot. What if we just took that? Well, taking the current Jackpot of $149 million:

{{< latex >}}(1/175000000)(149000000) + (174999999/175000000)(-2) \approx -1.15{{< /latex >}}

Better actually. But you're still out $1.15 on average per game. Really, the Jackpot has to be over $350 million for the expected value to actually be positive. What's interesting is that sometimes does actually happen. You actually do get people that will go out and buy a lot of tickets around that time, thinking that they're bound to make it big. But there's one more wrinkle to consider... What happens if two people both guess the correct numbers? Well, it turns out that they'd split the jackpot. So instead of that $350 million payout, you'd only get half that. And then there are taxes (quite a lot of them actually--the federal tax alone is about 25% on such winnings).

I guess my point is that trying to get rich by playing the lottery doesn't really make sense. With the sheer numbers of people playing, you're almost certainly going to get some winner--but the odds of it actually being you? Not so good.

But what about the game in general? What is the overall expected value of a Powerball ticket? For that, we have almost everything we need in that chart up there. But what we still need is the chance that you get none of the ones above at all. Luckily, it's easy enough to calculate, just sum up all of the odds above and subtract from one. That ends up giving us... 96.8% or approximately 1 in 1.03. So it's really good odds that you're just going to flat out lose the $2 you put into a ticket. But, now that we have that, we can work out the full expected value of a ticket:

Assuming today's estimated Jackpot of $149 million, we have:

{{< latex >}}1/175223510 * (149000000 - 2) {{< /latex >}}
{{< latex >}}1/5153632.65 * (1000000 - 2) +  {{< /latex >}}
{{< latex >}}1/648975.96 * (10000 - 2) + {{< /latex >}}
{{< latex >}}1/19087.53 * (100 - 2) +  {{< /latex >}}
{{< latex >}}1/12244.83 * (100 - 2) +  {{< /latex >}}
{{< latex >}}1/360.14 * (7 - 2) + {{< /latex >}}
{{< latex >}}1/706.43 * (7 - 2) + {{< /latex >}}
{{< latex >}}1/110.81 * (4 - 2) + {{< /latex >}}
{{< latex >}}1/55.41 * (4 - 2) + {{< /latex >}}
{{< latex >}}1/1.03 * (-2) = -\$0.79 {{< /latex >}}

So every time you buy a Powerball ticket, your going to lose an average of 80 cents.

But what's really interesting is if you play the Powerplay. The odds don't actually change, all that changes is that you're paying twice as much and that all of the non-Jackpot prizes go up. So what's the expected value now?

{{< latex >}}1/175223510 * (149000000 - 4) + {{< /latex >}}
{{< latex >}}1/5153632.65 * (2000000 - 4) + {{< /latex >}}
{{< latex >}}1/648975.96 * (40000 - 4) + {{< /latex >}}
{{< latex >}}1/19087.53 * (200 - 4) + {{< /latex >}}
{{< latex >}}1/12244.83 * (200 - 4) + {{< /latex >}}
{{< latex >}}1/360.14 * (14 - 4) + {{< /latex >}}
{{< latex >}}1/706.43 * (14 - 4) + {{< /latex >}}
{{< latex >}}1/110.81 * (12 - 4) + {{< /latex >}}
{{< latex >}}1/55.41 * (12 - 4) + {{< /latex >}}
{{< latex >}}1/1.03 * (-4) = -\$2.30{{< /latex >}}

Dang. So by buying a Powerplay ticket, you're actually losing about three times as much. Really though, this does make sense. For the expected value to remain the same with twice the pay-in, you'd have to double all of the prizes. And all of the prizes did double... except for the Jackpot. And that $149 million has a bit of weight all to itself.


What about if the Jackpot is different? Well here's a little tool that can help you calculate it:

<table class="table table-striped">
<tr><td>Jackpot:</td><td><input id="lotteryExpectedJackpot" type="text" value="149000000" /><span style="color: red;" id="lotteryExpectedJackpotError" /></tr>
<tr><td>Normal EV:</td><td id="lotteryExpectedNormal"></td></tr>
<tr><td>Powerplay EV:</td><td id="lotteryExpectedPower"></td></tr>
</table>

<p><input type="submit" id="lotteryExpectedButton" value="Calculate expected values" /></p>

<script type="text/javascript">// <![CDATA[
jQuery(function($) {
  function roundCents(val) {
    if (val >= 0)
      return "$" + val.toFixed(2);
    else
      return "-$" + Math.abs(val).toFixed(2);
  }

  function lotteryExpected() {
    $("#lotteryExpectedJackpotError").html("");
    $("#lotteryExpectedNormal").html("");
    $("#lotteryExpectedPower").html("");

    var jackpot = parseInt($("#lotteryExpectedJackpot").val().replace("$", ""));

    if (isNaN(jackpot ) || jackpot < 1) {
      $("#lotteryExpectedJackpotError").html("Please enter a valid Jackpot (a positive integer)");
      return;
    }

    if (jackpot < 1000000) {
      $("#lotteryExpectedJackpotError").html("Jackpots under ~$1M have roughly the same expected values");
    }

    $("#lotteryExpectedNormal").html(roundCents(
      1/175223510 * (jackpot - 2)  +  
      1/5153632.65 * (1000000 - 2) +
      1/648975.96 * (10000 - 2) +
      1/19087.53 * (100 - 2) +
      1/12244.83 * (100 - 2) +
      1/360.14 * (7 - 2) +
      1/706.43 * (7 - 2) +
      1/110.81 * (4 - 2) +
      1/55.41 * (4 - 2) +
      1/1.03 * (-2)));
    $("#lotteryExpectedPower").html(roundCents(
      1/175223510 * (jackpot - 4)  +  
      1/5153632.65 * (2000000 - 4) +
      1/648975.96 * (40000 - 4) +
      1/19087.53 * (200 - 4) +
      1/12244.83 * (200 - 4) +
      1/360.14 * (14 - 4) +
      1/706.43 * (14 - 4) +
      1/110.81 * (12 - 4) +
      1/55.41 * (12 - 4) +
      1/1.03 * (-4)));

  }

  $("#lotteryExpectedButton").click(lotteryExpected);
  lotteryExpected();
});
// ]]></script>

But you don't have to just believe the math. You can try it out for yourself. I've written a simple script below that simulates a series of Powerball drawings. Go ahead and fill out the chart below to try it out. Since the simulation is based on Powerball, you'll need to enter 5 different numbers in the first box, each from 1 through 59. The second box will be your Powerball and should be in the range 1-35. Finally, enter how many tickets you want to buy in the third box (1-100). If you'd rather just choose some random numbers, there's a button for that too.

Feel free to play as long as you want, it doesn't cost you anything. And if anyone actually does get a Jackpot, make sure to let me know. :smile:

<a name="lotteryGametime"></a>
<table class="table table-striped">
<tr><td>Your numbers:</td><td><input id="lotteryNumbers" type="text" value="" /><span id="lotteryNumbersWarning" style="color: red;"></span></tr>
<tr><td>Powerball:</td><td><input id="lotteryPowerball" type="text" value="" /><span id="lotteryPowerballWarning" style="color: red;"></span></tr>
<tr><td>Times to play:</td><td><input id="lotteryPlays" type="text" value="1" /><span id="lotteryPlaysWarning" style="color: red;"></span></tr>
</table>

<p>
<input type="submit" id="lotteryRandomButton" value="Choose for me" />
<input type="submit" id="lotteryPlayButton" value="Play now" />
</p>

<hr />

<div id="lotteryResults"></div>

<script type="text/javascript">// <![CDATA[
jQuery(function($) {
  var overallSpent = 0;
  var overallWon = 0;

  function roll(n) {
    return Math.floor(Math.random() * n) + 1;
  }

  function chooseNumbers() {
    var numbers = new Array(0, 0, 0, 0, 0)
    while (numbers[0] == numbers[1] || numbers[0] == numbers[2] || numbers[0] == numbers[3]
           || numbers[0] == numbers[4] || numbers[1] == numbers[2] || numbers[1] == numbers[3]
           || numbers[1] == numbers[4] || numbers[2] == numbers[3] || numbers[2] == numbers[4]
           || numbers[3] == numbers[4]) {
      numbers = new Array(roll(59), roll(59), roll(59), roll(59), roll(59));
    }
    numbers = numbers.sort();
    return new Array(numbers, roll(35));
  }

  function lotteryRandom() {
    var numbers = chooseNumbers();

    $('#lotteryNumbers').val(numbers[0].join(' '));
    $('#lotteryPowerball').val(numbers[1]);
  }

  function score(yours, theirs) {
    var matches = 0;
    for (var i = 0; i < 5; i++) {
      for (var j = 0; j < 5; j++) {
        if (yours[0][j] == theirs[0][i]) {
          matches += 1
          break;
        }
      }
    }

    var powerball = (yours[1] == theirs[1]);

    var result = 0;
    if (matches == 0 && powerball) result = 4;
    else if (matches == 1 && powerball) result = 4;
    else if (matches == 2 && powerball) result = 7;
    else if (matches == 3 && !powerball) result = 7;
    else if (matches == 3 && powerball) result = 100;
    else if (matches == 4 && !powerball) result = 100;
    else if (matches == 4 && powerball) result = 10000;
    else if (matches == 5 && !powerball) result = 1000000;
    else if (matches == 5 && powerball) result = 150000000;

    return new Array(matches, powerball, result);
  }

  function lotteryPlay() {
    $("#lotteryNumbersWarning").html("");
    $("#lotteryPowerballWarning").html("");
    $("#lotteryPlaysWarning").html("");
    var sanity = true;

    var numbers = new Array(
      $("#lotteryNumbers").val().split(" "),
      $("#lotteryPowerball").val()
    );

    if (numbers[0].length == 5) {
      for (var i = 0; i < 5; i++) {
        numbers[0][i] = parseInt(numbers[0][i]);
        if (isNaN(numbers[0][i]) || numbers[0][i] < 1 || numbers[0][i] > 59) {
          $("#lotteryNumbersWarning").html("Numbers must be in the range 1-59");
          sanity = false;
        }
      }
      numbers[0].sort();

      for (var i = 0; i < 5; i++) {
        for (var j = i + 1; j < 5; j++) {
          if (numbers[0][i] == numbers[0][j]) {
            $("#lotteryNumbersWarning").html("Numbers must be unique");
            sanity = false;
          }
        }
      }
    } else {
      $("#lotteryNumbersWarning").html("You must enter five numbers separated by spaces");
      sanity = false;
    }

    numbers[1] = parseInt(numbers[1]);
    if (isNaN(numbers[1]) || numbers[1] < 1 || numbers[1] > 59) {
      $("#lotteryPowerballWarning").html("You must enter a single number in the range 1-35");
      return;
    }

    var plays = parseInt($("#lotteryPlays").val());

    if (isNaN(plays) || plays < 1 || plays > 100) {
      $("#lotteryPlaysWarning").html("You can only play between 1 and 100 games at a time.");
      sanity = false;
    }

    if (!sanity) return;

    var result = '';
    var total = 0;
    for (var i = 0; i < plays; i++) {
      var winners = chooseNumbers();
      var scores = score(numbers, winners);
      total += scores[2];

      result += "<p>Round " + (i+1) + ": " + winners[0].join(" ") +
        " <span style='color: red;'>" + winners[1] + "</span> -- $" + scores[2] + "</p>\n";
    }

    overallSpent += 2 * plays;
    overallWon += total;

    $("#lotteryResults").html(
      "<p>Overall: $" + (overallSpent) + " spent, $" + (overallWon) + " won, $" + (overallWon - overallSpent) + " net gain/loss</p>" +
      "<p>This round: $" + (2 * plays) + " spent, $" + (total) + " won, $" + (-2 * plays + total) + " net gain/loss</p>" +
      "<hr />" + result
    );
  }

  $("#lotteryRandomButton").click(lotteryRandom);
  $("#lotteryPlayButton").click(lotteryPlay);
});
// ]]></script>

If you'd like, you can download the source here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/lottery.js" title="lottery source">lottery source</a>
