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
    scrollMargin: 100,       // Pixels from edge before auto-scroll triggers
    scrollBehavior: 'smooth' // 'smooth' or 'instant'
  };

  // State
  let wordData = null;       // Word timing array: [[start, end, "word"], ...]
  let wordElements = [];     // DOM span elements
  let audio = null;          // Audio element reference
  let isActive = false;      // Whether highlight is currently running
  let animationId = null;    // requestAnimationFrame ID
  let lastWordIndex = -1;    // Last highlighted word index

  /**
   * Initialize the word highlight system for a chapter.
   *
   * @param {number} chapterNum - Chapter number (1-12)
   * @param {HTMLAudioElement} audioElement - Audio element to sync with
   * @returns {Promise<boolean>} - Whether initialization succeeded
   */
  async function init(chapterNum, audioElement) {
    audio = audioElement;

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

        // Get timestamp for this word
        if (wordData && index < wordData.length) {
          const [start] = wordData[index];
          audio.currentTime = start;
          if (audio.paused) {
            audio.play();
          }

          // Track interaction
          if (window.saltmereTracker) {
            window.saltmereTracker.trackAudio('click-to-seek', { wordIndex: index, time: start });
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
    const currentIndex = findWordIndex(time);

    if (currentIndex === lastWordIndex && !forceScroll) {
      return; // No change
    }

    // Clear previous highlights
    wordElements.forEach(el => {
      el.style.setProperty('--glow', '0');
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
        progress = Math.min(1, Math.max(0, (time - start) / duration));
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
   * Apply glow effect to current word and neighbors.
   */
  function applyGlow(centerIndex, progress) {
    const radius = CONFIG.glowRadius;

    for (let offset = -radius; offset <= radius; offset++) {
      const index = centerIndex + offset;
      if (index < 0 || index >= wordElements.length) continue;

      const el = wordElements[index];
      const distance = Math.abs(offset);

      if (distance === 0) {
        // Current word: full glow, modulated by progress
        const glow = 0.7 + (progress * 0.3); // 0.7 to 1.0
        el.style.setProperty('--glow', glow.toFixed(2));
        el.classList.add('w-active');
      } else {
        // Neighbor words: decreasing glow
        const glow = Math.max(0, 1 - (distance * CONFIG.glowDecay));
        el.style.setProperty('--glow', glow.toFixed(2));
        el.classList.add('w-near');
      }
    }
  }

  /**
   * Scroll to word if it's outside the viewport (hybrid scroll).
   */
  function scrollToWordIfNeeded(index) {
    if (index < 0 || index >= wordElements.length) return;

    const el = wordElements[index];
    const rect = el.getBoundingClientRect();
    const margin = CONFIG.scrollMargin;

    // Check if word is outside viewport
    const isAbove = rect.top < margin;
    const isBelow = rect.bottom > window.innerHeight - margin;

    if (isAbove || isBelow) {
      el.scrollIntoView({
        behavior: CONFIG.scrollBehavior,
        block: 'center'
      });
    }
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
      el.style.removeProperty('--glow');
      el.classList.remove('w-active', 'w-near');
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
