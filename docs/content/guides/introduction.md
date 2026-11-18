# Introduction

The Portalu API provides the core capabilities needed for front-end applications to build and operate client portals.

## What is a Client Portal?

A client portal consists of two complementary experiences:

- **Client-facing experience** — A website or application where final consumers can submit, track, manage, and follow up on requests.
- **Administrative experience** — An internal application where staff can define request types and workflows, manage incoming requests, and handle requests throughout their lifecycle.

The API provides a consistent foundation for both experiences, allowing different types of organizations to build their own client portals without having to implement request management, workflows, and lifecycle handling from scratch.

## Who is this API for?

The API serves three primary groups:

- **Final Consumers** — People who submit and manage requests through a client-facing portal.
- **Internal Staff** — Employees or administrators who configure request types and workflows and manage submitted requests.
- **Organizations** — Organizations that use the API to power their own client portal and configure it according to their operational needs.

## Primary Use Cases

The API supports organizations with different types of request-driven interactions, including:

- **Public organizations** — Citizens submitting and tracking requests for public services.
- **Professional regulatory councils** — Members submitting requests, applications, or inquiries and tracking their progress.
- **Support organizations** — Customers or employees submitting requests for IT, administrative, or other types of support.
- **Other request-driven organizations** — Organizations where external users need to submit, manage, and track requests through a structured workflow.

## Key Scenarios

### Final Consumer

The consumer should be able to:

- **Make a request** — Select a request type and provide the required information.
- **Track a request** — View the current status and relevant information.
- **Manage a request** — Update information or take available actions on an active request.
- **Cancel a request** — Cancel a request when cancellation is permitted.
- **Follow up on a request** — Provide additional information, respond to questions, or continue an interaction related to an existing request.
- **View request history** — Access previous requests and their outcomes.

### Internal Staff

Internal staff should be able to:

- **Define request types** — Create and configure the types of requests an organization accepts.
- **Define workflows** — Configure the steps, statuses, and transitions associated with each request type.
- **Configure required information** — Define what information consumers need to provide for different request types.
- **Manage requests** — Review, update, assign, and process incoming requests.
- **Progress requests through their workflow** — Move requests between appropriate states and perform actions available at each stage.
- **Communicate with consumers** — Request additional information and provide updates related to a request.
- **View request history** — Understand what happened to a request throughout its lifecycle.
