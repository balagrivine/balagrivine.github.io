---
title: "When should you fsync directories?"
date: 2026-04-11 09:21:06 +0000
image:
  path: https://cdn.hashnode.com/uploads/covers/6488728c19ef65fa1e2bc378/29bbcb19-7361-4805-9ba8-6787d868eb5b.jpg
---

My [previous article](https://bala-grivine.hashnode.dev/was-your-data-actually-written-to-disk) talked about promises of disk durability, and the fact that you could still lose data even after fsync()-ing a file.

This will be a short blog that builds over the previous one, but views durability from a different angle; the directory.

## What is a directory?

A directory in UNIX-based systems is essentially a regular file, containing some entries, except its inode has special flag bit set to indicate that it's a directory.

These entries are what we call **directory entries** and their contents are defined in the `dirent.h` header file. The entries are essentially mappings from the `inode` number to filename pointing to that inode.

**dirent.h** is the header in the C POSIX library for the C programming language that contains constructs that facilitate directory traversing.

```c
#ifndef DIRENT_H
#define DIRENT_H

#include <sys/types.h>

...

typedef struct {
    ino_t d_ino /*file inode number*/
    char d_name[] /*name of the file within the directory*/
    s64		d_off;
	unsigned short	d_reclen;
	unsigned char	d_type;
} dirent;

/* A type representing a directory stream.*/
typedef struct {
    dirent ent;
} DIR;

...

static DIR *opendir(const char *dirname);

...

#endif /*DIRENT_H*/
```

## Inode

An inode, short form for index node, is a per-file data structure that stores all the metadata pertaining to the file (access rights, time stamps, block maps, extended attributes, etc), except its name.

Each inode has a unique identifier known as an inode number. This number is what directory entries (dirent) use to map inodes to filenames, **since inodes don't contain filenames within them**.

You can use the `ls` command with the `-i` flag to print a file's file inode number.

![](https://cdn.hashnode.com/uploads/covers/6488728c19ef65fa1e2bc378/34b64ae3-4540-402c-8cdb-c48165ae73b2.png)

## Updating file metadata

Here is where we'll see why certain file operations require directory sync to guarantee discoverability of the file across multiple server restarts or machine crashes.

So far, we've learnt that an inode contains file metadata except the filename, and a directory entry contains the inode number and the file name.

![](https://cdn.hashnode.com/uploads/covers/6488728c19ef65fa1e2bc378/b4fcdab3-fd12-44cd-84df-f13ccdd59534.png)

![](https://cdn.hashnode.com/uploads/covers/6488728c19ef65fa1e2bc378/1a49f25d-7573-4847-8813-b764e7ca6dfe.png)

This is a naive example showing the implementation of opening a bitcask directory and creating a WAL file upon startup. The directory sync operation is commented out to simulate failure.

Now incase the program crashes mid operation after the WAL has been created, we risk losing access to the file, even though the write to the file was durable and we called `file.Sync()`.

What sync does is flushing the OS page cache for the referenced file to stable storage. This ensures that the **inode** has been successfully persisted to disk.

But what happens to the directory entry? It will be lost after the crash. This leaves us in a situation where the WAL file has been durably stored on disk but is undiscoverable. The directory entry that had the mapping of inode number to the filename was lost, so there is no way of tracing the file on disk without it's file name.

Now this doesn't only affect file creation, here are the list of file operations that require explicit fsync on the parent directory:

*   File creation - This ensures new filename is linked to its inode on permanent storage. `fsync()` the parent directory to ensure the new filename is linked to its inode on permanent storage. Without this, a crash could result in a "ghost file" where the data exists on disk, but the directory has no record of the filename, making the file unreachable.
    
*   File renaming or moving.
    
*   Deleting or unlinking files.
    
*   Creating or removing subdirectories
    

> Calling fsync() does not necessarily ensure that the entry in the directory containing the file has also reached disk. For that an explicit fsync() on a file descriptor for the directory is also needed.

## Something to ponder on...

How does UNIX-based systems and windows differ in terms of these file operations and the directory durability guarantees?
