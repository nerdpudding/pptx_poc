/**
 * PPTX POC - Frontend Application
 * Handles API communication and UI updates
 */

(function() {
    'use strict';

    // ==========================================================================
    // Configuration
    // ==========================================================================

    const CONFIG = {
        API_BASE_URL: '/api/v1',
        ENDPOINTS: {
            GENERATE: '/api/v1/generate',
            HEALTH: '/health'
        }
    };


    // ==========================================================================
    // DOM Elements
    // ==========================================================================

    const elements = {
        form: null,
        topicInput: null,
        generateButton: null,
        buttonText: null,
        spinner: null,
        statusDiv: null,
        downloadSection: null,
        downloadButton: null,
        previewSection: null,
        previewContent: null,
        // Settings elements
        slidesInput: null,
        slidesValue: null,
        temperatureInput: null,
        temperatureValue: null,
        numCtxSelect: null
    };


    // ==========================================================================
    // State
    // ==========================================================================

    let state = {
        isGenerating: false,
        lastResponse: null
    };


    // ==========================================================================
    // Initialization
    // ==========================================================================

    function init() {
        // Cache DOM elements
        elements.form = document.getElementById('generationForm');
        elements.topicInput = document.getElementById('topic');
        elements.generateButton = document.getElementById('generateBtn');
        elements.buttonText = document.getElementById('buttonText');
        elements.spinner = document.getElementById('spinner');
        elements.statusDiv = document.getElementById('status');
        elements.downloadSection = document.getElementById('downloadSection');
        elements.downloadButton = document.getElementById('downloadBtn');
        elements.previewSection = document.getElementById('previewSection');
        elements.previewContent = document.getElementById('previewContent');

        // Settings elements
        elements.slidesInput = document.getElementById('slides');
        elements.slidesValue = document.getElementById('slidesValue');
        elements.temperatureInput = document.getElementById('temperature');
        elements.temperatureValue = document.getElementById('temperatureValue');
        elements.numCtxSelect = document.getElementById('numCtx');

        // Bind event listeners
        if (elements.form) {
            elements.form.addEventListener('submit', handleFormSubmit);
        }

        // Bind settings change listeners
        if (elements.slidesInput) {
            elements.slidesInput.addEventListener('input', updateSlidesDisplay);
            updateSlidesDisplay(); // Set initial value
        }
        if (elements.temperatureInput) {
            elements.temperatureInput.addEventListener('input', updateTemperatureDisplay);
            updateTemperatureDisplay(); // Set initial value
        }

        // Check API health on load
        checkApiHealth();
    }

    /**
     * Update slides display value
     */
    function updateSlidesDisplay() {
        if (elements.slidesValue && elements.slidesInput) {
            elements.slidesValue.textContent = elements.slidesInput.value;
        }
    }

    /**
     * Update temperature display value
     */
    function updateTemperatureDisplay() {
        if (elements.temperatureValue && elements.temperatureInput) {
            elements.temperatureValue.textContent = parseFloat(elements.temperatureInput.value).toFixed(2);
        }
    }

    /**
     * Get current settings values
     * @returns {Object} Settings object with temperature, num_ctx, slides
     */
    function getSettingsValues() {
        return {
            temperature: elements.temperatureInput ? parseFloat(elements.temperatureInput.value) : 0.15,
            num_ctx: elements.numCtxSelect ? parseInt(elements.numCtxSelect.value, 10) : 122880,
            slides: elements.slidesInput ? parseInt(elements.slidesInput.value, 10) : 5
        };
    }


    // ==========================================================================
    // API Functions
    // ==========================================================================

    /**
     * Check if the API is healthy
     */
    async function checkApiHealth() {
        try {
            const response = await fetch(CONFIG.ENDPOINTS.HEALTH);
            if (response.ok) {
                updateStatus('Ready to generate presentations', 'info');
            } else {
                updateStatus('API is not responding correctly', 'warning');
            }
        } catch (error) {
            updateStatus('Cannot connect to API. Please check if services are running.', 'error');
            console.error('Health check failed:', error);
        }
    }

    /**
     * Generate a presentation via the API
     * @param {string} topic - The presentation topic
     * @returns {Promise<Object>} - The API response
     */
    async function generatePresentation(topic) {
        const settings = getSettingsValues();

        const response = await fetch(CONFIG.ENDPOINTS.GENERATE, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                topic: topic,
                language: 'en',
                temperature: settings.temperature,
                num_ctx: settings.num_ctx,
                slides: settings.slides
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData?.error?.message || `HTTP error ${response.status}`;
            throw new Error(errorMessage);
        }

        return response.json();
    }


    // ==========================================================================
    // Event Handlers
    // ==========================================================================

    /**
     * Handle form submission
     * @param {Event} event - The submit event
     */
    async function handleFormSubmit(event) {
        event.preventDefault();

        if (state.isGenerating) {
            return;
        }

        const topic = elements.topicInput.value.trim();

        if (!topic) {
            updateStatus('Please enter a presentation topic', 'error');
            elements.topicInput.focus();
            return;
        }

        // Validate topic length
        if (topic.length > 500) {
            updateStatus('Topic is too long (max 500 characters)', 'error');
            return;
        }

        setGeneratingState(true);
        hideDownloadSection();
        hidePreviewSection();
        updateStatus('Generating your presentation...', 'info');

        try {
            const data = await generatePresentation(topic);

            if (data.success) {
                state.lastResponse = data;
                updateStatus('Presentation generated successfully!', 'success');
                showDownloadSection(data.downloadUrl);
                showPreviewSection(data.preview);
            } else {
                throw new Error(data.error?.message || 'Generation failed');
            }
        } catch (error) {
            console.error('Generation error:', error);
            updateStatus(escapeHtml(error.message), 'error');
        } finally {
            setGeneratingState(false);
        }
    }


    // ==========================================================================
    // UI Update Functions
    // ==========================================================================

    /**
     * Update the status message
     * @param {string} message - The status message
     * @param {string} type - The status type (info, success, error, warning)
     */
    function updateStatus(message, type) {
        if (!elements.statusDiv) return;

        elements.statusDiv.className = `status status-${type}`;
        // Use textContent to prevent XSS
        elements.statusDiv.textContent = message;
    }

    /**
     * Set the generating state (loading indicator)
     * @param {boolean} isGenerating - Whether generation is in progress
     */
    function setGeneratingState(isGenerating) {
        state.isGenerating = isGenerating;

        if (elements.generateButton) {
            elements.generateButton.disabled = isGenerating;
        }

        if (elements.buttonText) {
            elements.buttonText.textContent = isGenerating ? 'Generating...' : 'Generate Presentation';
        }

        if (elements.spinner) {
            elements.spinner.classList.toggle('hidden', !isGenerating);
        }
    }

    /**
     * Show the download section
     * @param {string} downloadUrl - The download URL
     */
    function showDownloadSection(downloadUrl) {
        if (!elements.downloadSection || !elements.downloadButton) return;

        elements.downloadButton.href = downloadUrl;
        elements.downloadSection.classList.remove('hidden');
    }

    /**
     * Hide the download section
     */
    function hideDownloadSection() {
        if (elements.downloadSection) {
            elements.downloadSection.classList.add('hidden');
        }
    }

    /**
     * Show the preview section with slide content
     * @param {Object} preview - The preview data
     */
    function showPreviewSection(preview) {
        if (!elements.previewSection || !elements.previewContent || !preview) return;

        // Clear previous content
        elements.previewContent.innerHTML = '';

        // Build preview HTML safely
        if (preview.slides && Array.isArray(preview.slides)) {
            preview.slides.forEach((slide, index) => {
                const slideDiv = document.createElement('div');
                slideDiv.className = 'preview-slide';

                const heading = document.createElement('h4');
                heading.textContent = `${index + 1}. ${slide.heading || 'Untitled'}`;
                slideDiv.appendChild(heading);

                if (slide.subheading) {
                    const subheading = document.createElement('p');
                    subheading.textContent = slide.subheading;
                    slideDiv.appendChild(subheading);
                }

                if (slide.bullets && Array.isArray(slide.bullets)) {
                    const ul = document.createElement('ul');
                    slide.bullets.forEach(bullet => {
                        const li = document.createElement('li');
                        li.textContent = bullet;
                        ul.appendChild(li);
                    });
                    slideDiv.appendChild(ul);
                }

                elements.previewContent.appendChild(slideDiv);
            });
        }

        elements.previewSection.classList.remove('hidden');
    }

    /**
     * Hide the preview section
     */
    function hidePreviewSection() {
        if (elements.previewSection) {
            elements.previewSection.classList.add('hidden');
        }
    }


    // ==========================================================================
    // Utility Functions
    // ==========================================================================

    /**
     * Escape HTML to prevent XSS
     * @param {string} text - The text to escape
     * @returns {string} - The escaped text
     */
    function escapeHtml(text) {
        if (typeof text !== 'string') return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }


    // ==========================================================================
    // Initialize on DOM Ready
    // ==========================================================================

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
