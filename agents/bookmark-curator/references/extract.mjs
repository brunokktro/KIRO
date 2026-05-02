#!/usr/bin/env node
// Firefox Bookmark Extractor for bookmark-curator agent
// Usage: node extract.mjs <path-to-bookmarks.json>
//
// Reads Firefox bookmark JSON export, extracts URLs from the
// "Opened Tabs" folder (or all folders), deduplicates against
// existing bookmarks-data.json, and outputs a batch for processing.

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join } from 'path';

const inputFile = process.argv[2];
if (!inputFile) {
  console.error('Usage: node extract.mjs <bookmarks.json>');
  process.exit(1);
}

const BATCH_SIZE = 50;
const DATA_PATH = join(process.env.HOME, '.kiro', 'agents', 'bookmark-curator-data', 'bookmarks-data.json');

// Load existing data for dedup
let existing = new Set();
if (existsSync(DATA_PATH)) {
  try {
    const data = JSON.parse(readFileSync(DATA_PATH, 'utf8'));
    data.forEach(item => existing.add(item.url));
  } catch (e) {
    console.warn('Warning: Could not parse existing bookmarks-data.json');
  }
}

// Recursively extract URLs from Firefox bookmark tree
function extractUrls(node, folder = '') {
  const urls = [];
  if (node.uri && node.uri.startsWith('http')) {
    urls.push({
      url: node.uri,
      title: node.title || '',
      dateAdded: node.dateAdded ? new Date(node.dateAdded / 1000).toISOString() : null,
      folder: folder
    });
  }
  if (node.children) {
    const currentFolder = node.title || folder;
    for (const child of node.children) {
      urls.push(...extractUrls(child, currentFolder));
    }
  }
  return urls;
}

// Parse and extract
const bookmarks = JSON.parse(readFileSync(inputFile, 'utf8'));
const allUrls = extractUrls(bookmarks);
const newUrls = allUrls.filter(b => !existing.has(b.url));

const result = {
  totalInFile: allUrls.length,
  alreadyProcessed: allUrls.length - newUrls.length,
  newCount: newUrls.length,
  newBookmarks: newUrls.slice(0, BATCH_SIZE),
  allNewUrls: newUrls.map(b => b.url),
  hasMore: newUrls.length > BATCH_SIZE
};

writeFileSync('/tmp/bookmark-extract-result.json', JSON.stringify(result, null, 2));
console.log(`Extracted: ${result.totalInFile} total, ${result.newCount} new, batch of ${result.newBookmarks.length}`);
