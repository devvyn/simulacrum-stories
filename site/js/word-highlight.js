/**
 * Word-Level Text Highlight Engine
 *
 * Creates a flowing, diffuse highlight that moves through text
 * in synchrony with audio playback. The text becomes the scrubber.
 *
 * Features:
 * - Word-by-word highlight with warm amber glow
 * - Smooth interpolation between words using requestAnimationFrame
 * - Click-to-seek: click any word to jump audio to that timestamp
 * - Hybrid scroll: auto-scroll only when highlighted word leaves viewport
 * - Graceful fallback when timing data unavailable
 */

(function() {
  'use strict';

  // Configuration
  const CONFIG = {
    glowRadius: 3,           // Number of words to glow on each side
    glowDecay: 0.3,          // How much glow decreases per word distance
    scrollMargin: 150,       // Pixels from edge before auto-scroll triggers
    scrollDuration: 1400,    // Duration of scroll animation in ms
    scrollCooldown: 2000     // Minimum ms between scroll animations
  };

  // Scroll state
  let lastScrollTime = 0;

  // State
  let wordData = null;       // Word timing array: [[start, end, "word"], ...]
  let wordElements = [];     // DOM span elements
  let audio = null;          // Audio element reference
  let isActive = false;      // Whether highlight is currently running
  let animationId = null;    // requestAnimationFrame ID
  let lastWordIndex = -1;    // Last highlighted word index
  let introOffset = 0;       // Seconds of intro before narration starts

  /**
   * Initialize the word highlight system for a chapter.
   *
   * @param {number} chapterNum - Chapter number (1-12)
   * @param {HTMLAudioElement} audioElement - Audio element to sync with
   * @param {object} options - Optional configuration
   * @param {number} options.introOffset - Seconds of intro before narration (default: 0)
   * @returns {Promise<boolean>} - Whether initialization succeeded
   */
  async function init(chapterNum, audioElement, options = {}) {
    audio = audioElement;
    introOffset = options.introOffset || 0;

    if (introOffset > 0) {
      console.log(`[WordHighlight] Applying intro offset: ${introOffset}s`);
    }

    // Load word timing data
    try {
      const response = await fetch(`/js/words/chapter-${String(chapterNum).padStart(2, '0')}-words.json`);
      if (!response.ok) {
        console.log('[WordHighlight] No word timing data for chapter', chapterNum);
        return false;
      }
      const data = await response.json();
      wordData = data.words;
      console.log(`[WordHighlight] Loaded ${wordData.length} words for chapter ${chapterNum}`);
    } catch (e) {
      console.log('[WordHighlight] Failed to load word timing:', e.message);
      return false;
    }

    // Collect word span elements
    wordElements = Array.from(document.querySelectorAll('.w[data-i]'));
    if (wordElements.length === 0) {
      console.log('[WordHighlight] No word spans found in DOM');
      return false;
    }
    console.log(`[WordHighlight] Found ${wordElements.length} word spans`);

    // Set up click-to-seek
    setupClickToSeek();

    // Set up audio event listeners
    audio.addEventListener('play', startHighlight);
    audio.addEventListener('pause', stopHighlight);
    audio.addEventListener('seeked', onSeek);
    audio.addEventListener('ended', stopHighlight);

    // Start if audio is already playing
    if (!audio.paused) {
      startHighlight();
    }

    return true;
  }

  /**
   * Set up click-to-seek on all word elements.
   */
  function setupClickToSeek() {
    wordElements.forEach((el, index) => {
      el.style.cursor = 'pointer';
      el.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();

        // Get timestamp for this word (add introOffset for final audio time)
        if (wordData && index < wordData.length) {
          const [start] = wordData[index];
          const seekTime = start + introOffset;
          audio.currentTime = seekTime;
          if (audio.paused) {
            audio.play();
          }

          // Track interaction
          if (window.saltmereTracker) {
            window.saltmereTracker.trackAudio('click-to-seek', { wordIndex: index, time: seekTime });
          }
        }
      });
    });
  }

  /**
   * Start the highlight animation loop.
   */
  function startHighlight() {
    if (isActive) return;
    isActive = true;
    document.body.classList.add('word-highlight-active');

    // Immediately scroll to current position when starting
    updateHighlight(audio.currentTime, true);

    animate();
  }

  /**
   * Stop the highlight animation loop.
   */
  function stopHighlight() {
    isActive = false;
    document.body.classList.remove('word-highlight-active');
    if (animationId) {
      cancelAnimationFrame(animationId);
      animationId = null;
    }
  }

  /**
   * Handle audio seek events.
   */
  function onSeek() {
    if (isActive) {
      // Clear all read states on seek (user may have gone backwards)
      wordElements.forEach(el => {
        el.classList.remove('w-read', 'w-active', 'w-near');
      });
      lastWordIndex = -1;

      // Force immediate update on seek
      updateHighlight(audio.currentTime, true);
    }
  }

  /**
   * Animation loop using requestAnimationFrame.
   */
  function animate() {
    if (!isActive) return;

    updateHighlight(audio.currentTime);
    animationId = requestAnimationFrame(animate);
  }

  /**
   * Binary search to find current word index for given time.
   */
  function findWordIndex(time) {
    if (!wordData || wordData.length === 0) return -1;

    let lo = 0;
    let hi = wordData.length - 1;

    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1;
      if (wordData[mid][0] <= time) {
        lo = mid;
      } else {
        hi = mid - 1;
      }
    }

    // Verify the word is currently being spoken
    const [start, end] = wordData[lo];
    if (time >= start && time <= end + 0.1) { // Small tolerance
      return lo;
    }

    return lo;
  }

  /**
   * Update highlight for current playback position.
   */
  function updateHighlight(time, forceScroll = false) {
    // Subtract introOffset to get raw transcript time
    const transcriptTime = time - introOffset;

    // Don't highlight during intro - all words stay hot
    if (transcriptTime < 0) {
      // Clear read states during intro (all words unread = hot)
      if (lastWordIndex >= 0) {
        wordElements.forEach(el => {
          el.classList.remove('w-active', 'w-near', 'w-read');
        });
        lastWordIndex = -1;
      }
      return;
    }

    const currentIndex = findWordIndex(transcriptTime);

    if (currentIndex === lastWordIndex && !forceScroll) {
      return; // No change
    }

    // Clear transition zone classes (but preserve w-read for already-read words)
    wordElements.forEach(el => {
      el.classList.remove('w-active', 'w-near');
    });

    if (currentIndex < 0 || currentIndex >= wordElements.length) {
      lastWordIndex = currentIndex;
      return;
    }

    // Calculate progress within current word (0 to 1)
    let progress = 0;
    if (wordData[currentIndex]) {
      const [start, end] = wordData[currentIndex];
      const duration = end - start;
      if (duration > 0) {
        progress = Math.min(1, Math.max(0, (transcriptTime - start) / duration));
      }
    }

    // Apply glow to current word and neighbors
    applyGlow(currentIndex, progress);

    // Auto-scroll if word is off-screen
    if (forceScroll || currentIndex !== lastWordIndex) {
      scrollToWordIfNeeded(currentIndex);
    }

    lastWordIndex = currentIndex;
  }

  /**
   * Apply cooling effect - mark read words and create transition gradient.
   * Unread words glow hot (via CSS), read words cool to default.
   */
  function applyGlow(centerIndex, progress) {
    const radius = CONFIG.glowRadius;

    // Mark all words before the transition zone as read (cooled)
    for (let i = 0; i < centerIndex - radius; i++) {
      if (i >= 0 && i < wordElements.length) {
        wordElements[i].classList.add('w-read');
        wordElements[i].classList.remove('w-active', 'w-near');
      }
    }

    // Apply transition gradient around current word
    for (let offset = -radius; offset <= radius; offset++) {
      const index = centerIndex + offset;
      if (index < 0 || index >= wordElements.length) continue;

      const el = wordElements[index];
      el.classList.remove('w-read'); // Ensure transition zone isn't marked as read

      if (offset < 0) {
        // Words behind current: cooling gradient (more read = less glow)
        const distance = Math.abs(offset);
        const glow = Math.max(0, 1 - (distance * CONFIG.glowDecay) - (progress * 0.2));
        el.style.setProperty('--heat', glow.toFixed(2));
        el.classList.add('w-near');
        el.classList.remove('w-active');
      } else if (offset === 0) {
        // Current word: transition point, glow decreases with progress
        const glow = 1 - (progress * 0.3); // 1.0 down to 0.7 as word completes
        el.style.setProperty('--heat', glow.toFixed(2));
        el.classList.add('w-active');
        el.classList.remove('w-near');
      } else {
        // Words ahead: still hot (unread)
        el.style.setProperty('--heat', '1');
        el.classList.add('w-near');
        el.classList.remove('w-active');
      }
    }
  }

  /**
   * Scroll to word if it's outside the viewport (hybrid scroll).
   * Uses gentle eased animation with cooldown for natural feel.
   */
  function scrollToWordIfNeeded(index) {
    if (index < 0 || index >= wordElements.length) return;

    // Respect cooldown to prevent scroll stacking
    const now = performance.now();
    if (now - lastScrollTime < CONFIG.scrollCooldown) return;

    const el = wordElements[index];
    const rect = el.getBoundingClientRect();
    const margin = CONFIG.scrollMargin;

    // Check if word is outside viewport
    const isAbove = rect.top < margin;
    const isBelow = rect.bottom > window.innerHeight - margin;

    if (isAbove || isBelow) {
      lastScrollTime = now;

      // Calculate target - place word in upper third for reading comfort
      const targetY = window.scrollY + rect.top - (window.innerHeight * 0.35);
      smoothScrollTo(targetY, CONFIG.scrollDuration);
    }
  }

  /**
   * Smooth scroll with gentle easing - feels like natural inertia.
   */
  function smoothScrollTo(targetY, duration) {
    const startY = window.scrollY;
    const distance = targetY - startY;

    // Skip tiny scrolls
    if (Math.abs(distance) < 20) return;

    const startTime = performance.now();

    // Ease-out quart - very gentle deceleration, like a heavy object slowing
    function easeOutQuart(t) {
      return 1 - Math.pow(1 - t, 4);
    }

    function step(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = easeOutQuart(progress);

      window.scrollTo(0, startY + (distance * eased));

      if (progress < 1) {
        requestAnimationFrame(step);
      }
    }

    requestAnimationFrame(step);
  }

  /**
   * Clean up event listeners and state.
   */
  function destroy() {
    stopHighlight();

    if (audio) {
      audio.removeEventListener('play', startHighlight);
      audio.removeEventListener('pause', stopHighlight);
      audio.removeEventListener('seeked', onSeek);
      audio.removeEventListener('ended', stopHighlight);
    }

    // Clear word element styles
    wordElements.forEach(el => {
      el.style.removeProperty('--heat');
      el.classList.remove('w-active', 'w-near', 'w-read');
      el.style.cursor = '';
    });

    wordData = null;
    wordElements = [];
    audio = null;
    lastWordIndex = -1;
  }

  /**
   * Check if word highlight is available for current chapter.
   */
  function isAvailable() {
    return wordData !== null && wordElements.length > 0;
  }

  // Export API
  window.WordHighlight = {
    init,
    destroy,
    isAvailable,
    startHighlight,
    stopHighlight
  };

})();
