/**
 * Error tracking and telemetry for Saltmere Chronicles
 * Captures errors with chapter context and audio player state
 *
 * Enhanced with patterns from herbarium-specimen-tools:
 * - Context extraction (chapter, audio state)
 * - Telemetry logging (non-error events)
 * - Rich API for debugging and diagnostics
 */

(function() {
  'use strict';

  const PROJECT_ID = 'saltmere-chronicles';
  const ENDPOINT = '/.netlify/functions/error-report';
  const MAX_STORED = 100;
  const STORAGE_KEY = 'saltmere-error-queue';
  const TELEMETRY_KEY = 'saltmere-telemetry';

  // Get current chapter context
  function getChapterContext() {
    try {
      const match = window.location.pathname.match(/chapter-(\d+)-?([\w-]*)/);
      const chapterNum = match ? parseInt(match[1]) : null;
      const chapterSlug = match ? match[2] : null;

      // Check for feedback state
      const feedbackDiv = document.querySelector('.chapter-feedback');
      const feedbackSubmitted = feedbackDiv?.classList.contains('submitted') || false;

      // Check modality state
      const activeMode = document.querySelector('.chapter-modalities .mode.active');

      return {
        chapter: chapterNum,
        slug: chapterSlug,
        path: window.location.pathname,
        modality: activeMode?.textContent?.trim() || 'unknown',
        feedbackSubmitted: feedbackSubmitted,
        hasAudioPlayer: !!document.querySelector('.chapter-player'),
        scrollPosition: Math.round(window.scrollY),
        viewportHeight: window.innerHeight
      };
    } catch (e) {
      return { error: 'Failed to extract chapter context' };
    }
  }

  // Get audio player metrics
  function getAudioMetrics() {
    try {
      const audio = document.querySelector('.chapter-player audio');
      if (!audio) return null;

      const player = document.querySelector('.chapter-player');
      const sections = document.querySelectorAll('.section-marker');

      return {
        currentTime: Math.round(audio.currentTime),
        duration: Math.round(audio.duration) || null,
        paused: audio.paused,
        playbackRate: audio.playbackRate,
        volume: audio.volume,
        muted: audio.muted,
        readyState: audio.readyState,
        networkState: audio.networkState,
        playerVisible: player?.offsetParent !== null,
        sectionCount: sections.length,
        followTextEnabled: document.body.classList.contains('follow-text-active')
      };
    } catch (e) {
      return null;
    }
  }

  // Get read-along state
  function getReadAlongState() {
    try {
      const highlighted = document.querySelector('.current-section');
      const sections = document.querySelectorAll('.content hr');

      return {
        highlightedSection: highlighted ? Array.from(sections).indexOf(highlighted) : -1,
        totalSections: sections.length,
        followActive: document.body.classList.contains('follow-text-active')
      };
    } catch (e) {
      return null;
    }
  }

  // Queue error for later reporting
  function queueError(error) {
    try {
      const queue = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
      queue.push({
        ...error,
        project: PROJECT_ID,
        timestamp: new Date().toISOString(),
        chapter: getChapterContext(),
        audio: getAudioMetrics()
      });

      // Keep queue bounded
      while (queue.length > MAX_STORED) queue.shift();
      localStorage.setItem(STORAGE_KEY, JSON.stringify(queue));
    } catch (e) {
      // localStorage not available, skip
    }
  }

  // Log telemetry event (non-error)
  function logTelemetry(eventType, data) {
    try {
      const telemetry = JSON.parse(localStorage.getItem(TELEMETRY_KEY) || '[]');
      telemetry.push({
        eventType,
        data,
        project: PROJECT_ID,
        timestamp: new Date().toISOString(),
        chapter: getChapterContext(),
        audio: getAudioMetrics()
      });

      // Keep bounded
      while (telemetry.length > MAX_STORED * 2) telemetry.shift();
      localStorage.setItem(TELEMETRY_KEY, JSON.stringify(telemetry));
    } catch (e) {
      // Skip if localStorage unavailable
    }
  }

  // Report error (queue locally + send to endpoint)
  function reportError(error) {
    const payload = {
      message: error.message || String(error),
      stack: error.stack || null,
      type: error.type || 'error',
      url: window.location.href,
      userAgent: navigator.userAgent
    };

    // Queue locally
    queueError(payload);

    // Attempt to send
    fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...payload,
        chapter: getChapterContext(),
        audio: getAudioMetrics()
      })
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

  // Track audio player interactions
  function trackAudioInteraction(action, details) {
    logTelemetry('audio_interaction', {
      action,
      ...details,
      audio: getAudioMetrics()
    });
  }

  // Track feedback submissions
  function trackFeedback(chapter, response, note) {
    logTelemetry('feedback', {
      chapter,
      response,
      hasNote: !!note
    });
  }

  // Expose API globally
  window.saltmereTracker = {
    // Manual error reporting
    reportError: function(message, extra) {
      reportError({
        message: message,
        type: 'manual',
        extra: extra
      });
    },

    // Telemetry logging
    log: logTelemetry,

    // Audio interaction tracking
    trackAudio: trackAudioInteraction,

    // Feedback tracking
    trackFeedback: trackFeedback,

    // Get current context (for debugging)
    getContext: function() {
      return {
        chapter: getChapterContext(),
        audio: getAudioMetrics(),
        readAlong: getReadAlongState()
      };
    },

    // Export error queue (for diagnostic script)
    exportErrors: function() {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    },

    // Export telemetry (for diagnostic script)
    exportTelemetry: function() {
      return JSON.parse(localStorage.getItem(TELEMETRY_KEY) || '[]');
    },

    // Clear stored data
    clear: function() {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(TELEMETRY_KEY);
      console.log('[SaltmereTracker] Cleared stored data');
    },

    // Get summary stats
    stats: function() {
      const errors = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
      const telemetry = JSON.parse(localStorage.getItem(TELEMETRY_KEY) || '[]');
      return {
        errorCount: errors.length,
        telemetryCount: telemetry.length,
        oldestError: errors[0]?.timestamp || null,
        newestError: errors[errors.length - 1]?.timestamp || null,
        errorTypes: errors.reduce((acc, e) => {
          acc[e.type] = (acc[e.type] || 0) + 1;
          return acc;
        }, {}),
        eventTypes: telemetry.reduce((acc, e) => {
          acc[e.eventType] = (acc[e.eventType] || 0) + 1;
          return acc;
        }, {}),
        chaptersCovered: [...new Set(telemetry.map(t => t.chapter?.chapter).filter(Boolean))]
      };
    },

    // Flush errors to server
    flush: flushQueue
  };

  // Legacy API compatibility
  window.reportError = window.saltmereTracker.reportError;

  // Flush queue on load
  if (document.readyState === 'complete') {
    flushQueue();
  } else {
    window.addEventListener('load', flushQueue);
  }

  console.log('[SaltmereTracker] Initialized for', PROJECT_ID);
})();
