---
title: "What graceful shutdowns taught us about running Golang applications in production"
date: 2025-07-19 08:29:00 +0000
categories: [Go Language]
tags: ["Go Language", "networking", "General Programming"]
image:
  path: https://cdn.hashnode.com/res/hashnode/image/stock/unsplash/fd9mIBluHkA/upload/d6d747d7a20eea117429e900911539e4.jpeg
---

Imagine you have been running a Golang web service in production without any issues. Everything is running perfectly, until you decide to deploy a new change to production, then everything bursts into flames.

This article explains in depth how lack of proper application shutdown caused us issues when deploying an new change to production.

## The back-story

We use Supervisor to manage our application processes in our servers. On successful deploy, we expect Supervisord to restart the application. However what we were noticing was quite strange. Supervisor was unable to restart our application, and on tailing logs, what we met was `listen tcp: 8080": bind: address already in use`. But how could this be possible? We were sure supervisor stopped the application. Could another application have taken up the port before supervisor started our application?  
There was only one way to confirm our doubt. We ran `lsof -i :8080` to check which application was listening on the port, but to our surprise, our application was still listening on that port, even after we thought Supervisor had stopped it. We immediately knew this was going to be an interesting problem to tackle.

## Debugging the issue

Our first attempt to fix the issue was to break down the application restart task within the Ansible play that was running our deploy job. This was informed by the fact that we were able to reproduce the issue within the server.

We noticed that running `supervisorctl restart our.service` resulted in the same `address already in use` error we had encountered earlier. So we broke it down into `supervisorctl stop our.service` and `supervisorctl start our.service` and the application was up and running without an issues.

This led us to change how supervisor restarts our application: Separate the stop task from the start task and introduce a timeout of 10 seconds between the two tasks to ensure that our application releases all resources and frees the port it was running on.

We persisted this change in our Ansible playbook and reran the deploy job. Just as we had expected, the deploy ran successfully. This was our deploy to the dev environment. We ran a subsequent deploy to our staging environment which was again successful.

## Release to production

Having successfully debugged the issue and running two successful deploys, it was time to make a release to production.

However, things did not go as expected. The same Ansible play that had successfully deployed the application to dev and staging environments had now failed to deploy to production. Our application was not streaming any logs, it was like it hung. Looking at our Grafana dashboard, it was all smeared with spikes of 502 errors from a different service that depended the Golang service. Our deploy had failed immediately the task to stop the service had ran. In short, **we were down**. This is the last thing you expect when running a service used by a country’s healthcare infrastructure.

A look at our gitlab-ci deploy job gave us a hint. The ten second delay we introduced as a fix to the first issue was now sabotaging us. The application failed to stop after the ten second timeout we had put.

```powershell
elapsed: 10
    msg: Timeout when waiting for localhost:8080 to drain
```

One of our senior platform engineers hinted that we look at how our application was handling termination signals from Supervisor. We were sure supervisor issues a SIGTERM, so our application needed to handle that.

Code never lies and indeed, it didn’t.

```go
go func() {
		// service connections
		if err := srv.ListenAndServe(); err != nil {
			log.Fatalf("listen: %s\n", err)
		}
}()

// Wait for interrupt signal to gracefully shutdown the server
quit := make(chan os.Signal, 1)
signal.Notify(quit, os.Interrupt)
<-quit
log.Println("Shutdown Server ...")
```

This code implies that we service a connection in a goroutine, and block the main program from exiting until we receive an interrupt signal. This looks perfect, the only problem is that we are listening to interrupts only, but Supervisor issues a `SIGTERM`.

This means that the program never receives `SIGTERM` because we didn’t register for it, so it just keeps running until killed by `SIGKILL` . Supervisor and even Kubernetes usually do this, it issues a SIGTERM, and if the application doesn’t exit before a specified duration, then it sends a SIGKILL. The dangers of SIGKILL is that it kills processes abruptly, possibly leaving sockets/ports in `TIME_WAIT` status. This also explains why we had issues with port being in use when the application was trying to start.

Our modified code looked something like this:

```go
go func() {
		// service connections
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			log.Fatalf("listen: %s\n", err)
		}
	}()

// Wait for interrupt signal to gracefully shutdown the server
quit := make(chan os.Signal, 1)
signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
<-quit
log.Println("Shutdown Server ...")
```

This code involves 3 changes.  
1\. Register `syscall.SIGTERM`  
2\. Remove `os.Interrupt` and register `syscall.SIGINT`  
3\. Check that the error we receive in ListenAndServe() is not `http.ErrServerClosed`

Checking the error in this case is quite important. When Shutdown is called, Serve, ListenAndServe, and ListenAndServeTLS immediately return ErrServerClosed. It’s important to make sure the program doesn’t exit and waits instead for Shutdown to return.

`os.Interrupt` and `syscall.SIGINT` both represent interrupt signals. The difference is that os.Interrupt is cross-platform, working both in windows and UNIX-like platforms while syscall.SIGINT is UNIX specific. Since we are running under Supervisor on Linux, it is wise to register `SIGTERM` (and optionally `SIGINT` for development). There’s no need to use `os.Interrupt` in this Linux-only context.

With this change, we reverted back to using `supervisorctl restart our.service` to restart our service.

From our experience, we learnt that graceful shutdowns aren’t just a nice-to-have feature, they are mandatory for running reliable apps, ensuring proper goroutine management to avoid leaks, ports are released in time, data integrity and proper cleanup of resources.
