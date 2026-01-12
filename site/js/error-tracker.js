/**
 * Lightweight error tracking for Simulacrum Stories projects
 * Captures errors and reports them to Netlify Functions
 *
 * Shared pattern - can be copied to other projects
 * Just change PROJECT_ID and ENDPOINT as needed
 */

(function() {
  'use strict';

  const PROJECT_ID = 'saltmere-chronicles';
  const ENDPOINT = '/.netlify/functions/error-report';
  const MAX_STORED = 50;
  const STORAGE_KEY = 'error-tracker-queue';

  // Detect current chapter from URL
  function getCurrentChapter() {
    const match = window.location.pathname.match(/chapter-(\d+)/);
    return match ? parseInt(match[1]) : null;
  }

  // Queue error for reporting
  function queueError(error) {
    try {
      const queue = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
      queue.push({
        ...error,
        project: PROJECT_ID,
        timestamp: new Date().toISOString()
      });

      // Keep queue bounded
      while (queue.length > MAX_STORED) queue.shift();
      localStorage.setItem(STORAGE_KEY, JSON.stringify(queue));
    } catch (e) {
      // localStorage not available, skip
    }
  }

  // Send error to endpoint
  function reportError(error) {
    const payload = {
      message: error.message || String(error),
      stack: error.stack || null,
      type: error.type || 'error',
      url: window.location.href,
      userAgent: navigator.userAgent,
      chapter: getCurrentChapter(),
      project: PROJECT_ID
    };

    // Queue locally as backup
    queueError(payload);

    // Attempt to send
    fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).catch(() => {
      // Silently fail - error is queued locally
    });
  }

  // Flush queued errors on page load
  function flushQueue() {
    try {
      const queue = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
      if (queue.length === 0) return;

      // Send batch
      fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ batch: queue })
      }).then(response => {
        if (response.ok) {
          localStorage.removeItem(STORAGE_KEY);
        }
      }).catch(() => {
        // Keep queue for next attempt
      });
    } catch (e) {
      // Skip if localStorage unavailable
    }
  }

  // Capture unhandled errors
  window.addEventListener('error', (event) => {
    // Skip browser extension errors
    if (event.filename && event.filename.includes('extension')) return;

    reportError({
      message: event.message,
      stack: event.error ? event.error.stack : `${event.filename}:${event.lineno}:${event.colno}`,
      type: 'uncaught'
    });
  });

  // Capture unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    reportError({
      message: event.reason ? (event.reason.message || String(event.reason)) : 'Unhandled rejection',
      stack: event.reason ? event.reason.stack : null,
      type: 'promise'
    });
  });

  // Expose for manual error reporting
  window.reportError = function(message, extra) {
    reportError({
      message: message,
      type: 'manual',
      extra: extra
    });
  };

  // Flush queue on load
  if (document.readyState === 'complete') {
    flushQueue();
  } else {
    window.addEventListener('load', flushQueue);
  }

  console.log('[ErrorTracker] Initialized for', PROJECT_ID);
})();
