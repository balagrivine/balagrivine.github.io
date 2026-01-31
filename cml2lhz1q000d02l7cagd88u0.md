---
title: "Understanding Limited Direct Execution in Operating Systems"
datePublished: Sat Jan 31 2026 17:38:02 GMT+0000 (Coordinated Universal Time)
cuid: cml2lhz1q000d02l7cagd88u0
slug: understanding-limited-direct-execution-in-operating-systems
cover: https://cdn.hashnode.com/res/hashnode/image/stock/unsplash/G6YltyA2Mvg/upload/e5ba94e9545cd6c292273e9d9bac1c45.jpeg
tags: operating-system

---

I recently picked up this timeless book, [Operating Systems: Three Easy Pieces](https://www.amazon.com/Operating-Systems-Pieces-Hardcover-Version/dp/B0722MJYCB/ref=tmm_hrd_swatch_0), a book covering the fundamentals of operating systems. My motivation to read this book comes from partly working on a critical software, a fast embeddable key-value storage engine called [TidesDB](https://tidesdb.com/).

You see, to deeply understand how such a critical component in a DBMS works, how it interacts with both memory, CPU and the hardware, as well as optimize it for extremely high performance like TidesDB, you need to understand how the storage engine manipulates these resources.

There’s no better place to begin than understanding the OS, which acts as the bridge, allowing code running the storage engine to interact with these resources.

In this blog post, we are going to learn a technique the operating system uses to allow code run natively on the CPU in user mode, with restricted privileges, while at the same time regaining control of the CPU when needed.

On to the details.

## Introduction

One of the most powerful abstraction the OS provides to a running process is **virtualization**, in the sense that the OS takes a physical resource like the CPU and creates an illusion that many virtual CPUs exist, when in fact there is only one or a few CPUs depending on the CPU architecture.

By virtualizing the CPU, the OS can then run lots of programs on a single or a few available CPUs creating a basis for something called **time sharing**.

By definition, time sharing is a technique used by the OS to allow several processes share the CPU by running one process, then stopping it for some time and allowing another process to run without any of the processes knowing that they are sharing a single CPU.

## Process Execution Protocol

Before delving deeper into the blog, I will want us to understand a few things, specifically about the difference between a **process** and a **program**, and how a program gets transformed into a process.

A program is a set of instructions and some static data, that directs a computer to perform specific tasks.

A process on the other hand is a running instance of a program.

The first thing that the OS must do to run a program is to load its code and any static data (e.g., initialized variables), into the **address space** of the process.

Address space is the complete range of memory addresses a process can use, providing an isolated, virtual view of memory that maps to actual physical memory locations.

When a process accesses memory outside its address space, the **memory management unit** raises a fault, which transfers control to the OS, often resulting in a **segmentation fault.**

Once the code and static data are loaded into memory, some memory must be located for the program’s **stack.** Programs use the stack for local variables, function parameters, and return addresses.

The OS may also allocate some memory for the program’s **heap**. The heap is used for explicitly requested dynamically-allocated data, storing data structures such as linked lists, hash tables, trees, and other interesting data structures.

Lastly, the OS locates the program’s entry point i.e, the main() routine, jumps to it, and starts running the user’s code.

## Direct Execution

We have talked about the operating system running a process directly on the CPU to maximize performance by reducing the indirection if the process was accessing CPU through the OS.

In an ideal scenario, the OS would load a program and let it run directly on the CPU until it finishes. However, this gives the OS no control, allowing a rogue program to take over.

“How can a program take over the system yet the OS can easily terminate it?” You see, **when a process is executing, the operating system sits idle doing nothing, unless it’s invoked by the process or through hardware support.**

This happens because the CPU is busy running the program’s instructions not the OS’s code. The risk with this manifests itself in the sense that when the OS is not running to intervene, the currently executing process will run for as long as it wants, starving other programs CPU time.

## Limited Direct Execution

We have seen that without the operating system’s intervention, a process will completely dominate the CPU and execute until it finishes. If it's a long running process, this is bad for other processes in the system.

To mange, the OS, with hardware support, ensures it regains control of the CPU and divides the CPU time fairly among all the processes in the system.

### A Cooperative approach: Wait for system calls

Operating systems of the earlier days `trusted` processes to behave selflessly and give up the CPU to other processes after executing for some time.

Most of the processes as it turns out give up control of the CPU to the OS by making **system calls**, or if the process **does something illegal.**

A system call ,for those who might not be familiar, is a mechanism the OS provides to processes executing in the **user mode** to request access to resources controlled by the hardware, for example, access to memory or disk.

A process might do something illegal, let’s say accessing memory address outside its address space, dividing by zero, or even trying to execute something directly from the kernel. In all of the above cases, the process generates a **trap** to the OS. The OS will then have control of the CPU again and likely terminate the offending process.

Once the OS has regained control of CPU via the system call, it decides what to do next.

The OS might choose to continue execution of the current process and perform the privileged action requested by the process, it may halt execution of the current process and transfer control to another process based on the wise decision of the scheduler.

### A Non-cooperative approach. The OS takes over

The first approach might work perfectly for well-behaved processes that understand **“sharing is caring”**. However, the OS is always faced by all kinds of ill-mannered processes, those written to run infinite loops, those that never make system calls or generate traps. In one way or the other, the system must still regain control of the CPU.

The answer to this is a **timer interrupt**. A timer device can be programmed to raise an interrupt every so many milliseconds; when the interrupt is raised, the currently running process is halted, and a pre-configured interrupt handler in the OS runs. At this point, the OS has regained control of the CPU, and thus can do what it pleases: stop the current process, and start a different one.

Once the OS has regained control of the CPU, the OS will have to choose whether to keep running the currently running process or switch to another process. In case it switches to a different process, it will perform a **context switch**.

A context switch is a low-level piece of code that instruct the OS to save a few register values for the currently-executing process (onto its kernel stack) and restore a few for the soon-to-be-executing process (from its kernel stack).

By doing so, the OS thus ensures that when the return-from-trap instruction is finally executed, instead of returning to the process that was running, the system resumes execution of another process.

![](https://cdn.hashnode.com/res/hashnode/image/upload/v1769885414085/3a69294a-1468-48b6-8b40-30f8adbc76d2.png align="center")

## Conclusion

Maybe something you as a reader can to ponder on. How does the operating system perform a system call under the hood, given that requests to the OS for example, `write()` or `fork()` look like “normal procedure calls”. Do you think there is something special about them?

## References

“Operating systems: Three easy pieces” by Remzi H. Arpaci-Dusseau and Andrea C. Arpaci-Dusseau