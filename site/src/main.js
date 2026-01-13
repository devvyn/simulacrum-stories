/**
 * Saltmere Chronicles - Main Entry Point
 *
 * This module bootstraps all components for chapter pages.
 * Import order matters: error-tracker first for global error handling,
 * then word-highlight, then chapter-player which depends on both.
 */

// Error tracking (sets up global handlers)
import './error-tracker.js';

// Word-level highlight engine
import './word-highlight.js';

// Chapter audio player (imports and uses the above)
import './chapter-player.js';

console.log('[Saltmere] Modules loaded');
