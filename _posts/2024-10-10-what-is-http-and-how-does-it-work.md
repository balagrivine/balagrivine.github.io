---
title: "What is HTTP and How Does It Work?"
date: 2024-10-10 10:04:09 +0000
categories: [Http]
tags: ["http", "Web Development", "networking"]
image:
  path: https://cdn.hashnode.com/res/hashnode/image/stock/unsplash/f5pTwLHCsAg/upload/04c3f2143f83a6a061db9c56b0891898.jpeg
---

You may have come across the term HTTP maybe in books or even web pages, but have you ever taken time to really understand what it entails. Well let’s take a deep dive, okay not too deep but just the fundamentals of HTTP and how we apply it in building web applications.

HTTP(HyperText Transfer Protocol) is a protocol for transferring hypertext documents, images, videos and other multimedia files over the web. It defines how messages are formatted and transmitted and how web servers and browsers respond to specific commands. HTTP is a client-server protocol, meaning the client, which in this case may be a web browser, initiates a HTTP request to the server and the server on the other hand responds with a HTTP response.

Let’s explore in detail some of the things we have mentioned in the paragraph above.

### What is an HTTP request

An HTTP request is the way a user-agent such as a browser asks for information it needs from a web server. A typical HTTP request contains:

* HTTP version type
    
* an HTTP method
    
* HTTP request headers
    
* an optional HTTP request body
    

Another thing to note is that HTTP requests are stateless, implying that each request carries all information sufficient for it to be understood and processed by the server. Each request from the client does not retain information about previous interactions.

### What is an HTTP method

A HTTP method or sometimes called an HTTP verb is the action an HTTP request expects from the server. Two most common HTTP methods used are “GET“, for retrieving data from the server and “POST” for submitting data to the server for processing. Other HTTP methods include “PUT”, “PATCH” and “DELETE”. These are the fundamental basis on which Restful APIs operate. We’ll learn more about APIs at a later stage.

### What is an HTTP response

An HTTP response just as the name implies is what the client receives from the server in answer to an HTTP request.

A typical HTTP response contains:

* an HTTP status code
    
* HTTP response headers
    
* optional HTTP body
    

Let’s dive in and understand the nuances of an HTTP response:

### What’s an HTTP status code

These are 3-digit codes used to indicate success, failure and other properties about the result of an HTTP request. These codes are broken down as follows:

1. 1XX informational response - the request was received, continue processing
    
2. 2XX successful - request was successfully received, understood and processed
    
3. 3XX redirection - further actions needed to complete the request
    
4. 4XX client error - request contains bad syntax or cannot be fulfilled
    
5. 5XX server error - server failed to fulfil an apparently valid request
    

The “xx” refers to different numbers ranging between 00 to 99

With that we now have a basic understanding of various components of the HTTP protocol and later on we will see how RESTful web services use HTTP to transfer data between different web components.
