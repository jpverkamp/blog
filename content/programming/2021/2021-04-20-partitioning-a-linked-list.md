---
title: Partitioning a Linked List
date: 2021-04-20
programming/languages:
- Python
programming/topics:
- Small Scripts
programming/sources:
- LeetCode
---
One more fairly standard tech interview problem (for better or for worse, you're likely to see one of these if you go for a programming job):

> Given a {{< wikipedia "linked list" >}} and an element `x`. Partition the list so that all elements less than `x` are before elements greater than or equal to `x`, but do not otherwise change the order of the elements.

<!--more-->

Interviewers really do love their linked lists. And it does make sense, since they can be a very efficient data structure for center kinds of problems, such as moving around and inserting elements in the end where more 'traditional' straight arrays would have problems (to insert in the middle, you have to move every element). 

Python doesn't directly have a built in linked list class (lists in python are sort of a hybrid), but it's easy enough to make one! Especially with {{< doc python "dataclasses" >}}. Those are wonderful for boiler plate. Decorate the class with `@dataclasses.dataclass` and you get a constructor, stringification, and comparison for free! I added a method to turn a traditional python list into a linked list, but that's it:

```python
@dataclass
class ListNode:
    val: int = 0
    next: 'ListNode' = None

    @staticmethod
    def from_iterable(ls):
        head = None
        previous = None

        for el in ls:
            current = ListNode(el)

            if previous:
                previous.next = current
            else:
                head = current

            previous = current

        return head
```

Now for the actual solution, my goal will be essentially to make 5 different pointers into the list and iterate along them at different speeds:

* `current` will store where we are in our progress through the list
* `lt_head` will store the first node in the eventual less than half of the list, this will become the new head of the list
* `lt_current` will store the current tail of the less than half of the list, add each 'lt' element here and advance it
* `gte_head` will store the head of the greater than or equal to half, this will get attached to the last `lt_current`
* `gte_current` will be the tail of the second half of the list, add each 'gte' element here

And that's pretty much the entire algorithm:

* For each element: 
  * If it's less than the pivot point, add it to the `lt_current`'s next and move that pointer forward
  * Otherwise do the same for the `gte_current`
* Store the first `lt` node in `lt_head` and the first `gte` node in `gte_head`

That helps us deal with the corner cases: 

* If there are no elements less than the pivot, the final head node will be `gte_head` (since both `lt_head` and `lt_current` will be null). Vice versa if all of the elements are less than, although in that case, you can just combine the two anyways, since `gte_head` will be `None` and a `None` element in `.next` means the same thing as no element. 

Code!

```python
def partition(self, head: ListNode, x: int) -> ListNode:
    current = head

    # Create two linked lists: lt (less than) and gte (greater than or equal)
    # The head is the beginning of the new linked list, the current node is the tail we're building
    lt_head = None
    lt_current = None
    gte_head = None
    gte_current = None

    # Iterate through the current list
    while current:
        # Add to the lt partition
        # If we already have a tail, connect it to this node
        # If we don't, this is the new head
        if current.val < x:
            if lt_current:
                lt_current.next = current

            lt_current = current

            if not lt_head:
                lt_head = lt_current
        # Otherwise, add it to the gte partition with the same conditions
        else:
            if gte_current:
                gte_current.next = current
                
            gte_current = current

            if not gte_head:
                gte_head = gte_current

        # Advance on the main iteration
        current = current.next

    # If the gte_current wasn't the last node, this points somewhere wrong
    # Since this is the current tail, None the next pointer
    if gte_current:
        gte_current.next = None

    # So long as at least one element is in the lt partition, connect the two
    if lt_current:
        lt_current.next = gte_head

    # Return the lt partition's head if it exists, otherwise there are only gte nodes
    return lt_head or gte_head
```

I thought that was a pretty cool algorithm. 

Some test cases:

```python
class TestSolution(unittest.TestCase):
    def test_1(self):
        self.assertEqual(
            partition(ListNode.from_iterable([1,4,3,2,5,2]), 3),
            ListNode.from_iterable([1,2,2,4,3,5])
        )

    def test_2(self):
        self.assertEqual(
            partition(ListNode.from_iterable([2,1]), 2),
            ListNode.from_iterable([1, 2])
        )

    def test_3(self):
        self.assertEqual(
            partition(ListNode.from_iterable([1,4,3,2,5,2]), 3),
            ListNode.from_iterable([1, 2, 2, 4, 3, 5])
        )

if __name__ == '__main__':
    unittest.main()
```

Quick:

```bash
...
----------------------------------------------------------------------
Ran 3 tests in 0.000s

OK
```