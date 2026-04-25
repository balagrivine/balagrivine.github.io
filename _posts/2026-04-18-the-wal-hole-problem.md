---
title: "The WAL Hole Problem"
date: 2026-04-18 10:16:49 +0000
image:
  path: https://cdn.hashnode.com/uploads/covers/6488728c19ef65fa1e2bc378/65db6901-de47-4b84-911d-ca807688f066.jpg
---

<s>TL;DR</s> Too Short;Just Read

> If a WAL write is interrupted by a Unix signal, or completes as a short write, the kernel may leave a zero-filled gap at the reserved offset. During crash recovery, TidesDB's cursor would hit that zero block\_size, have no way to determine the hole's extent, and stop. Every valid record written after the hole was silently abandoned. I discovered this while studying how system calls like pwritev interact with the kernel's file layer. What I found became what I call the "WAL hole problem".

This article explains what a WAL hole is, the exact failure mode it creates under concurrent writes, and how we fixed for TidesDB in https://github.com/tidesdb/tidesdb/pull/591

## What is a WAL

A write-ahead log (WAL) is an append-only file used by database systems to ensure durability.

All changes are first written to the WAL before being applied to in-memory or on-disk structures. This guarantees recovery after a crash.

It provides high performance by turning random, slow disk writes into fast sequential appends.

![](https://cdn.hashnode.com/uploads/covers/6488728c19ef65fa1e2bc378/c79c906d-8904-4182-ae53-27085951b635.png)

This mimics TidesDB's LSM architecture in which all operations modifying the database are first applied to the WAL before being committed to the in-memory memtable and then later flushed to disk as Sorted Strings Tables(SSTables).

## The WAL hole

A WAL hole surfaces when the WAL is being written to concurrently by multiple threads.

What happens is that a thread will reserve space by atomically incrementing the WAL file offset. This happens by loading the current file offset, summing it up with the size of data the thread is requesting to be written to disk, such that subsequent threads read the new file offset.

```c
...

int64_t block_manager_write_raw(block_manager_t *bm, const void *data, const uint32_t size)
{
    ...

    const size_t total_size = BLOCK_MANAGER_BLOCK_HEADER_SIZE + size + BLOCK_MANAGER_FOOTER_SIZE;

    ...

    const int64_t offset = (int64_t)atomic_fetch_add(&bm->current_file_size, total_size);

    unsigned char header[BLOCK_MANAGER_BLOCK_HEADER_SIZE];
    encode_uint32_le_compat(header, size);
    encode_uint32_le_compat(header + BLOCK_MANAGER_SIZE_FIELD_SIZE, checksum);

    unsigned char footer[BLOCK_MANAGER_FOOTER_SIZE];
    encode_uint32_le_compat(footer, size);
    encode_uint32_le_compat(footer + 4, BLOCK_MANAGER_FOOTER_MAGIC);

    struct iovec iov[3];
    iov[0].iov_base = header;
    iov[0].iov_len = BLOCK_MANAGER_BLOCK_HEADER_SIZE;
    iov[1].iov_base = (void *)data;
    iov[1].iov_len = size;
    iov[2].iov_base = footer;
    iov[2].iov_len = BLOCK_MANAGER_FOOTER_SIZE;

    if (BM_UNLIKELY(tdb_pwritev(bm->fd, iov, 3, (off_t)offset) != (ssize_t)total_size))
        return -1;

    ...

    return offset;
}
```

In its simplest form, this function requests the kernel to copy data from the application buffer to the page cache. Space reservation by the thread happens when we do `const int64_t offset = (int64_t)atomic_fetch_add(&bm->current_file_size, total_size);`. The fetch and add operation will happen as one CPU instruction, ensuring no two threads can ever read the same file offset.

The danger of this is that the offset reservation and the actual I/O are not atomic together:

```c
// Step 1 atomic, irreversible
const int64_t offset = (int64_t)atomic_fetch_add(&bm->current_file_size, total_size);

// Step 2 NOT atomic, can fail independently
if (tdb_pwritev(bm->fd, iov, 3, (off_t)offset) != (ssize_t)total_size) return -1;
```

When Step 1 completes, the file region `[offset, offset + total_size)` is permanently claimed. The atomic counter cannot be rolled back because another thread may have already read the new value and claimed the region immediately above it. Step 2 is then the sole mechanism for filling that region with valid data.

If Step 2 fails:

*   The file region was already claimed and will never be claimed again.
    
*   `pwritev` wrote zero bytes (EINTR) or a partial count.
    

This produces a **hole**: a file region of `N + 16` bytes where the size field at the header reads `0x00000000`(just garbage).

## WAL replay during recovery

The recovery path (`tidesdb_wal_recover`) reads blocks sequentially using a cursor:

```c
cursor->current_pos +=
    BLOCK_MANAGER_BLOCK_HEADER_SIZE + (uint64_t)block_size + BLOCK_MANAGER_FOOTER_SIZE;
```

If `block_size == 0`, `cursor_next` returns `-1` immediately. The replay loop breaks. Every block written by every thread after the hole is permanently unreachable via sequential scan, even though those blocks are physically present on disk and structurally valid.

**Add data written after the failed write is silently lost on recovery.**

This breaks the promise of durability because we had acknowledged to the client that the transaction containing those write requests was successfully committed.

This is the hole problem.

![](https://cdn.hashnode.com/uploads/covers/6488728c19ef65fa1e2bc378/0ccb9664-7298-4e6a-854c-b637ace5dfc0.png)

## Proposed solutions

### Wrap mutex around pwritev + offset reclamation

The idea was to wrap `atomic_fetch_add` + `pwritev` pair inside a mutex. Now the two operations are serialised and no other writer can claim an offset until the current write completes.

Even-though this works correctly, it kills the entire purpose of the lock-free write design of TidesDB. The WAL is on the critical write path: every `tidesdb_put` calls it before the memtable apply. Serialising all writers through a single mutex creates a global bottleneck - concurrent writes that currently scale linearly with thread count would degrade to a single-writer queue. TidesDB is explicitly designed to support concurrent writes.

The current design allows N writers to simultaneously write to N different file regions in parallel. Each `pwritev` call is independent. A mutex makes all of them sequential.

### Sentinel block write on failure

If `pwritev` returns an error, write a sentinel block at the reserved offset. A sentinel block is a structurally valid block (correct header, correct footer) whose payload begins with a known magic value (`0x454C4F48`, the ASCII string "HOLE" in little-endian). The WAL replay code knows to skip sentinels.

```plaintext
Sentinel layout at the failed offset:
[size(4)][checksum(4)][HOLE_MAGIC(4)][padding(size-4)][size(4)][FOOTER_MAGIC(4)]
```

On recovery, when the cursor reads a sentinel, it recognises the magic, skips to the next block, and replay continues normally.

This approach elegantly converts a "broken hole" (size = 0, cursor gets stuck) into a "navigable sentinel" (size = original, cursor can advance). The recovery path requires no structural changes. The cursor already knows how to advance past a valid block; it just needs to check the payload magic and treat HOLE blocks as no-ops.

**Why it was not chosen as the primary fix:**

The sentinel write suffers from the same failure mode it is trying to fix. After `pwritev` returns EINTR:

1.  We attempt to write a sentinel to the failed offset.
    
2.  This sentinel write is itself a `pwrite` call.
    
3.  If another EINTR fires during the sentinel write, we now have a second hole at the same offset, except the size field in this new hole is still zero (because the sentinel write wrote 0 bytes). We're back where we started.
    

The sentinel approach transforms a write-time failure into a recovery-time guarantee, but only if the sentinel write itself succeeds. We cannot guarantee that in the presence of repeated signal interruptions without first solving the signal problem. Solving the signal problem is the better root cause fix - once signals cannot interrupt `pwritev`, neither the original write nor the sentinel write will fail due to EINTR, so the sentinel becomes unnecessary.

### Footer validation + cursor skip

```plaintext
1. Read size field at current_pos.
   If size == 0: zero-filled hole. Cannot determine extent. Return -1.

2. Read footer_magic at the footer offset.
   - If pread fails, it means the file truncated before footer. This is a partial write and the cursor advances.
   - If footer_magic != BLOCK_MANAGER_FOOTER_MAGIC, it's a  partial write and the cursor advances.
   - If footer_magic == BLOCK_MANAGER_FOOTER_MAGIC, this signals a complete write so we validate the checksum.
```

The critical insight is that the footer is the **last thing written** in the `pwritev` call. It is physically located at the end of the scatter-gather vector. On a partial write, the footer is either not reached at all or only partially written. It will not contain the correct 4-byte magic. On a complete write with a corrupt data byte (hardware bit-flip after the write), the footer magic is intact because it was written correctly; only the payload bytes changed after the fact.

**Why this was chosen over the sentinel:**

1.  It requires no changes to the write path. The block format already carries all the information needed.
    
2.  It works for partial writes (any number of bytes written, as long as the header survived). The sentinel only works for the EINTR case (0 bytes written, since a partial header would be an even harder recovery scenario).
    
3.  It correctly refuses to skip genuine corruption, preventing silent data loss in the more serious case.
    

### Signal masking around pwritev

Here, we use `pthread_sigmask` to block interrupt signals for the duration of each `pwritev` call. After `pwritev` returns, restore the original signal mask. The signals are not lost, they queue as pending and are delivered as soon as the mask is restored. This is what forms the basis for `tdb_prwritev_safe`.

```c
static ssize_t tdb_pwritev_safe(int fd, const struct iovec *iov, int iovcnt, off_t offset)
{
#ifndef _WIN32
    sigset_t block_set, old_set;
    sigemptyset(&block_set);
    sigaddset(&block_set, SIGALRM);
    pthread_sigmask(SIG_BLOCK, &block_set, &old_set);
    const ssize_t written = pwritev(fd, iov, iovcnt, offset);
    pthread_sigmask(SIG_SETMASK, &old_set, NULL);
    return written;
#else
    return pwritev(fd, iov, iovcnt, offset);
#endif
}
```

The final solution I chose was the combination of signal masking for preventing EINTR errors and footer validation + cursor skip for recovery from short writes.

Much thanks to Alex Padula, creator and maintainer of TidesDB for his constant assistance, guidance and providing insights while I was working on this patch.

## References

Linux signals - [https://man7.org/linux/man-pages/man7/signal.7.html](https://man7.org/linux/man-pages/man7/signal.7.html)

Linux pwrite(2) manual -> [https://man7.org/linux/man-pages/man2/pwrite.2.html](https://man7.org/linux/man-pages/man2/pwrite.2.html)
