/**
 * Saltmere Chronicles - Chapter Audio Player
 * Sticky footer player with section navigation, localStorage persistence,
 * read-along highlighting, and defect reporting
 */

(function() {
  'use strict';

  // State
  let audioManifest = null;
  let audio = null;
  let currentChapter = null;
  let playerElement = null;
  let readAlongMode = false;
  let sectionElements = [];

  // Get chapter key from current page URL
  function getChapterKey() {
    const path = window.location.pathname;
    const match = path.match(/chapter-(\d+)-([a-z-]+)/);
    if (match) {
      return `chapter-${match[1]}-${match[2]}`;
    }
    return null;
  }

  // Format seconds as M:SS
  function formatTime(seconds) {
    if (isNaN(seconds)) return '0:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  }

  // Save playback position to localStorage
  function savePosition() {
    if (audio && currentChapter) {
      const state = {
        chapter: currentChapter,
        position: audio.currentTime,
        speed: audio.playbackRate
      };
      localStorage.setItem('saltmere-playback', JSON.stringify(state));
    }
  }

  // Load playback position from localStorage
  function loadPosition() {
    try {
      const saved = localStorage.getItem('saltmere-playback');
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (e) {}
    return null;
  }

  // Create player HTML
  function createPlayerHTML(chapterData) {
    const sectionsHTML = chapterData.sections.length > 0
      ? `<div class="player-sections">
          <button class="sections-toggle" aria-expanded="false" aria-controls="sections-list">
            Sections <span class="toggle-icon">▼</span>
          </button>
          <ul id="sections-list" class="sections-list" hidden>
            <li><button data-time="0">Start</button></li>
            ${chapterData.sections.map(s =>
              `<li><button data-time="${s.timestamp}">${s.label}</button></li>`
            ).join('')}
          </ul>
        </div>`
      : '';

    return `
      <div class="chapter-player" role="region" aria-label="Audio player">
        <div class="player-info">
          <span class="player-title">${chapterData.title}</span>
          <span class="player-time">
            <span class="current-time">0:00</span> /
            <span class="duration">${chapterData.duration_display}</span>
          </span>
        </div>
        <div class="player-controls">
          <button class="player-btn skip-back" aria-label="Skip back 15 seconds">
            <span>-15</span>
          </button>
          <button class="player-btn play-pause" aria-label="Play">
            <span class="play-icon">▶</span>
            <span class="pause-icon" hidden>⏸</span>
          </button>
          <button class="player-btn skip-forward" aria-label="Skip forward 15 seconds">
            <span>+15</span>
          </button>
          <input type="range" class="progress-bar" min="0" max="${chapterData.duration}" value="0"
                 aria-label="Playback progress">
          <div class="speed-control">
            <button class="speed-btn" aria-label="Playback speed">1x</button>
          </div>
          ${sectionsHTML}
          <a href="${chapterData.audio}" download class="download-btn" aria-label="Download audio">
            ↓
          </a>
          <button class="read-along-btn" aria-label="Toggle read-along mode">
            Follow Text
          </button>
          <button class="report-issue-btn" aria-label="Report audio issue">
            Report Issue
          </button>
        </div>
        <button class="player-minimize" aria-label="Minimize player">−</button>
      </div>
    `;
  }

  // Initialize player
  function initPlayer(chapterData) {
    currentChapter = getChapterKey();

    // Create audio element
    audio = new Audio(chapterData.audio);
    audio.preload = 'metadata';

    // Create player container
    playerElement = document.createElement('div');
    playerElement.id = 'chapter-player-container';
    playerElement.innerHTML = createPlayerHTML(chapterData);
    document.body.appendChild(playerElement);

    // Get elements
    const player = playerElement.querySelector('.chapter-player');
    const playPauseBtn = player.querySelector('.play-pause');
    const playIcon = player.querySelector('.play-icon');
    const pauseIcon = player.querySelector('.pause-icon');
    const skipBackBtn = player.querySelector('.skip-back');
    const skipForwardBtn = player.querySelector('.skip-forward');
    const progressBar = player.querySelector('.progress-bar');
    const currentTimeEl = player.querySelector('.current-time');
    const speedBtn = player.querySelector('.speed-btn');
    const minimizeBtn = player.querySelector('.player-minimize');
    const sectionsToggle = player.querySelector('.sections-toggle');
    const sectionsList = player.querySelector('.sections-list');

    // Speed options
    const speeds = [0.75, 1, 1.25, 1.5, 2];
    let speedIndex = 1;

    // Load saved position
    const saved = loadPosition();
    if (saved && saved.chapter === currentChapter) {
      audio.currentTime = saved.position;
      progressBar.value = saved.position;
      currentTimeEl.textContent = formatTime(saved.position);
      if (saved.speed) {
        audio.playbackRate = saved.speed;
        speedIndex = speeds.indexOf(saved.speed);
        if (speedIndex === -1) speedIndex = 1;
        speedBtn.textContent = saved.speed + 'x';
      }
    }

    // Play/Pause
    playPauseBtn.addEventListener('click', () => {
      if (audio.paused) {
        audio.play();
      } else {
        audio.pause();
      }
    });

    audio.addEventListener('play', () => {
      playIcon.hidden = true;
      pauseIcon.hidden = false;
      playPauseBtn.setAttribute('aria-label', 'Pause');
    });

    audio.addEventListener('pause', () => {
      playIcon.hidden = false;
      pauseIcon.hidden = true;
      playPauseBtn.setAttribute('aria-label', 'Play');
      savePosition();
    });

    // Skip buttons
    skipBackBtn.addEventListener('click', () => {
      audio.currentTime = Math.max(0, audio.currentTime - 15);
    });

    skipForwardBtn.addEventListener('click', () => {
      audio.currentTime = Math.min(audio.duration, audio.currentTime + 15);
    });

    // Progress bar
    audio.addEventListener('timeupdate', () => {
      progressBar.value = audio.currentTime;
      currentTimeEl.textContent = formatTime(audio.currentTime);
    });

    audio.addEventListener('loadedmetadata', () => {
      progressBar.max = audio.duration;
    });

    progressBar.addEventListener('input', () => {
      audio.currentTime = progressBar.value;
    });

    // Speed control
    speedBtn.addEventListener('click', () => {
      speedIndex = (speedIndex + 1) % speeds.length;
      audio.playbackRate = speeds[speedIndex];
      speedBtn.textContent = speeds[speedIndex] + 'x';
      savePosition();
    });

    // Minimize
    minimizeBtn.addEventListener('click', () => {
      player.classList.toggle('minimized');
      minimizeBtn.textContent = player.classList.contains('minimized') ? '+' : '−';
      minimizeBtn.setAttribute('aria-label',
        player.classList.contains('minimized') ? 'Expand player' : 'Minimize player');
    });

    // Sections toggle
    if (sectionsToggle && sectionsList) {
      sectionsToggle.addEventListener('click', () => {
        const expanded = sectionsToggle.getAttribute('aria-expanded') === 'true';
        sectionsToggle.setAttribute('aria-expanded', !expanded);
        sectionsList.hidden = expanded;
        sectionsToggle.querySelector('.toggle-icon').textContent = expanded ? '▼' : '▲';
      });

      // Section jump buttons
      sectionsList.querySelectorAll('button[data-time]').forEach(btn => {
        btn.addEventListener('click', () => {
          audio.currentTime = parseInt(btn.dataset.time, 10);
          if (audio.paused) audio.play();
          sectionsList.hidden = true;
          sectionsToggle.setAttribute('aria-expanded', 'false');
          sectionsToggle.querySelector('.toggle-icon').textContent = '▼';
        });
      });
    }

    // Save position periodically and on page unload
    setInterval(savePosition, 5000);
    window.addEventListener('beforeunload', savePosition);

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

      switch (e.key) {
        case ' ':
          e.preventDefault();
          if (audio.paused) audio.play();
          else audio.pause();
          break;
        case 'ArrowLeft':
          audio.currentTime = Math.max(0, audio.currentTime - 15);
          break;
        case 'ArrowRight':
          audio.currentTime = Math.min(audio.duration, audio.currentTime + 15);
          break;
      }
    });

    // Report Issue functionality
    const reportBtn = player.querySelector('.report-issue-btn');
    if (reportBtn) {
      reportBtn.addEventListener('click', () => {
        showReportModal(chapterData.title, audio.currentTime);
      });
    }

    // Read-along mode
    const readAlongBtn = player.querySelector('.read-along-btn');
    if (readAlongBtn) {
      initReadAlong(chapterData);
      readAlongBtn.addEventListener('click', () => {
        readAlongMode = !readAlongMode;
        readAlongBtn.textContent = readAlongMode ? 'Following ●' : 'Follow Text';
        readAlongBtn.classList.toggle('active', readAlongMode);
        document.body.classList.toggle('read-along-active', readAlongMode);
        if (readAlongMode) {
          updateReadAlongHighlight();
        } else {
          clearReadAlongHighlight();
        }
      });

      // Update highlight during playback
      audio.addEventListener('timeupdate', () => {
        if (readAlongMode) {
          updateReadAlongHighlight();
        }
      });
    }
  }

  // Initialize read-along by finding section elements in the page
  function initReadAlong(chapterData) {
    // Find all paragraph and section elements in the chapter content
    const content = document.querySelector('.chapter-content, article, main');
    if (!content) return;

    // Get section timestamps from manifest
    const sectionTimes = [0, ...(chapterData.sections || []).map(s => s.timestamp)];

    // Find HR elements (section breaks) or use paragraphs
    const hrs = content.querySelectorAll('hr');
    if (hrs.length > 0) {
      // Group paragraphs by section (between HRs)
      let currentSection = [];
      let sectionIdx = 0;

      Array.from(content.children).forEach(el => {
        if (el.tagName === 'HR') {
          if (currentSection.length > 0) {
            sectionElements.push({
              elements: currentSection,
              startTime: sectionTimes[sectionIdx] || 0,
              endTime: sectionTimes[sectionIdx + 1] || Infinity
            });
            sectionIdx++;
          }
          currentSection = [];
        } else if (el.tagName === 'P') {
          currentSection.push(el);
        }
      });
      // Last section
      if (currentSection.length > 0) {
        sectionElements.push({
          elements: currentSection,
          startTime: sectionTimes[sectionIdx] || 0,
          endTime: Infinity
        });
      }
    } else {
      // No HRs, use paragraphs directly with estimated timing
      const paragraphs = content.querySelectorAll('p');
      const totalDuration = chapterData.duration || 600;
      const avgParaDuration = totalDuration / paragraphs.length;

      paragraphs.forEach((p, i) => {
        sectionElements.push({
          elements: [p],
          startTime: i * avgParaDuration,
          endTime: (i + 1) * avgParaDuration
        });
      });
    }
  }

  // Update which section is highlighted based on current audio time
  function updateReadAlongHighlight() {
    if (!audio || sectionElements.length === 0) return;

    const currentTime = audio.currentTime;
    let activeSection = null;

    for (const section of sectionElements) {
      const isActive = currentTime >= section.startTime && currentTime < section.endTime;
      section.elements.forEach(el => {
        el.classList.toggle('read-along-highlight', isActive);
      });
      if (isActive) {
        activeSection = section;
      }
    }

    // Auto-scroll to keep highlighted section visible
    if (activeSection && activeSection.elements[0]) {
      const el = activeSection.elements[0];
      const rect = el.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      const playerHeight = playerElement ? playerElement.offsetHeight : 100;

      // If element is outside visible area (accounting for player), scroll to it
      if (rect.top < 0 || rect.bottom > viewportHeight - playerHeight) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }

  // Clear all highlighting
  function clearReadAlongHighlight() {
    sectionElements.forEach(section => {
      section.elements.forEach(el => {
        el.classList.remove('read-along-highlight');
      });
    });
  }

  // Show report issue modal
  function showReportModal(chapterTitle, timestamp) {
    // Create modal if it doesn't exist
    let modal = document.querySelector('.report-modal-overlay');
    if (!modal) {
      modal = document.createElement('div');
      modal.className = 'report-modal-overlay';
      modal.innerHTML = `
        <div class="report-modal" role="dialog" aria-labelledby="report-modal-title">
          <h3 id="report-modal-title">Report Audio Issue</h3>
          <p>Help us improve the audio quality by reporting any issues you notice.</p>
          <div class="timestamp-display">
            <strong>Chapter:</strong> <span class="report-chapter"></span><br>
            <strong>Timestamp:</strong> <span class="report-timestamp"></span>
          </div>
          <label for="report-issue-type" class="sr-only">Issue Type</label>
          <select id="report-issue-type" class="issue-type-select">
            <option value="">Select issue type...</option>
            <option value="cut-off">Word cut off or clipped</option>
            <option value="wrong-word">Wrong word or mispronunciation</option>
            <option value="timing">Timing/pacing issue</option>
            <option value="audio-quality">Audio quality problem</option>
            <option value="other">Other</option>
          </select>
          <textarea placeholder="Describe the issue (e.g., 'The word Sarah is clipped at the beginning')"></textarea>
          <div class="report-modal-buttons">
            <button class="cancel-btn">Cancel</button>
            <button class="submit-btn">Submit Report</button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
    }

    // Update modal content
    modal.querySelector('.report-chapter').textContent = chapterTitle;
    modal.querySelector('.report-timestamp').textContent = formatTime(timestamp);
    modal.querySelector('textarea').value = '';
    modal.querySelector('select').value = '';
    modal.hidden = false;

    // Store timestamp for submission
    modal.dataset.timestamp = timestamp;
    modal.dataset.chapter = currentChapter;

    // Event listeners
    const cancelBtn = modal.querySelector('.cancel-btn');
    const submitBtn = modal.querySelector('.submit-btn');
    const overlay = modal;

    const closeModal = () => {
      modal.hidden = true;
    };

    cancelBtn.onclick = closeModal;
    overlay.onclick = (e) => {
      if (e.target === overlay) closeModal();
    };

    submitBtn.onclick = () => {
      const issueType = modal.querySelector('select').value;
      const description = modal.querySelector('textarea').value;

      if (!issueType) {
        alert('Please select an issue type.');
        return;
      }

      // Submit to Netlify Forms
      const formData = new FormData();
      formData.append('form-name', 'audio-issue-report');
      formData.append('chapter', modal.dataset.chapter);
      formData.append('timestamp', modal.dataset.timestamp);
      formData.append('timestamp-display', formatTime(parseFloat(modal.dataset.timestamp)));
      formData.append('issue-type', issueType);
      formData.append('description', description);

      fetch('/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams(formData).toString()
      })
      .then(() => {
        modal.querySelector('.report-modal').innerHTML = `
          <h3>Thank You!</h3>
          <p>Your report has been submitted. We appreciate your help improving the audio quality.</p>
          <div class="report-modal-buttons">
            <button class="cancel-btn">Close</button>
          </div>
        `;
        modal.querySelector('.cancel-btn').onclick = closeModal;
      })
      .catch(() => {
        alert('Failed to submit report. Please try again.');
      });
    };

    // Focus the select for accessibility
    setTimeout(() => modal.querySelector('select').focus(), 100);
  }

  // Add modality header to chapter page
  function addModalityHeader(chapterData) {
    const chapterHeader = document.querySelector('.chapter-header, header');
    if (!chapterHeader) return;

    const existingModality = chapterHeader.querySelector('.chapter-modalities');
    if (existingModality) return;

    const modalityDiv = document.createElement('div');
    modalityDiv.className = 'chapter-modalities';

    if (chapterData) {
      modalityDiv.innerHTML = `
        <span class="mode active">Read</span>
        <button class="mode" id="listen-mode-btn">Listen (${chapterData.duration_display})</button>
        <a href="${chapterData.audio}" download class="mode-download">Download MP3</a>
      `;

      // Listen button scrolls to player and starts playback
      modalityDiv.querySelector('#listen-mode-btn').addEventListener('click', () => {
        if (audio) {
          audio.play();
          playerElement.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
      });
    } else {
      modalityDiv.innerHTML = `
        <span class="mode active">Read</span>
        <span class="mode-pending">Audio in production</span>
      `;
    }

    chapterHeader.appendChild(modalityDiv);
  }

  // Main initialization
  async function init() {
    const chapterKey = getChapterKey();
    if (!chapterKey) return; // Not on a chapter page

    try {
      // Load manifest
      const response = await fetch('/js/audio-manifest.json');
      audioManifest = await response.json();

      const chapterData = audioManifest[chapterKey];

      // Add modality header (always, even if no audio)
      addModalityHeader(chapterData);

      // Initialize player if audio exists
      if (chapterData) {
        initPlayer(chapterData);
      }
    } catch (e) {
      console.error('Failed to initialize chapter player:', e);
    }
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
