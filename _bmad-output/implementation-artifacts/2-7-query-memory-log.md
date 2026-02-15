# Story 2-7: Query Memory Log

**Status:** done

## Story

As a User,
I want to query the memory log,
So that I can see what memories exist.

## Acceptance Criteria

1. [AC1] Given a query is made, when executed, then memories are returned
2. [AC2] Given filtering is applied, when searched, then only matching memories appear
3. [AC3] Given pagination is used, when browsing, then results are paginated

## Tasks / Subtasks

- [x] Task 1: Implement memory query endpoint
- [x] Task 2: Add filtering support
- [x] Task 3: Add pagination

## Dev Notes

- Query endpoint in apps/h-bridge/src/main.py
- Filtering by agent, date, strength
- Pagination supported

## Status: done
