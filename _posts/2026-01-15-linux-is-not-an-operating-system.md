---
title: "Linux is not an operating system"
date: 2026-01-15 16:36:22 +0000
categories: [Operating System]
tags: ["operating system", "Linux", "GNU/Linux"]
image:
  path: https://cdn.hashnode.com/res/hashnode/image/upload/v1768495168844/6ebd9084-d246-4a90-af09-45429a6c552a.webp
---

\[Note: If you are confident that you know the difference between an operating system and a kernel, and why it would not make sense to call Linux an operating system as many usually do, I’d happily recommend you to read this totally unrelated article by my friend *Alex Gaetano Padula*, lead architect of TidesDB. [https://tidesdb.com/articles/what-i-learned-building-a-storage-engine-that-outperforms-rocksdb/](https://tidesdb.com/articles/what-i-learned-building-a-storage-engine-that-outperforms-rocksdb/)

I also contribute to [TidesDB](https://github.com/tidesdb/tidesdb), an open-source embeddable key-value storage engine written in C, regularly doing some routine cleanup work while trying to understand the system as a whole.

My interest in this topic comes from working close to the metal.

In to the details:

“What operating system do you use?” Someone will confidently answer “Linux”. I don’t blame you, it’s the confusion that has been there for years across the web and many formal academic publications have made the same mistake, calling Linux an operating system.

Let’s first begin by understanding what the terms Operating System and Kernel mean.

An **operating system** as we use the term, means a collection of programs that are sufficient to use the computer to do a wide variety of jobs. A general purpose operating system, to be complete, ought to handle all the jobs that many users may want to do.

A **kernel** on the other hand is one of the programs in an operating system that allocates the machine's resources to the other programs that are running. The kernel also takes care of starting and stopping other programs.

If a car is the Operating System, Linux kernel is the engine. Both complement each other, and one cannot bear much usefulness without the other.

So in our case, Linux is the kernel. It is one of the most important software components within any UNIX-based operating system, acting as the vital bridge between software applications and the computer's hardware, managing resources like CPU and memory, and enabling multitasking by controlling hardware access, ensuring apps run smoothly and securely through functions like process scheduling, memory management, device management, and system calls.

## Confusion of “Linux as an operating system”

This confusion stems back to the mid 80s, when Richard Stallman, and a group of friends from the **Free Software Foundation** decided to build a new operating system that would be free to use, modify and distribute, unlike the then proprietary UNIX operating system developed by Bell Labs under AT & T. The operating system was called “**GNU**”, a wordplay to mean “**GNU’s Not UNIX**“**.**

Years later, the GNU project had made tremendous effort towards achieving their goal of developing a completely free operating system, its just that there was a little problem. The GNU project did not have a ready kernel to make their GNU operating system usable.

By the early 90s GNU project had put together the whole system aside from the kernel. They had also started a kernel, the GNU Hurd[,](https://www.gnu.org/software/hurd/hurd.html) but it was a long way from being ready for people to use in general.

Once Torvalds released Linux in 1991, it fit into the last major gap in the GNU system. People could then combine Linux with the GNU system to make a complete free system, a version of the GNU system which also contained Linux.

The GNU project then coined a name for this operating system; **“GNU/Linux”** majorly to give credits to Linus Torvalds for his work on the kernel that allowed them to release a completely free operating system.

Linux kernel continued gaining more traction, and at the same time, GNU/Linux became too wordy, and many users started referring to the operating system as “**Linux**” instead on “**GNU/Linux**”.

That’s how the GNU/Linux operating system quickly “re-branded” to Linux operating system.

## Linux Distributions

Many of the distributions today (Ubuntu, Debian, Arch) all run a modified version of the GNU system, with Linux running as their kernel. Therefore, most of the so-called “Linux” distributions are really distributions of GNU/Linux.

## Final Thoughts

Without Torvalds’ Linux kernel, there would be nothing today like the GNU/Linux system, and probably no free operating system with comparable adoption and impact.

Even if Torvalds had released Linux under some other free software license, a free kernel alone would not have made much difference to the world. The significance of Linux came from fitting into a larger framework, a complete free operating system: GNU/Linux.

From today, if it’s the operating system you are referring to, please use **GNU/Linux**, and if it’s the kernel, just use **Linux**.

## References

“GNU by Richard Stallman and the Free Software Foundation” - [https://www.gnu.org/](https://www.gnu.org/)

“UNIX wiki” - [https://en.wikipedia.org/wiki/Unix](https://en.wikipedia.org/wiki/Unix)

See you in my next article🥂
