/**
 * Word-Level Text Highlight Engine
 *
 * Follow text / follow audio - synchronized reading experience.
 *
 * Visual model:
 * - Line-level: warm background on paragraph containing active word
 * - Word-level: text dims as spoken (wick burning down)
 *
 * Scroll behavior:
 * - When paused + scroll: seek to viewport position
 * - When playing: gentle, hesitant autoscroll (respects user)
 * - User scroll during playback: allow, then gently correct
 *
 * Interactions:
 * - Click word while paused: seek + enable follow
 * - End of playback: gracefully disable follow
 * - Visual feedback on state changes
 */

(function() {
  'use strict';

  // Configuration
  const CONFIG = {
    glowRadius: 3,           // Number of words in transition zone
    glowDecay: 0.3,          // How much dim increases per word distance
    scrollMargin: 150,       // Pixels from edge before auto-scroll triggers
    scrollDuration: 1600,    // Duration of scroll animation in ms
    scrollCooldown: 2500,    // Minimum ms between scroll animations
    scrollHesitancy: 800,    // Extra delay after user scroll before auto-correcting
    seekDebounce: 300        // Debounce for scroll-to-seek when paused
  };

  // State
  let wordData = null;
  let wordElements = [];
  let audio = null;
  let isActive = false;
  let animationId = null;
  let lastWordIndex = -1;
  let currentParagraph = null;

  // Scroll state
  let lastScrollTime = 0;
  let userScrollTime = 0;
  let isUserScrolling = false;
  let scrollSeekTimeout = null;

  // Callbacks for external control
  let onFollowEnabled = null;
  let onFollowDisabled = null;

  /**
   * Initialize the word highlight system.
   */
  async function init(chapterNum, audioElement, options = {}) {
    audio = audioElement;
    onFollowEnabled = options.onFollowEnabled || null;
    onFollowDisabled = options.onFollowDisabled || null;

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

    // Set up interactions
    setupClickToSeek();
    setupScrollDetection();

    // Set up audio event listeners
    audio.addEventListener('play', onPlay);
    audio.addEventListener('pause', onPause);
    audio.addEventListener('seeked', onSeek);
    audio.addEventListener('ended', onEnded);

    return true;
  }

  /**
   * Set up click-to-seek on all word elements.
   * When paused, clicking enables follow mode.
   */
  function setupClickToSeek() {
    wordElements.forEach((el, index) => {
      el.style.cursor = 'pointer';
      el.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();

        if (wordData && index < wordData.length) {
          const [start] = wordData[index];
          audio.currentTime = start;

          // If paused, enable follow and start playing
          if (audio.paused) {
            enableFollow();
            audio.play();
          }

          // Visual feedback
          el.classList.add('w-clicked');
          setTimeout(() => el.classList.remove('w-clicked'), 300);

          // Track interaction
          if (window.saltmereTracker) {
            window.saltmereTracker.trackAudio('click-to-seek', { wordIndex: index, time: start });
          }
        }
      });
    });
  }

  /**
   * Detect user scroll to be respectful of their intent.
   */
  function setupScrollDetection() {
    let scrollTimeout;

    window.addEventListener('scroll', () => {
      // Only track user scroll when playing
      if (!audio.paused && isActive) {
        userScrollTime = performance.now();
        isUserScrolling = true;

        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
          isUserScrolling = false;
        }, 150);
      }

      // When paused and follow is active, scroll-to-seek
      if (audio.paused && isActive) {
        handleScrollSeek();
      }
    }, { passive: true });
  }

  /**
   * When paused and user scrolls, seek to visible text.
   */
  function handleScrollSeek() {
    clearTimeout(scrollSeekTimeout);
    scrollSeekTimeout = setTimeout(() => {
      const visibleWord = findWordInViewport();
      if (visibleWord !== null && wordData[visibleWord]) {
        const [start] = wordData[visibleWord];
        audio.currentTime = start;
        updateHighlight(audio.currentTime, false);
      }
    }, CONFIG.seekDebounce);
  }

  /**
   * Find the word closest to the viewport center.
   */
  function findWordInViewport() {
    const viewportCenter = window.innerHeight * 0.4;
    let closestWord = null;
    let closestDistance = Infinity;

    for (let i = 0; i < wordElements.length; i++) {
      const rect = wordElements[i].getBoundingClientRect();
      const wordCenter = rect.top + rect.height / 2;
      const distance = Math.abs(wordCenter - viewportCenter);

      if (distance < closestDistance) {
        closestDistance = distance;
        closestWord = i;
      }

      // Stop searching if we're past the viewport
      if (rect.top > window.innerHeight) break;
    }

    return closestWord;
  }

  /**
   * Enable follow mode.
   */
  function enableFollow() {
    if (isActive) return;
    isActive = true;
    document.body.classList.add('word-highlight-active');

    // Visual feedback
    if (onFollowEnabled) onFollowEnabled();

    // Update immediately
    updateHighlight(audio.currentTime, true);
  }

  /**
   * Disable follow mode gracefully.
   */
  function disableFollow() {
    if (!isActive) return;
    isActive = false;

    // Fade out line highlight
    if (currentParagraph) {
      currentParagraph.classList.remove('line-active');
      currentParagraph = null;
    }

    // Keep word states but stop updating
    if (animationId) {
      cancelAnimationFrame(animationId);
      animationId = null;
    }

    // Delay removing body class for graceful fade
    setTimeout(() => {
      if (!isActive) {
        document.body.classList.remove('word-highlight-active');
      }
    }, 500);

    // Visual feedback
    if (onFollowDisabled) onFollowDisabled();
  }

  /**
   * Handle play event.
   */
  function onPlay() {
    if (isActive) {
      animate();
    }
  }

  /**
   * Handle pause event.
   */
  function onPause() {
    if (animationId) {
      cancelAnimationFrame(animationId);
      animationId = null;
    }
    // Keep isActive true so scroll-to-seek works
  }

  /**
   * Handle seek event.
   */
  function onSeek() {
    // Clear all read states on seek (user may have gone backwards)
    wordElements.forEach(el => {
      el.classList.remove('w-read', 'w-active', 'w-near');
    });
    lastWordIndex = -1;

    if (isActive) {
      updateHighlight(audio.currentTime, true);
    }
  }

  /**
   * Handle playback ended - gracefully disable follow.
   */
  function onEnded() {
    // Mark all words as read
    wordElements.forEach(el => {
      el.classList.add('w-read');
      el.classList.remove('w-active', 'w-near');
    });

    // Gracefully disable
    disableFollow();
  }

  /**
   * Animation loop.
   */
  function animate() {
    if (!isActive || audio.paused) return;

    updateHighlight(audio.currentTime);
    animationId = requestAnimationFrame(animate);
  }

  /**
   * Binary search to find current word index.
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

    return lo;
  }

  /**
   * Update highlight for current playback position.
   */
  function updateHighlight(time, forceScroll = false) {
    // Word timestamps are pre-calibrated to match final audio
    const currentIndex = findWordIndex(time);

    // Don't highlight if before first word
    if (wordData && wordData.length > 0 && time < wordData[0][0]) {
      if (lastWordIndex >= 0) {
        wordElements.forEach(el => {
          el.classList.remove('w-active', 'w-near', 'w-read');
        });
        if (currentParagraph) {
          currentParagraph.classList.remove('line-active');
          currentParagraph = null;
        }
        lastWordIndex = -1;
      }
      return;
    }

    if (currentIndex === lastWordIndex && !forceScroll) {
      return;
    }

    // Clear transition zone classes
    wordElements.forEach(el => {
      el.classList.remove('w-active', 'w-near');
    });

    if (currentIndex < 0 || currentIndex >= wordElements.length) {
      lastWordIndex = currentIndex;
      return;
    }

    // Update line-level highlight (paragraph)
    updateLineHighlight(currentIndex);

    // Apply word-level dimming
    applyWordDimming(currentIndex);

    // Gentle autoscroll
    if (forceScroll || currentIndex !== lastWordIndex) {
      scrollToWordIfNeeded(currentIndex);
    }

    lastWordIndex = currentIndex;
  }

  /**
   * Update the line-level highlight (paragraph background).
   */
  function updateLineHighlight(wordIndex) {
    const el = wordElements[wordIndex];
    const paragraph = el.closest('p');

    if (paragraph !== currentParagraph) {
      if (currentParagraph) {
        currentParagraph.classList.remove('line-active');
      }
      if (paragraph) {
        paragraph.classList.add('line-active');
      }
      currentParagraph = paragraph;
    }
  }

  /**
   * Apply word-level dimming effect.
   */
  function applyWordDimming(centerIndex) {
    const radius = CONFIG.glowRadius;

    // Mark all words before transition zone as read (dimmed)
    for (let i = 0; i < centerIndex - radius; i++) {
      if (i >= 0 && i < wordElements.length) {
        wordElements[i].classList.add('w-read');
      }
    }

    // Transition zone
    for (let offset = -radius; offset <= radius; offset++) {
      const index = centerIndex + offset;
      if (index < 0 || index >= wordElements.length) continue;

      const el = wordElements[index];
      el.classList.remove('w-read');

      if (offset === 0) {
        el.classList.add('w-active');
      } else {
        el.classList.add('w-near');
      }
    }
  }

  /**
   * Scroll to word - gentle and hesitant.
   */
  function scrollToWordIfNeeded(index) {
    if (index < 0 || index >= wordElements.length) return;

    const now = performance.now();

    // Respect cooldown
    if (now - lastScrollTime < CONFIG.scrollCooldown) return;

    // Extra hesitancy if user recently scrolled
    if (now - userScrollTime < CONFIG.scrollHesitancy + CONFIG.scrollCooldown) return;

    const el = wordElements[index];
    const rect = el.getBoundingClientRect();
    const margin = CONFIG.scrollMargin;

    const isAbove = rect.top < margin;
    const isBelow = rect.bottom > window.innerHeight - margin;

    if (isAbove || isBelow) {
      lastScrollTime = now;

      // Place word in upper third
      const targetY = window.scrollY + rect.top - (window.innerHeight * 0.35);
      smoothScrollTo(targetY, CONFIG.scrollDuration);

      // Flash the line to draw attention
      const paragraph = el.closest('p');
      if (paragraph) {
        paragraph.classList.add('line-scrolled-to');
        setTimeout(() => paragraph.classList.remove('line-scrolled-to'), 1200);
      }
    }
  }

  /**
   * Smooth scroll with gentle easing.
   */
  function smoothScrollTo(targetY, duration) {
    const startY = window.scrollY;
    const distance = targetY - startY;

    if (Math.abs(distance) < 20) return;

    const startTime = performance.now();

    function easeOutQuint(t) {
      return 1 - Math.pow(1 - t, 5);
    }

    function step(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = easeOutQuint(progress);

      window.scrollTo(0, startY + (distance * eased));

      if (progress < 1 && isActive) {
        requestAnimationFrame(step);
      }
    }

    requestAnimationFrame(step);
  }

  /**
   * Clean up.
   */
  function destroy() {
    disableFollow();

    if (audio) {
      audio.removeEventListener('play', onPlay);
      audio.removeEventListener('pause', onPause);
      audio.removeEventListener('seeked', onSeek);
      audio.removeEventListener('ended', onEnded);
    }

    wordElements.forEach(el => {
      el.classList.remove('w-active', 'w-near', 'w-read');
      el.style.cursor = '';
    });

    if (currentParagraph) {
      currentParagraph.classList.remove('line-active');
    }

    wordData = null;
    wordElements = [];
    audio = null;
    lastWordIndex = -1;
    currentParagraph = null;
  }

  /**
   * Check if available.
   */
  function isAvailable() {
    return wordData !== null && wordElements.length > 0;
  }

  /**
   * Check if follow is currently active.
   */
  function isFollowActive() {
    return isActive;
  }

  // Export API
  window.WordHighlight = {
    init,
    destroy,
    isAvailable,
    isFollowActive,
    enableFollow,
    disableFollow
  };

})();
