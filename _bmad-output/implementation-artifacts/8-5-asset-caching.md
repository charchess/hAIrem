# Story 8-5: Asset Caching

**Status:** done

## Story

As a System,
I want to cache generated assets,
So that repeated requests are faster.

## Acceptance Criteria

1. [AC1] Given an asset is generated, when cached, then subsequent requests use cache
2. [AC2] Given cache is full, when new asset arrives, then oldest is evicted
3. [AC3] Given cache is cleared, when triggered, then all cached assets are removed

## Tasks / Subtasks

- [x] Task 1: Implement asset caching
- [x] Task 2: Add cache eviction
- [x] Task 3: Add cache clearing

## Dev Notes

- Asset caching via Redis
- LRU eviction policy
- Cache clear endpoint available

## Status: done
