---
title: Evaluating prefix/infix/postfix expressions
date: 2012-10-08 14:00:30
programming/languages:
- JavaScript
programming/topics:
- Data Structures
slug: evaluating-prefixinfixpostfix
---
In [yesterday's post]({{< ref "2012-10-07-three-ways-to-write-expressions.md" >}}), I talked about three different ways to write expressions: prefix, infix, and postfix expressions. I also promised to write up a web-based example that would show the guts of each algorithm in action. Well, here it is!

Use the three buttons at the top to switch between the different machines. Enter an expression in the box and click run to evaluate it. The only things that are supported at the moment are numbers (integers or floating point) and the operators +, -, \*, and /, although the code is extensible enough that adding more shouldn't be an issue.

Have fun!

* [prefix](#prefix)
* [infix](#infix)
* [postfix](#postfix)

# Prefix / Scheme <a name="prefix"></a>

<input type="text" id="prefixInput" value="+ * 5 8 + 5 - 1 4"> <button id="prefixRun">Run</button>

## Results

<table class="table table-striped">
	<thead><tr><td>Tick</td><td>Input</td><td>Output</td><td>Rest</td><td>Error</td></tr></thead>
	<tbody id="prefixResult"></tbody>
</table>

```javascript
// known operators
var operators = {
	'+': function(a, b) { return a + b; },
	'-': function(a, b) { return a - b; },
	'*': function(a, b) { return a * b; },
	'/': function(a, b) { return a / b; },
};

// process at this level
// return the result of this level and what we didn't use
// return a null value if we fail at any point
function step(current) {
	// directly return numbers
	if (!isNaN(parseFloat(current[0]))) {
		return {
			value: parseFloat(current[0]),
			rest: current.slice(1)
		};
	}

	// otherwise, we're going to have to recur
	else {
		var f = operators[current[0]];

		// recur for left, use that rest for right
		var left = step(current.slice(1));
		if (left.value == null) return {value: null, rest: []};
		var right = step(left.rest);
		if (right.value == null) return {value: null, rest: []};

		// return at my level
		return {
			value: f(left.value, right.value),
			rest: right.rest
		};
	}
}
step(input);
```

* * *

# Infix <a name="infix"></a>

<input type="text" id="infixInput" value="4 + 2 * 7 - 1 * 5 + 6 * 5 - 1"> <button id="infixRun">Run</button>

## Results

<table class="table table-striped">
	<thead><tr><td>Tick</td><td>Command</td><td>Reducing</td><td>Error</td></tr></thead>
	<tbody id="infixResult"></tbody>
</table>

```javascript
// known operators
var operators = {
	'+': function(a, b) { return a + b; },
	'-': function(a, b) { return a - b; },
	'*': function(a, b) { return a * b; },
	'/': function(a, b) { return a / b; },
};
var precedence = [
	['*', '/'],
	['+', '-']
]

// process until we are done
while (input.length > 1) {
	// find the first operator at the lowest level
	var reduceAt = 0;
	var found = false;
	for (var i = 0; i < precedence.length; i++) {
		for (var j = 1; j < input.length - 1; j++) {
			if ($.inArray(input[j], precedence[i]) >= 0) {
				reduceAt = j;
				found = true;
				break;
			}
		}
		if (found) break;
	}

	// if we didn't find one, bail
	if (!found) return;

	// otherwise, reduce that operator
	var newInput = [];
	var f = operators[input[reduceAt]];

	for (var i = 0; i < reduceAt - 1; i++)
		newInput.push(input[i]);

	newInput.push("" + f(
		parseFloat(input[reduceAt - 1]),
		parseFloat(input[reduceAt + 1])
	));

	for (var i = reduceAt + 2; i < input.length; i++)
		newInput.push(input[i]);

	input = newInput;
}
```

* * *

# Postfix / RPN <a name="postfix"></a>

<input type="text" id="postfixInput" value="4 2 7 * + 1 6 - 5 * - 1 -"> <button id="postfixRun">Run</button>

## Results

<table class="table table-striped">
	<thead><tr><td>Tick</td><td>Command</td><td>Stack</td><td>Error</td></tr></thead>
	<tbody id="postfixResult"></tbody>
</table>

```javascript
// known operators
var operators = {
	'+': function(a, b) { return a + b; },
	'-': function(a, b) { return a - b; },
	'*': function(a, b) { return a * b; },
	'/': function(a, b) { return a / b; },
};

// run through all commands in the input
var stack = [];
for (var i = 0; i < input.length; i++) {
	var cmd = input[i];

	// known operator
	if (cmd in operators) {
		// get the function
		var f = operators[cmd];

		// sanity check
		if (stack.length < f.length) {
			error = 'not enough arguments';
			break;
		}

		// get the correct number of arguments
		var args = [];
		for (var j = 0; j < f.length; j++)
			args.unshift(stack.shift());

		// apply and push back onto the stack
		// note: the first argument to apply is 'this'
		stack.unshift(f.apply(undefined, args));
	}

	// anything else, push onto the stack as either a number or string
	else {
		stack.unshift(isNaN(parseFloat(cmd)) ? cmd : parseFloat(cmd));
	}
}
```

* * *

Hopefully this helps give some insight into what I was talking about in [yesterday's post]({{< ref "2012-10-07-three-ways-to-write-expressions.md" >}}). I have to admit, I'm actually starting to like Javascript. It's a bit strange at times, but it does have a nice functional flavor which is always fun.

If you'd like to download the entire source code, you can do so here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/evaluating-prefix-infix-postfix.js" title="Evaluating prefix/infix/postfix source code">source code</a>

<style>
.warning { color: red; }
</style>

<script>
jQuery(function($) {

// only show one of the three at a time
//$("#prefix").hide();
$("#infix").hide();
$("#postfix").hide();

$("#prefixShow").click(function() {    
	$("#prefix").show();
	$("#infix").hide();
	$("#postfix").hide();
});

$("#infixShow").click(function() {    
	$("#prefix").hide();
	$("#infix").show();
	$("#postfix").hide();
});

$("#postfixShow").click(function() {    
	$("#prefix").hide();
	$("#infix").hide();
	$("#postfix").show();
});

// show/hide source, start with it hidden
$(".source").hide();
$("#showHidePrefixSource").click(function() { $("#prefixSource").toggle(); });
$("#showHideInfixSource").click(function() { $("#infixSource").toggle(); });
$("#showHidePostfixSource").click(function() { $("#postfixSource").toggle(); });

// known operators
var operators = {
	'+': function(a, b) { return a + b; },
	'-': function(a, b) { return a - b; },
	'*': function(a, b) { return a * b; },
	'/': function(a, b) { return a / b; },
};
var precedence = [
	['*', '/'],
	['+', '-']
]

// evaluate an prefix expression
function prefixRun() {
	$("#prefixResult").empty();

	var tick = 0;

	var input = $('#prefixInput').val().split(" ");
	var error = null;

	// process at this level
	// return an array of the result of this level and what we didn't use
	function step(current) {
		tick += 1;

		// if we don't have anything else, this is an error
		if (current.length == 0) {
			$('#prefixResult').append('<tr><td>' + tick + '</td><td>' + current.join(' ') + '</td><td></td><td></td><td class="warning">unable to continue, no input</td></tr>\n');
			return {value: null, rest: []};;
		}

		// report what we started with
		$('#prefixResult').append('<tr><td>' + tick + '</td><td>' + current.join(' ') + '</td><td></td><td></td><td class="warning"></td></tr>\n');

		// directly return numbers
		if (!isNaN(parseFloat(current[0]))) {
			var output = parseFloat(current[0]);
			var rest = current.slice(1);

			$('#prefixResult').append('<tr><td>' + tick + '</td><td></td><td>' + output + '</td><td>' + rest.join(' ') + '</td><td class="warning"></td></tr>\n');

			return {value: output, rest: rest};
		}

		// otherwise, we're going to have to recur
		else {
			var f = operators[current[0]];

			// recur for left, use that rest for right
			var left = step(current.slice(1));
			if (left.value == null) return {value: null, rest: []};
			var right = step(left.rest);
			if (right.value == null) return {value: null, rest: []};

			// apply the function to the two values
			var output = f(left.value, right.value);
			var rest = right.rest;

			$('#prefixResult').append('<tr><td>' + tick + '</td><td></td><td>' + left.value + ' ' + current[0] + ' ' + right.value + ' = ' + output + '</td><td>' + rest.join(' ') + '</td><td class="warning"></td></tr>\n');

			return {value: output, rest: rest};
		}
	}
	var result = step(input);
	if (result.value == null) {
	} else if (result.rest.length == 0) {
		$('#prefixResult').append('<tr><td>result</td><td></td><td><b>' + result.value + '</b></td><td></td><td class="warning"></td></tr>\n');
	} else {
		$('#prefixResult').append('<tr><td>result</td><td></td><td></td><td>' + result.rest.join(' ') + '</td><td class="warning">malformed expression</td></tr>\n');
	}
}
$("#prefixRun").click(prefixRun);

// evaluate an infix expression
function infixRun() {
	$("#infixResult").empty();

	var tick = 0;

	var input = $('#infixInput').val().split(" ");
	var error = null;

	// process until we are done
	while (input.length > 1) {
		tick += 1;

		// find the first operator at the lowest level
		var reduceAt = 0;
		var reduceWhich = undefined;
		var found = false;
		for (var i = 0; i < precedence.length; i++) {
			for (var j = 1; j < input.length - 1; j++) {
				if ($.inArray(input[j], precedence[i]) >= 0) {
					reduceAt = j;
					reduceWhich = precedence[i].join(' ')
					found = true;
					break;
				}
			}
			if (found) break;
		}

		// if we didn't find one, error
		if (!found) {
			$('#infixResult').append('<tr><td>' + tick + '</td><td>' + input.join(' ') + '</td><td></td><td class="warning">unable to find an operator to reduce</td></tr>\n');
			$('.warning').css('color', 'red');     
			return;
		}

		// report what we're about to do
		$('#infixResult').append('<tr><td>' + tick + '</td><td>' + input.join(' ') + '</td><td>' + reduceWhich + '</td><td class="warning"></td></tr>\n');

		// otherwise, reduce that operator
		var newInput = [];
		var f = operators[input[reduceAt]];

		for (var i = 0; i < reduceAt - 1; i++)
			newInput.push(input[i]);

		newInput.push("" + f(
			parseFloat(input[reduceAt - 1]),
			parseFloat(input[reduceAt + 1])
		));

		for (var i = reduceAt + 2; i < input.length; i++)
			newInput.push(input[i]);

		input = newInput;
	}

	// report the final result
	$('#infixResult').append('<tr><td>result</td><td><b>' + input.join(' ') + '</b></td><td></td><td class="warning"></td></tr>\n');
}
$("#infixRun").click(infixRun);

// evaluate a postfix expression
function postfixRun() {
	$("#postfixResult").empty();

	var tick = 0;
	var stack = [];

	var input = $('#postfixInput').val().split(" ");
	var error = null;

	// run through all commands in the input
	for (var i = 0; i < input.length; i++) {
		var cmd = input[i];
		tick += 1;

		// known operator
		if (cmd in operators) {
			// get the function
			var f = operators[cmd];

			// sanity check
			if (stack.length < f.length) {
			error = 'not enough arguments';
			break;
			}

			// get the correct number of arguments
			var args = [];
			for (var j = 0; j < f.length; j++)
			args.unshift(stack.shift());

			// apply and push back onto the stack
			// note: the first argument to apply is 'this'
			stack.unshift(f.apply(undefined, args));
		}

		// anything else, push onto the stack as either a number or string
		else {
			stack.unshift(isNaN(parseFloat(cmd)) ? cmd : parseFloat(cmd));
		}

		// report on current stack
		$('#postfixResult').append('<tr><td>' + tick + '</td><td>' + cmd + '</td><td>' + stack + '</td><td></td></tr>\n');
	}

	// check final stack
	if (stack.length > 1)
		error = 'malformed expression, multiple results on final stack';

	// report final result or error
	if (error == null) {
		$('#postfixResult').append('<tr><td>result</td><td></td><td><b>' + stack + '</b></td><td></td></tr>\n');
	} else {
		$('#postfixResult').append('<tr><td>result</td><td>' + cmd + '</td><td>' + stack + '</td><td class="warning">' + error + '</td></tr>\n');
		error = null;
	}  
}
$("#postfixRun").click(postfixRun);
});
</script>
