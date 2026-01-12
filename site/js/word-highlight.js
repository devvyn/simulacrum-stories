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

  // Calibration data from audio-structure.json
  let calibration = null;  // { intro_duration, section_breaks }

  // Scroll state
  let lastScrollTime = 0;
  let userScrollTime = 0;
  let isUserScrolling = false;
  let scrollSeekTimeout = null;

  // Callbacks for external control
  let onFollowEnabled = null;
  let onFollowDisabled = null;

  /**
   * Convert raw transcript time to final audio time.
   * Adds intro_duration and cumulative section break durations.
   */
  function rawToFinal(rawTime) {
    if (!calibration) return rawTime;

    let finalTime = rawTime + calibration.intro_duration;

    // Add durations of all section breaks that occur before this raw time
    for (const brk of calibration.section_breaks) {
      if (brk.raw_position <= rawTime) {
        finalTime += brk.duration;
      }
    }

    return finalTime;
  }

  /**
   * Convert final audio time to raw transcript time.
   * Subtracts intro_duration and cumulative section break durations.
   */
  function finalToRaw(finalTime) {
    if (!calibration) return finalTime;

    // Start by subtracting intro
    let rawTime = finalTime - calibration.intro_duration;
    if (rawTime < 0) return 0;

    // Binary search-like: find which section breaks we've passed in final time
    // and subtract their durations. This is tricky because break positions
    // are in raw time but we're converting from final time.

    // Approach: iteratively subtract breaks we've passed
    let cumulativeBreakDuration = 0;
    for (const brk of calibration.section_breaks) {
      // The break occurs at raw_position in raw time
      // In final time, the break starts at: raw_position + intro + breaks_before_this_one
      const breakStartInFinal = brk.raw_position + calibration.intro_duration + cumulativeBreakDuration;

      if (finalTime >= breakStartInFinal + brk.duration) {
        // We're past this break entirely - subtract its duration
        cumulativeBreakDuration += brk.duration;
      } else if (finalTime >= breakStartInFinal) {
        // We're in the middle of this break (silence) - clamp to break start
        return brk.raw_position;
      } else {
        // We haven't reached this break yet
        break;
      }
    }

    rawTime = finalTime - calibration.intro_duration - cumulativeBreakDuration;
    return Math.max(0, rawTime);
  }

  /**
   * Initialize the word highlight system.
   */
  async function init(chapterNum, audioElement, options = {}) {
    audio = audioElement;
    onFollowEnabled = options.onFollowEnabled || null;
    onFollowDisabled = options.onFollowDisabled || null;

    // Load word timing data and calibration structure in parallel
    try {
      const [wordsResponse, structureResponse] = await Promise.all([
        fetch(`/js/words/chapter-${String(chapterNum).padStart(2, '0')}-words.json`),
        fetch('/js/audio-structure.json')
      ]);

      if (!wordsResponse.ok) {
        console.log('[WordHighlight] No word timing data for chapter', chapterNum);
        return false;
      }

      const wordsData = await wordsResponse.json();
      wordData = wordsData.words;
      console.log(`[WordHighlight] Loaded ${wordData.length} words for chapter ${chapterNum}`);

      // Load calibration data
      if (structureResponse.ok) {
        const structure = await structureResponse.json();
        const chapterKey = String(chapterNum);
        if (structure.chapters && structure.chapters[chapterKey]) {
          calibration = structure.chapters[chapterKey];
          console.log(`[WordHighlight] Calibration: intro=${calibration.intro_duration}s, ${calibration.section_breaks.length} breaks`);
        } else {
          console.log('[WordHighlight] No calibration data for chapter', chapterNum);
          calibration = null;
        }
      } else {
        console.log('[WordHighlight] No audio-structure.json found, using raw timestamps');
        calibration = null;
      }
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
          const [rawStart] = wordData[index];
          // Convert raw timestamp to final audio time
          const finalStart = rawToFinal(rawStart);
          audio.currentTime = finalStart;

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
            window.saltmereTracker.trackAudio('click-to-seek', { wordIndex: index, rawTime: rawStart, finalTime: finalStart });
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
        const [rawStart] = wordData[visibleWord];
        // Convert raw timestamp to final audio time
        audio.currentTime = rawToFinal(rawStart);
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
   * Input is final audio time; converts to raw for searching.
   */
  function findWordIndex(finalTime) {
    if (!wordData || wordData.length === 0) return -1;

    // Convert final audio time to raw transcript time
    const rawTime = finalToRaw(finalTime);

    let lo = 0;
    let hi = wordData.length - 1;

    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1;
      if (wordData[mid][0] <= rawTime) {
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
    const currentIndex = findWordIndex(time);

    // Don't highlight if before first word
    // Convert first word's raw timestamp to final for comparison
    const firstWordFinalTime = wordData && wordData.length > 0 ? rawToFinal(wordData[0][0]) : 0;
    if (wordData && wordData.length > 0 && time < firstWordFinalTime) {
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
    calibration = null;
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
