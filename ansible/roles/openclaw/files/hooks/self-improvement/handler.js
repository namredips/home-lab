/**
 * Self-Improvement Hook
 *
 * Processes the agent's MEMORY.md and daily notes to extract
 * learnings, patterns, and insights. Fires on the internal hook trigger.
 *
 * This hook reads recent workspace files and synthesizes observations
 * into structured entries in MEMORY.md.
 */

const fs = require('fs');
const path = require('path');

const WORKSPACE = process.env.OPENCLAW_WORKSPACE || path.join(process.env.HOME, '.openclaw', 'workspace');
const MEMORY_FILE = path.join(WORKSPACE, 'MEMORY.md');
const NOTES_DIR = path.join(WORKSPACE, 'notes');

/**
 * Get today's date as YYYY-MM-DD
 */
function today() {
  return new Date().toISOString().split('T')[0];
}

/**
 * Read a file, returning empty string if it doesn't exist
 */
function readFile(filePath) {
  try {
    return fs.readFileSync(filePath, 'utf8');
  } catch {
    return '';
  }
}

/**
 * Ensure MEMORY.md has the standard section headers
 */
function ensureMemoryStructure(content) {
  const sections = ['## Learnings', '## Patterns', '## Decisions', '## Watch List'];
  let updated = content;

  if (!updated.trim()) {
    updated = '# Agent Memory\n\nThis file persists key insights across sessions.\n\n';
  }

  for (const section of sections) {
    if (!updated.includes(section)) {
      updated += `\n${section}\n\n`;
    }
  }

  return updated;
}

/**
 * Check if today's notes file exists and has content worth processing
 */
function getTodaysNotes() {
  const notesPath = path.join(NOTES_DIR, `${today()}.md`);
  return readFile(notesPath);
}

/**
 * Append a timestamped entry to the Watch List section
 * Used to flag things that recurred or need attention
 */
function appendToWatchList(memory, entry) {
  const timestamp = new Date().toISOString().split('T')[0];
  const marker = '## Watch List';
  const idx = memory.indexOf(marker);

  if (idx === -1) return memory;

  const insertAt = idx + marker.length;
  const newEntry = `\n- [${timestamp}] ${entry}`;
  return memory.slice(0, insertAt) + newEntry + memory.slice(insertAt);
}

/**
 * Main hook handler
 */
async function run() {
  // Ensure notes directory exists
  if (!fs.existsSync(NOTES_DIR)) {
    fs.mkdirSync(NOTES_DIR, { recursive: true });
  }

  // Read and normalize MEMORY.md
  let memory = readFile(MEMORY_FILE);
  memory = ensureMemoryStructure(memory);

  // Read today's notes
  const notes = getTodaysNotes();

  // Check for recurring blockers or patterns in notes
  if (notes) {
    const blockerMatch = notes.match(/blocked[^.]*\./gi) || [];
    const learnMatch = notes.match(/learned[^.]*\./gi) || [];

    if (blockerMatch.length > 1) {
      memory = appendToWatchList(memory, `Recurring blocker pattern in ${today()} notes`);
    }

    if (learnMatch.length > 0) {
      // Notes contain learning entries - signal to agent to consolidate
      memory = appendToWatchList(memory, `New learnings in ${today()} notes - consolidate into ## Learnings`);
    }
  }

  // Write updated MEMORY.md
  fs.writeFileSync(MEMORY_FILE, memory, 'utf8');

  // Return signal to OpenClaw (non-zero exit = hook wants agent attention)
  const needsAttention = notes && notes.includes('TODO:');
  process.exit(needsAttention ? 1 : 0);
}

run().catch((err) => {
  console.error('self-improvement hook error:', err.message);
  process.exit(0); // Don't block agent on hook failure
});
