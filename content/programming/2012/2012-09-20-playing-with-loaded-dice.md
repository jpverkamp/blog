---
title: Playing with loaded dice
date: 2012-09-20 14:00:45
programming/languages:
- JavaScript
programming/topics:
- Mathematics
---
A couple of months ago, I posted [a simple simulation]({{< ref "2012-07-04-analyzing-the-dice-game.md" >}}) of a loaded dice game <a title="How to use math and win free drinks from your friends" href="http://lifehacker.com/5923186/how-to-use-math-and-win-free-drinks-from-your-friends">posted by Lifehacker</a> (originally from <a href="http://www.datagenetics.com/blog/july12012/index.html" title="DataGenetics: Intransitive Dice">DataGenetics</a>). Today I wanted to take a chance to give everyone a chance to actually play the game.

<!--more-->

The rules are simple. There are three six-sided dice available:

Red: <span style="color: red;">2, 2, 4, 4, 9, 9</span>
Green: <span style="color: green;">1, 1, 6, 6, 8, 8</span>
Blue: <span style="color: blue;">3, 3, 5, 5, 7, 7</span>

You choose one die and then I'll choose one. We'll each roll our die twenty times; for each roll, whoever comes out ahead scores a point. If you get ten or more points, you win (so you win ties). If you don't make ten, I win.

Simple enough, yes? Let's try it. Pick a die below to begin.

<div class="dice" id="red">2</div>
<div class="dice" id="green">1</div>
<div class="dice" id="blue">3</div>

<br />
<input type="checkbox" id="fastMode" /> Fast mode
<br />

<h3>Results</h3>
<div id="results"></div>


<br />

In all likelihood (61% of the time to be exact) I'm going to win. It doesn't matter which die you pick, there is no "best" die. I can always pick the one that has an edge over you. If you're curious to learn why, check out the post on [previous post]({{< ref "2012-07-04-analyzing-the-dice-game.md" >}}) on the subject.

If you'd like to download the source code, you can do so here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/loaded-dice.js" title="loaded dice source">loaded dice source</a>

<script type="text/javascript">// <![CDATA[
jQuery(function($) {
  var userOverall = 0;
  var compOverall = 0;
  var fastMode = false;

  $(".dice").css("display", "inline-block");  
  $(".dice").css("width", "32px");
  $(".dice").css("height", "32px");
  $(".dice").css("border", "2px solid black");
  $(".dice").css("padding", "8px");
  $(".dice").css("text-align", "center");
  $(".dice").css("font", "24px/32px monospace");
  $(".dice").css("color", "white");

  $("#red").css("background-color", "red");
  $("#green").css("background-color", "green");
  $("#blue").css("background-color", "blue");

  var resultDiv = $("#results");
  resultDiv.css("height", "250px");
  resultDiv.css("overflow", "scroll");

  var redRolls = new Array(2, 4, 9);
  var greenRolls = new Array(1, 6, 8);
  var blueRolls = new Array(3, 5, 7);

  function roll(die) {
    if (die == "red")
      return redRolls[Math.floor(Math.random() * 3)];
    else if (die == "green")
      return greenRolls[Math.floor(Math.random() * 3)];
    else
      return blueRolls[Math.floor(Math.random() * 3)];
  }

  function animateDice(userDie, compDie, userScore, compScore, round, frame) {
    if (frame == 1)
      resultDiv.append("**Round " + round + "**<br />");

    if ((fastMode && frame >= 2) || frame >= 20) {
      var userRoll = parseInt($("#" + userDie).text());
      var compRoll = parseInt($("#" + compDie).text());

      if (userRoll > compRoll) userScore += 1;
      else compScore += 1

      resultDiv.append(
        "You rolled <span style='color: " + userDie + ";'>" + userRoll + "</span> and " +
        "I rolled <span style='color: " + compDie + ";'>" + compRoll + "</span>.<br />" +
        "The current score is " + userScore + " to " + compScore + "; " + (userScore >= compScore ? "you're" : "I'm") + " winning.<br /><br />"
      );
      resultDiv.scrollTop(resultDiv[0].scrollHeight);

      if (round == 20) {
        if (userScore >= compScore) {
          resultDiv.append("**You win!**<br /><br />");
          userOverall += 1;
        } else {
          resultDiv.append("**I win!**<br /><br />");
          compOverall += 1;
        }
        resultDiv.append(
          "**So far, you've won " + userOverall + " game" + (userOverall == 1 ? "" : "s") + " and " +
          "I've won " + compOverall + ".**<br />"
        );
        resultDiv.scrollTop(resultDiv[0].scrollHeight);
        $(".dice").click(playGame);
      } else {
        fastMode = $("#fastMode").is(':checked');
        setTimeout(function() { animateDice(userDie, compDie, userScore, compScore, round + 1, 1); }, (fastMode ? 0 : 250));

      }
    } else {
      $("#" + userDie).text(roll(userDie));
      $("#" + compDie).text(roll(compDie));

      setTimeout(function() { animateDice(userDie, compDie, userScore, compScore, round, frame + 1); }, (fastMode ? 0 : 50));
    }
  }

  function playGame(b) {
    $(".dice").unbind("click");
    resultDiv.empty();
    fastMode = $("#fastMode").is(':checked');

    var userPick = b.target.id;
    var compPick;
    if (userPick == "red") compPick = "blue";
    else if (userPick == "green") compPick = "red";
    else compPick = "green";

    resultDiv.append("You picked the <span style='color: " + userPick + ";'>" + userPick + "</span> die.<br />");
    resultDiv.append("I picked the <span style='color: " + compPick + ";'>" + compPick + "</span> die.<br /><br />");

    animateDice(userPick, compPick, 0, 0, 1, 1);
  };

  $(".dice").click(playGame);
});
// ]]></script>
