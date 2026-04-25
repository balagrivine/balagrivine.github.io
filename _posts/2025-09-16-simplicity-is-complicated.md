---
title: "Simplicity is complicated"
date: 2025-09-16 05:40:03 +0000
categories: [Design Principles]
tags: ["design principles", "architecture"]
image:
  path: https://cdn.hashnode.com/res/hashnode/image/stock/unsplash/B_vs3DVjvic/upload/10cbde174629ebbfd065e74fb3bb3d05.jpeg
---

I didn’t have time to write a short article, so I wrote a long one instead.

Funny thing: writing a short and accurate article about a complex topic is harder than writing a long one. Same with software, keeping it simple is way harder than making it complex.

So what does C. A. R. Hoare say about program simplicity?

> There are two ways of constructing a software design: One is to make it so simple that there are obviously no deficiencies, and the other is to make it so complicated that there are no obvious deficiencies. The first one is far more difficult. **It demands the same skill, devotion, insight, and even inspiration as the discovery of the simple physical laws which underlie the complex phenomena of nature. It also requires a willingness to accept objectives which are limited by physical, logical, and technological constraints, and to accept a compromise when conflicting objectives cannot be met. No committee will ever do this until it is too late.**

For a first-time reader, this quote might seem a little bit too ambiguous. What does he mean when he says `obviously no deficiencies` and `no obvious deficiencies`? I’ll break it down in a way you can understand.

### Obviously no deficiencies

This is about keeping your design so simple and transparent that correctness almost stares you in the face. The structure leaves very little room for surprises, fewer moving parts, clearer logic, and fewer dark corners where poor design can hide. Simplicity becomes the best safety net: correctness, reliability, and longevity come naturally because maintenance stays easy.

### No obvious deficiencies

Complexity gives a false illusion of correctness. A complex design can look fine at the surface because problems are buried so deep in the structure that they aren’t immediately visible, until they explode later. Such brittle software quickly become a big ball of mud. This poses the biggest challenge, software maintainability and extensibility becomes difficult.

But what is the essence of a piece software if it can’t be maintained? It’s bound to be thrown away and forgotten, or replaced entirely by a new software if efforts to refactor it yield no fruits.

### Complexity

There are two kinds of complexity: **essential**, which is a quality about the problem being solved, and **incidental**, which is the complexity introduced by our engineering approaches. Here we’re talking about incidental complexity, as that’s the only kind we as developers can manage. Essential complexity is meant to be managed, and incidental complexity removed.

As engineers we are always attracted to complexity. Complex algorithms, complex designs, complex solutions to really simple problems. No lie. I’ve been deep in this rabbit hole a few times in my career. However Brian Kernighan tells us one thing:

> Controlling complexity is the essence of computer programming

As I gain more experience, I have learnt to embrace simplicity, learnt that perfection in a software design is achieved, not when there is nothing more to add, but when there is nothing left to take away.

> Fools ignore complexity. Pragmatists suffer it. Some can avoid it. Geniuses remove it
> 
> ― **Alan J. Perlis**

### Clever code

Clever code is bad code, if misused. That’s why some of the most prominent programming languages like Golang prioritize simplicity at their core, because if the language in which we design and code our programs, is also complicated, the language itself becomes part of the problem rather than part of its solution.

Brian Kernighan goes ahead and adds a quote

> Everyone knows that debugging is twice as hard as writing code the first time, therefore if you are as clever as you can be when writing, how will you even ever debug it

Clear is better than clever. Because maintenance is so important and so expensive, write programs as if the most important communication they do is not to the computer that executes them but to the human beings who will read and maintain the source code in the future (including yourself).

### Design for simplicity

“The rule of simplicity” from **Unix philosophy,** which originated from Ken Thompson underscores one important thing:

> Design for simplicity; add complexity only where you must.

All these people, the likes of Ken Thompson, Brian Kernighan, Rob Pike agree that at some point in time of a programs life, there will be complexity. But this complexity should not be modeled in the software from the ground up, it should only be added only when no simple solution can solve the problem you have.

> *A complex system that works has evolved from a simple system that worked. A complex system built from scratch won’t work.*

### The essence of simplicity in software design

At first, it may seem paradoxical that simplicity in software can be so hard to achieve. After all, shouldn’t simpler solution be easier to develop and maintain? Hoare’s principles underscore a fundamental truth: that simplicity is not about doing less, but doing the right thing in the right way.

1. **Reducing cognitive load**
    

Complexity in software introduces a high cognitive load on developers. When code becomes convoluted, understanding it becomes challenging. Also debugging and modifying it becomes a nightmare to the maintainer. Simplicity aims to reduce this by making the codebase more transparent and intuitive.

2. **Enhancing maintainability**
    

> The maintainability of a system is inversely proportional to the complexity of its individual pieces.

Simple code is easier to maintain. Fewer moving parts, meaning fewer fewer surprises and less frequent breakages. The maintainability of a system is inversely proportional to the complexity of its individual pieces. If the individual components within our system are simple, then generally our program will be maintainable. As a result, development can be done efficiently, saving time and money in the long run.

3. **Increasing reliability**
    

> At first I hoped that such a technically unsound project would collapse but I soon realized it was doomed to success. Almost anything in software can be implemented, sold, and even used given enough determination. There is nothing a mere scientist can say that will stand against the flood of a hundred million dollars. But there is one quality that cannot be purchased in this way - and that is reliability. The price of reliability is the pursuit of the utmost simplicity. It is a price which the very rich find most hard to pay.  
> ― **C.A.R. Hoare**

It asserts that achieving reliability in systems, particularly software, requires designing them with minimal complexity, as intricate designs inherently increase the potential for errors and failures.

### Strategies for achieving simplicity

1. **Refactoring**
    

One of the ways of controlling complexity is through continuous refactoring.

Refactoring is not a one-time action. Martin Fowler, in his book Refactoring says that refactoring is “**a disciplined, technique for improving existing code's internal structure without changing its external behavior**, **achieved through numerous small, behavior-preserving transformations**“ .

As engineers, it’s our duty to always refactor our applications. That messy part of the code that was delivered in haste during the last quarter, take some time and revisit it, revisit that design that was poorly done and improve areas that need improvement. You teammates, and even your future self will thank you for it.

2. **Developing good culture**
    

If you are part of a larger team, ensure the team has some sort of convention. Bad convention is better than no convention. Conventions guarantee consistency. And consistency is what matters. It helps teams avoid chaos. Have standard coding standards, set stringent linters that catch poor design or complex code early enough, establish a common coding standard. Because to scale a development team, you need culture, and good culture attracts brilliant engineers.

3. **Continuous learning**
    

This is a proven way of achieving simplicity. The more you learn, the more perspectives you gain, and the more tools you have to choose from. Instead of jumping on the first clever solution that comes to mind, you start recognizing simpler approaches you might have missed before.

### Simple is always better, but not always the best

The simplest solution might not always be the best solution. While simplicity is often a goal, it can sometimes be insufficient or lack necessary complexity. Some problems inherently demand complex solutions. In such cases, remember that we cannot do away entirely with essential complexity, but that’s fine. Because we can manage it.

### Conclusion

There is no silver bullet. No single, easy solution to a complex problem; instead, achieving simplicity requires consistent effort, multiple approaches, and practical, incremental steps.

Anyway, this article is long enough. If I keep going, I’ll be violating my own simplicity rule. So I’ll stop here before it gets complex.

Hope you enjoyed.
