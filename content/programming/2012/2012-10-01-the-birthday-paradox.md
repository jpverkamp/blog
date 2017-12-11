---
title: The Birthday Paradox
date: 2012-10-01 14:00:40
programming/languages:
- JavaScript
programming/topics:
- Mathematics
---
Probability can be a bit counter-intuitive at times. Take for example, the {{< wikipedia page="Birthday paradox" text="birthday problem / paradox" >}}: how many people do you need in a room to have a 50/50 chance that two share the same birthday?

<!--more-->

Turns out, it's not as many as you might think: you only need 23.

Why? Math!

If you have one person, it's guaranteed that you won't have duplicated birthdays. If you have two, there is a 1/365 chance (we're going to ignore {{< wikipedia page="February 29" text="Leap Days" >}} for the time being). You can think of it by randomly choosing the first birthday then finding the chance of matching that.

The math starts getting a bit more interesting when you have three people. Rather than directly calculating the problem, consider the inverse. Start with the chance that the second person doesn't match the first and then add the chance that the third doesn't match either the first or second:

{{< latex >}}(1 - 1/365) * (1 - 2/365) \approx 99.2\%{{< /latex >}}

One minus that is the chance that any of the three share a birthday:

{{< latex >}}1 - ((1 - 1/365) * (1 - 2/365)) \approx 0.8\%{{< /latex >}}

Then if you have four:

{{< latex >}}1 - ((1 - 1/365) * (1 - 2/365) * (1 - 3/365)) \approx 1.6\%{{< /latex >}}

Which generalizes pretty directly to any number of people *n*:

{{< latex >}}B(n) = 1 - \prod_{i=1}^{(n-1)}(1-\frac{i}{365}){{< /latex >}}

Working out several interesting values of *n*:


|   n    |   B(n)    |
|--------|-----------|
|   1    |   0.8%    |
|   2    |   1.6%    |
|   3    |   2.7%    |
|   5    |   5.6%    |
|   10   |   11.7%   |
|   20   |   41.1%   |
| **23** | **50.7%** |
|   30   |   70.6%   |
|   50   |   97.0%   |
|   57   |   99.0%   |
|  100   |   99.9%   |
|  366   |   100%    |


So it turns out, you only need 23 people to get a 50/50 chance of two sharing the same birthday. That's about what you'd seen in the average classroom.
Not what you'd probably expect, but the math holds it out. There's also another interesting factor going on that once you have 367 people in a room (one more than the possible number of days in a year, then are guaranteed to have a match). That's from the {{< wikipedia "pigeonhole principle" >}}, but hopefully it's more intuitive as well. If you have 366 people spread out all over the year, even on February 29, then when could the 367's birthday possibly be to *not* overlap? Exactly.

But you don't have to take my word for it, the math should stand by itself. And if that's not enough, here's a quick script that might just help to convince you. Just click the button to generate a random room of 23 people. Run it enough times and you should see that 50/50 split.


<table class="table table-striped">
<tr>
<td style="text-align: right;">Number of birthdays:</td>
<td><input id="numberOfBirthdays" value="23" /></td>
<td><button style="width: 200px;" id="runBirthdays">Random birthdays!</button></td>
</tr>
<tr>
<td style="text-align: right;">Repeat:</td>
<td><input id="repeatCount" value="1"></td>
<td><button style="width: 200px;" id="repeatBirthdays">Run multiple</button></td>
</tr>
</table>

<button style="width: 200px;" id="viewHideSource">View/Hide Source</button>
<button style="width: 200px;" id="resetBirthdays">Reset</button>

<p id="result"></p>

```javascript
var results = {};

function randomBirthday() {
	var d = new Date((new Date().getTime()) +
		Math.floor(Math.random() * 365) *
		24 * 60 * 60 * 1000);
	d.setHours(0);
	d.setMinutes(14);
	d.setSeconds(0);
	d.setMilliseconds(0);
	return d;
}

function date_sort(date1, date2) {
	if (date1 > date2) return 1;
	if (date1 < date2) return -1;
	return 0;
};

function b(n) {
	var prod = 1;
	for (var i = 1; i < n; i++)
		prod *= (1 - i / 365);
	return Math.round(10000 * (1 - prod)) / 100;
}

function doRun(n) {
	var dates = new Array();
	for (var i = 0; i < n; i++)
		dates.push(randomBirthday());

	dates.sort(date_sort);

	var found = false;
	for (var i = 0; i < n; i++)
		dates[i] = dates[i].toLocaleDateString();

	for (var i = 0; i < n; i++) {
		if ((i > 0 && dates[i] == dates[i - 1]) ||
				(i < n - 1 && dates[i] == dates[i + 1])) {
			found = true;
			break;
		}
	}

	if (!(n in results)) results[n] = {runs: 0, good: 0};
	results[n].runs += 1;
	if (found) results[n].good += 1;
}
```

Or download it here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/birthday-paradox.js" title="Birthday Paradox source">Birthday Paradox source</a>


<p id="result"></p>

<script>
jQuery(function($) {
	var results = {};

	function randomBirthday() {
		var d = new Date((new Date().getTime()) + Math.floor(Math.random() * 365) * 24 * 60 * 60 * 1000);
		d.setHours(0);
		d.setMinutes(14);
		d.setSeconds(0);
		d.setMilliseconds(0);
		return d;
	}

	function date_sort(date1, date2) {
		if (date1 > date2) return 1;
		if (date1 < date2) return -1;
		return 0;
	};

	function b(n) {
		var prod = 1;
		for (var i = 1; i < n; i++)
			prod *= (1 - i / 365);
		return Math.round(10000 * (1 - prod)) / 100;
	}

	function doRun(silent) {
		var result = '';
		silent = silent || false;

		var n = $("#numberOfBirthdays").val();
		if (isNaN(n) || n < 1) {
			if (!silent) result = '<p class="warning">Invalid number of birthdays, defaulting to 23.</p>\n';
			n = 23;
		}

		var dates = new Array();
		for (var i = 0; i < n; i++)
			dates.push(randomBirthday());

		dates.sort(date_sort);

		var found = false;
		for (var i = 0; i < n; i++)
			dates[i] = dates[i].toLocaleDateString();

		for (var i = 0; i < n; i++) {
			if ((i > 0 && dates[i] == dates[i - 1]) || (i < n - 1 && dates[i] == dates[i + 1])) {
				if (!silent) result += '**' + dates[i] + '**<br />\n';
				found = true;
			} else {
				if (!silent) result += dates[i] + '<br />\n';
			}
		}

		if (!(n in results)) results[n] = {runs: 0, good: 0};
		results[n].runs += 1;
		if (found) results[n].good += 1;

		if (!silent) {
			result = '* * *\n' + result;
			result = 'So far for ' + n + ' birthday' + (n == 1 ? '' : 's') + ' there ' + (results[n].good == 1 ? 'has' : 'have') + ' been ' +
					results[n].good + ' matched birthday' + (results[n].good == 1 ? '' : 's') + ' from ' +
					results[n].runs + ' run' + (results[n].runs == 1 ? '' : 's') + ' for a ' +
					(Math.round(10000 * results[n].good / results[n].runs) / 100) + '% chance. ' +
					'The expected chance for ' + n + ' birthday' + (n == 1 ? '' : 's') + ' is ' + b(n) + '%.<br />\n' + result;

			$("#result").html(result);
		}
	}

	$("#runBirthdays").click(function() { doRun(false); } );

	$("#resetBirthdays").click(function() {
		results = {};
		$("#result").html('');
	});

	$("#repeatBirthdays").click(function() {
	repeatBirthdays
		var n = $("#repeatCount").val();
		var warning = '';
		if (isNaN(n) || n < 1) {
			warning = '<p class="warning">Invalid number of birthdays, defaulting to 23.</p>\n';
			n = 1;
		}

		for (var i = 0; i < n - 1; i++)
			doRun(true);

		doRun(false);
		$("#result").prepend(warning);
	});

	$("#source").hide();
	$("#viewHideSource").click(function() { $("#source").toggle(); } );
});
</script>

Also, I'm a quarter of a century old today. Here's to several more of those. :smile:
