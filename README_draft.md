# Finance Tree

Finance Tree is a web app designed to help individuals and small groups manage finances in a more structured and understandable way.

Rather than treating finance as a flat list of income and expenses, Finance Tree lets users organize records through a **branch-based structure**, attach receipts, and generate report files for sharing and review. The app supports transaction tracking, receipt OCR, and report export features such as Excel and PDF. :contentReference[oaicite:0]{index=0} :contentReference[oaicite:1]{index=1} :contentReference[oaicite:2]{index=2}

---

## Why I Built This

Many small groups need to manage money, but they often do not have access to full-scale accounting systems.

This applies to places such as:

- churches and ministry teams
- charity groups
- clubs and student organizations
- small communities or volunteer teams
- people who want more structure than a typical personal finance app

In these environments, financial management often becomes messy for a few common reasons:

- categories become harder to manage over time
- it becomes unclear which expense belongs to which purpose
- receipts and supporting documents are scattered
- reporting usually happens later through manual work
- Excel sheets become harder to maintain as the structure grows

Finance Tree was built to solve that problem by making financial records more **structured, navigable, and explainable**.

---

## Who This App Is For

Finance Tree is especially useful for:

- small organizations that need transparent financial tracking
- teams that manage money by purpose, department, or activity
- users who want to organize transactions by hierarchy instead of a flat category list
- people who need reports and receipt-based records, not just simple bookkeeping

This app is **not intended to replace a full enterprise accounting system**.  
Instead, it is aimed at **small-scale financial operations** that need clarity, structure, and easier reporting.

---

## Core Idea

The key idea of Finance Tree is simple:

> **Manage finance like a tree, not like a flat list.**

Instead of storing every transaction under disconnected labels, users can create and navigate a **branch structure**.

For example:

- Home
  - Worship
  - Mission
  - Education
  - Events

Each transaction can be connected to a branch, which makes it easier to understand:

- where the money belongs
- how spending is grouped
- how sub-items relate to larger categories
- which part of the structure a report should focus on

This makes the data easier to read not only when entering it, but also later when reviewing or explaining it.

---

## Main Features

### 1. Branch-Based Financial Management

Finance Tree allows users to organize their financial structure through branches.

Instead of managing everything under a single long category list, users can build a tree-like structure and view transactions in context. This makes it easier to manage complex or growing financial records. Branch data is stored and retrieved per user, and transactions are linked to branch paths. :contentReference[oaicite:3]{index=3} :contentReference[oaicite:4]{index=4}

### 2. Transaction Tracking

Users can record transactions with:

- date
- amount
- description
- branch
- receipt image

The app supports transaction retrieval by branch and date range, allowing users to focus on a specific part of their financial structure when reviewing records. :contentReference[oaicite:5]{index=5} :contentReference[oaicite:6]{index=6}

### 3. Receipt OCR

To reduce repetitive manual input, Finance Tree includes receipt OCR support.

When a receipt image is uploaded, the system attempts to extract key information such as:

- date
- cash flow amount
- description

This feature is intended to make transaction entry faster and more practical in real usage. :contentReference[oaicite:7]{index=7} :contentReference[oaicite:8]{index=8}

### 4. Report Generation

Finance Tree focuses not only on recording transactions, but also on making them easier to review and explain.

The report system supports:

- date-range filtering
- income and expenditure summaries
- child-branch breakdown
- monthly flow analysis
- downloadable Excel and PDF report files

This is useful for internal reviews, team sharing, or periodic reporting. :contentReference[oaicite:9]{index=9} :contentReference[oaicite:10]{index=10} :contentReference[oaicite:11]{index=11}

### 5. Authentication and Per-User Data Handling

The app includes authentication and token-based access control so each user can manage their own financial structure and records. Backend routing is organized around authentication, database operations, and testing endpoints. :contentReference[oaicite:12]{index=12} :contentReference[oaicite:13]{index=13}

---

## Example Workflow

A typical user flow may look like this:

1. Sign up and log in
2. Create a branch structure that matches the group or purpose
3. Add transactions under the correct branch
4. Upload receipt images when needed
5. Use OCR to reduce manual entry
6. Review records by period or branch
7. Export reports as Excel or PDF for sharing or archiving

This workflow is meant to help users move from simple record-keeping to more structured financial management.

---

## What Makes Finance Tree Different

Many finance apps are built for personal spending logs.

Finance Tree takes a slightly different approach:

- it focuses on **structure**, not just input
- it treats categories as a **tree**, not a flat tag list
- it supports **receipt-based record management**
- it helps users create **report-ready outputs**
- it fits small groups that need clarity but do not want a heavy accounting system

In short, Finance Tree is closer to a **structured financial tracker for small groups** than a typical household expense app.

---

## Current Scope

Finance Tree currently focuses on:

- branch-based transaction management
- receipt handling
- OCR-assisted input
- financial report generation
- user-based data separation

Possible future improvements may include:

- budget vs actual tracking
- role-based permissions
- approval workflows
- audit history
- stronger collaboration features for teams

---

## Tech Stack

### Frontend
- Next.js / React
- Tailwind CSS
- Recharts

### Backend
- FastAPI
- PostgreSQL
- Firebase Storage

### Other
- OCR pipeline for receipt analysis
- Excel and PDF report generation tools

The technical stack is important, but the main goal of this project is not technical complexity itself.  
The goal is to make financial management easier to understand and easier to explain for real users.

---

## Project Goal

Finance Tree was built with the following question in mind:

> How can small groups manage finance more clearly, without needing a full accounting system?

This project is an attempt to answer that question through:

- structured branch management
- practical transaction entry
- receipt-based record keeping
- simpler reporting and sharing

---

## Status

This project is currently a working implementation of the core concept.

It already includes the essential flow of:

- building a branch structure
- recording financial data
- attaching receipts
- generating reports

The long-term direction is to evolve it into a more reliable tool for small organizations that need transparent and manageable financial operations.

---