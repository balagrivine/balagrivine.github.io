---
title: "Be Mindful of Your Config Changes"
date: 2026-04-25 21:13:50 +0000
categories: [Configuration Management]
tags: ["configuration management"]
image:
  path: https://cdn.hashnode.com/uploads/covers/6488728c19ef65fa1e2bc378/e6d5b948-8b24-44e9-b86a-64874daf55a8.jpg
---

From Google's SRE book;

> *"The cost of failure is education."*
> 
> ***Devin Carraway***

Yesterday; okay, might not be yesterday depending on when you bump into this :), I decided to explore the idea of having a postmortem culture at my place of work after watching a podcast featuring Marc Brooker, a distinguished engineer at AWS.

I ended up gathering some useful insights which I'll share in this short blog.

## Why systems fail

A lot of factors influence system failure, but one stands out **human errors** in the form of **misconfiguration**.

This Github repository https://github.com/danluu/post-mortems is a goldmine for postmortems from different high-scale companies detailing incidents, the actions taken to mitigate or resolve them and their root cause(s). The category with the most postmortems is **config errors**.

Human error often acts as the silent killer, accounting for over 75% of all downtime incidents, often during routine maintenance.

## Why config management is inherently difficult

Unlike code changes, config changes are harder to stage. Changes to config values are atomic; in the sense that you either change them fully or it seems like they were never changed.

Secondly, staging environments usually have different config values from production environments, meaning that user acceptance testing done on staging environment might succeed, but deployment to production fails because certain config value, ie. database connection string is incorrect leading to unforeseen failures that would never have been caught during the user acceptance test.

We engineers tend to assume a lot of things. Take for example a secret management tool like **Infisical**. When configured with the application correctly, a config change is as simple as logging into the Infisical management UI and navigating to the relevant project where you need to apply your secret changes. Things might go wrong when you change an application secret on Infisical but fail to confirm if the application successfully restarted.

## A recent learning opportunity

We recently encountered this firsthand.

We introduced a new stream to our NATS server, meaning the application would try to create and register the new stream at startup. However, NATS JetStream has a policy that requires unique message ownership; one subject cannot be persisted by two different streams, often triggered by overlapping wildcards.

Our new stream overlapped with subjects already registered in an existing stream. As a result, the application failed to start entirely.

We couldn't delete the old stream because it stores messages other systems were consuming and that would have been more catastrophic. The safest move was to roll back the configuration change.

## What to do

### Have a config rollback strategy

Configuration changes should be reversible just as quickly as they are applied. Whether manual or automated, rollback should be part of the plan.

### Monitor your changes

A successful update in a configuration tool does not mean the system is healthy. Always confirm through logs, metrics, or health checks that the application is functioning as expected.

### Treat config changes like code changes

They may look simpler, but their blast radius is often larger. Apply the same level of caution, validation, and observability.

## Conclusion

Config is one of the easiest ways to change system behaviour, see https://12factor.net/config. It’s also one of the fastest ways to take everything down.

You'll run into this at some point. Hopefully from our mistakes and the lessons we learnt, you will be a little faster at fixing it next time.
