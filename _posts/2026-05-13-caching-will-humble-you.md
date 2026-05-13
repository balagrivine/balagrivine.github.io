---
title: "Caching Will Humble You"
date: 2026-05-13 00:00:00 +0000
categories: [Go, Debugging]
tags: ["caching", "golang", "debugging"]
image:
  path: https://cdn.hashnode.com/uploads/covers/6488728c19ef65fa1e2bc378/9e560412-83b8-4c2f-963b-ac54dcd3b2a3.jpg
---

> *There are only two hard things in Computer Science: cache invalidation and naming things*
>
> *-- Phil Karlton*

I recently took on a side-quest to refactor one of the applications I first worked on when joining Savannah Informatics. Honestly, some parts of it were a mess; and specifically the code portions I decided to refactor.

Functions had repetitive code blocks; all which handled getting and inserting items to our cache server. This was really a good candidate for refactoring.

So the first thing here was to extract the cache logic; both fetching and storing items, into separate functions so that any other function that needed to perform cache operations would not have its own logic of doing so, but would just call a function, pass it the item to be cached and a TTL, or a cache key depending on whether the function wants to fetch or store a cache item.

The overall result of this refactor was ~700 lines of code removed from over 20 functions, with each function length almost halved, from about 130 lines to roughly 70 LOC on average.

The above was the happy path; but as we know with every good thing, there are always side-effects. And the refactor I did certainly had to have some really weird ones.

## The failure mode

During UAT on staging, I noticed requests to a certain endpoint became blazing fast; like really fast because latency has dropped from ~4 seconds to around 150ms.

But unlike most cases where a latency drop is good news, this drop was a red flag because we expected any request to that endpoint to modify state but this wasn't the case. All requests were leaving the state of the referenced object in an upstream system unmodified.

Reads were returning stale cached data instead of the current upstream state, so the object appeared unchanged regardless of what the request sent.

What made the diagnosis particularly puzzling was that the stale data persisted well past the 1-minute TTL we had configured. My first instinct was to question the cache server itself, specifically how memcached handles item eviction once a TTL expires. Does it sweep for expired keys proactively on a schedule? Does it wait until a key is accessed and only then check whether it has expired? I was convinced the problem lived somewhere inside the eviction mechanism. I was wrong.

## Root cause

There were 3 contributing factors; I was one of them, the others were Golang and Memcached related.

My mistake was wrapping an `int32` in `time.Duration()`. Go's type system allowed it because both are integer types. Memcached's zero-expiration semantics did the rest.

The bug lived in how the cache TTL was constructed and passed:

```go
func (c *Client) cacheComputedResult(
    cacheKey string,
    result any,
    ttl time.Duration,
) error {
    err = c.memcache.Set(&memcache.Item{
        Key:        cacheKey,
        Value:      result,
        Expiration: int32(ttl.Seconds()),
    })

    return nil
}
```

Two things collide here. First, Go's `time.Duration` is nanoseconds, not seconds:

```go
// A Duration represents the elapsed time between two instants
// as an int64 nanosecond count. The representation limits the
// largest representable duration to approximately 290 years.
type Duration int64
```

Second, memcached's `Expiration` field is seconds, and `0` means "never expire":

```go
// Item is an item to be got or stored in a memcached server.
type Item struct {
    // Key is the Item's key (250 bytes maximum).
    Key string

    // Value is the Item's value.
    Value []byte

    // Expiration is the cache expiration time, in seconds: either a relative
    // time from now (up to 1 month), or an absolute Unix epoch time.
    // Zero means the Item has no expiration time.
    Expiration int32
}
```

```go
var cacheSecondsDefault = int32(1 * 60)
c.cacheComputedResult(cacheKey, item, time.Duration(cacheSecondsDefault))
// time.Duration(60)  →  60 nanoseconds
// ttl.Seconds()      →  ~6e-8
// int32(~6e-8)       →  0
// Expiration: 0      →  never expires
```

The fix was straightforward once the cause was clear; change the constant to a proper `time.Duration` and remove the wrapping:

```go
// before
var cacheSecondsDefault = int32(1 * 60)
c.cacheComputedResult(cacheKey, item, time.Duration(cacheSecondsDefault))

// after
var cacheSecondsDefault = 1 * time.Minute
c.cacheComputedResult(cacheKey, item, cacheSecondsDefault)
```

## Key lesson

The Go compiler won't catch this class of bug because `int32` and `time.Duration` are both integers so the conversion is valid code. The real guard here is to never pass a bare numeric literal or an integer type to `time.Duration()`. If your TTL variable isn't already a `time.Duration`, construct it explicitly with `time.Second` or `time.Minute`.

After a major code overhaul, thoroughly test the changes, both at the unit test level and e2e, to ensure there are no regressions. Secondly, always measure latency numbers before and after significant code changes. This helps you set a performance baseline and you will immediately get to know when things have gone wrong.

Turns out cache invalidation is hard in ways that don't always look like cache problems.

[Falsehoods programmers believe about time](https://gist.github.com/timvisee/fcda9bbdff88d45cc9061606b4b923ca). This link was shared by my director exactly a year ago (2nd May 2025). I just reopened it today and found one of the falsehoods programmers believe is `The smallest unit of time is one second.` — exactly what led to the failure we ran into 😂
