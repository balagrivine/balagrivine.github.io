---
title: "Implementing Domain-Driven Design in Storage Engine Development"
date: 2026-01-17 17:03:03 +0000
categories: [Domain Driven Design]
tags: ["Domain-Driven-Design", "software design"]
image:
  path: https://cdn.hashnode.com/res/hashnode/image/stock/unsplash/42T6bwBT_QM/upload/0b6b4c65865df88dea1f9e0b081155f7.jpeg
---

A few weeks ago, I began contributing to [TidesDB](https://tidesdb.com/getting-started/what-is-tidesdb/), an open-source, embeddable key-value storage engine written in C. Coming from an application engineering background, I noticed that many of the design principles I had relied on in large-scale backend systems were uncommon in low-level systems code.

In this article, I explore how Domain-Driven Design can be applied even in a systems programming context by walking through a refactor of the WAL and SSTable recovery logic in TidesDB. Drawing from my experience building Go systems, I applied familiar design concepts to improve readability, reasoning, and extensibility.

The changes discussed here are based on a real contribution to the project, which you can find in this merge request - [https://github.com/tidesdb/tidesdb/pull/527](https://github.com/tidesdb/tidesdb/pull/527)

## What is a storage engine

A storage engine is the core component of a database system responsible for managing how data is physically stored, retrieved, and organized on disk or in memory. It handles data persistence, caching, and access patterns while implementing specific optimizations for different types of workloads.

There are 2 types of storage engines; Log-Structure oriented and Page-Oriented engines. The one we will be referencing today, TidesDB, is Log-Structure oriented.

## What is Domain-Driven Design

Domain-Driven Design is an approach to software development that centers the development on programming a domain model that has a rich understanding of the processes and rules of a domain.

The whole idea is that code should use the same language as domain experts use when discussing the system.

This approach was popularized by Eric Evans in his book [Domain-Driven Design: Tackling Complexity in the Heart of Software](https://www.amazon.com/Domain-Driven-Design-Tackling-Complexity-Software/dp/0321125215).

Let’s discuss the rules of the domain around which we are programming TidesDB.

TidesDB has mechanisms to recover a database from disk after crash. There are 2 on-disk components that need to be recovered during the recovery process. Write Ahead Log (WAL) files and Sorted Strings Tables (SSTables).

A **WAL file** is a transaction log that ensures data integrity, recording changes *before* they're made to the memtable. Once a memtable has been flushed to disk as an SSTable, the WAL file can be safely deleted in the background. However, suppose a power outage occurred before we flushed the memtable or during flushing, TidesDB on startup will recover the WAL file containing the memtable’s data and flush it to disk as an SSTable.

An **SSTable(Sorted Strings Table)** on the other hand is an append-only immutable file where writes buffered in memory within a data structure called memtable are flushed, once the memtable grows beyond the configured write buffer size. SSTables are later on merged in a process called compaction, discarding obsolete entries and reclaiming space.

TidesDB applies different validation rules when recovering WAL files and SSTables from disk.

* WAL files use **permissive mode**. If the last block has invalid footer magic or incomplete data, the system truncates the file to the last valid block by walking backward through the file. This handles crashes during WAL writes. If no valid blocks exist, truncates to header only.
    
* SSTables use **strict mode**. Any corruption in the last block causes the SSTable to be rejected entirely. This reflects that SSTables are permanent and must be correct.
    

These two semantics tie to “**ubiquitous language**” in DDD. The idea behind ubiquitous language is building up a common, rigorous language between developers and users and embed that language into the software systems that we build.

## Talk is cheap, show me the code

```c
/**
 * block_manager_validate_last_block
 * validates the integrity of the last block in a block manager file
 * @param bm the block manager
 * @param strict if 1, reject any corruption (for SSTables); if 0, truncate to last valid block (for
 * WAL)
 * @return 0 if valid or successfully recovered, -1 if validation fails
 *
 * In strict mode -- any corruption returns -1, file is not modified
 * In permissive mode -- truncates to last valid block on corruption
 */
int block_manager_validate_last_block(block_manager_t *bm, int strict);
```

Looking at the original function signature, it’s clear that the domain semantics are not explicitly modeled:

The documentation tells the reader to pass `0` for permissive validation and `1` for strict validation. However, this encoding relies entirely on convention. Nothing prevents a caller from passing `2`, `-1`, or any other value, leading to semantically undefined behavior at the domain level.

We are programming in C, a compiled language. So in the above scenario, we change the function signature in such a way that we will let the compiler enforce that we will never have accidental misuse of this function.

Using the ubiquitous language, we can replace meaningless primitive integer defined in the function signature with a **domain concept**.

```c
typedef enum
{
    TDB_PERMISSIVE_BLOCK_VALIDATION = 0, /* validation mode for WAL files */
    TDB_STRICT_BLOCK_VALIDATION = 1      /* validation mode for SSTables */
} tidesdb_block_validation_mode_t;

/**
 * block_manager_validate_last_block
 * validates the integrity of the last block in a block manager file
 * @param bm the block manager
 * @param validation the type of validation to apply, either strict or permissive
 * @return 0 if valid or successfully recovered, -1 if validation fails
 *
 * In strict mode -- any corruption returns -1, file is not modified
 * In permissive mode -- truncates to last valid block on corruption
 */
int block_manager_validate_last_block(block_manager_t *bm,
                                      tidesdb_block_validation_mode_t validation);
```

This change improves the API in several ways:

* It documents intent directly in the type system
    
* It reduces accidental misuse
    
* It aligns the code with the domain’s ubiquitous language
    

```c
block_manager_validate_last_block(wal, TDB_PERMISSIVE_BLOCK_VALIDATION);
block_manager_validate_last_block(klog_bm, TDB_STRICT_BLOCK_VALIDATION);
```

## Policy modelling

In DDD, a policy is a rule that controls how the system behaves under certain conditions.

In our case, we have a policy that WAL recovery should use permissive validation and SSTable recovery should use strict validation mode.

The old code read like this:

```c
int block_manager_validate_last_block(block_manager_t *bm, const int strict)
{
    ...
    if (strict)
        {
            return -1;
        }
    ...
}
```

The code above has been simplified for the purpose of making this article short. With this code, imagine the effort that would be required to change it if the policy we have was to change, or if we needed to add a new policy for a new recovery mode. It probably will need massive refactors.

Now let’s see how this will look with policy modelling enforced.

```c
int block_manager_validate_last_block(block_manager_t *bm,
    tidesdb_block_validation_mode_t validation)
{
    if (validation == TDB_STRICT_BLOCK_VALIDATION) {
        return -1;
    }
}
```

This is now a policy switch, not a boolean flag. It future-proofs the API, making the changes involved in the future less costly.

```c
/**
* initally, someone could do this without the compiler complaining
* however, with the new change, we get compiler protection and no one can call the function
* with an invalid argument.
*/
block_manager_validate_last_block(bm, 42);
```

There are other DDD semantics like bounded contexts that I haven’t covered here but I’ll probably write about them in future articles.

## Conclusion

From the refactor, it’s evident that techniques like Domain-Driven Design are not only applicable in enterprise software, they can also be applied in low-level systems programming and still be relevant.
