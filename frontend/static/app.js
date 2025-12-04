/**
 * PPTX POC - Frontend Application
 * Handles API communication, template selection, and UI updates
 */

(function() {
    'use strict';

    // ==========================================================================
    // Configuration
    // ==========================================================================

    const CONFIG = {
        API_BASE_URL: '/api/v1',
        ENDPOINTS: {
            CONFIG: '/api/v1/config',
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
        // Template elements
        templateSelect: null,
        templateDescription: null,
        // Settings elements
        slidesInput: null,
        slidesValue: null,
        temperatureInput: null,
        temperatureValue: null,
        systemPromptInput: null,
        resetBtn: null
    };


    // ==========================================================================
    // State
    // ==========================================================================

    let state = {
        isGenerating: false,
        lastResponse: null,
        // Loaded from API
        defaults: null,
        templates: [],
        // Track if user has modified system prompt
        systemPromptModified: false
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

        // Template elements
        elements.templateSelect = document.getElementById('template');
        elements.templateDescription = document.getElementById('templateDescription');

        // Settings elements
        elements.slidesInput = document.getElementById('slides');
        elements.slidesValue = document.getElementById('slidesValue');
        elements.temperatureInput = document.getElementById('temperature');
        elements.temperatureValue = document.getElementById('temperatureValue');
        elements.systemPromptInput = document.getElementById('systemPrompt');
        elements.resetBtn = document.getElementById('resetBtn');

        // Bind event listeners
        if (elements.form) {
            elements.form.addEventListener('submit', handleFormSubmit);
        }

        // Template change listener
        if (elements.templateSelect) {
            elements.templateSelect.addEventListener('change', handleTemplateChange);
        }

        // Settings change listeners
        if (elements.slidesInput) {
            elements.slidesInput.addEventListener('input', updateSlidesDisplay);
        }
        if (elements.temperatureInput) {
            elements.temperatureInput.addEventListener('input', updateTemperatureDisplay);
        }
        if (elements.systemPromptInput) {
            elements.systemPromptInput.addEventListener('input', () => {
                state.systemPromptModified = true;
            });
        }

        // Reset button
        if (elements.resetBtn) {
            elements.resetBtn.addEventListener('click', handleResetToDefaults);
        }

        // Load configuration from API
        loadConfiguration();
    }


    // ==========================================================================
    // Configuration Loading
    // ==========================================================================

    /**
     * Load configuration (defaults + templates) from API
     */
    async function loadConfiguration() {
        try {
            const response = await fetch(CONFIG.ENDPOINTS.CONFIG);
            if (!response.ok) {
                throw new Error('Failed to load configuration');
            }

            const config = await response.json();
            state.defaults = config.defaults;
            state.templates = config.templates;

            // Populate template dropdown
            populateTemplates();

            // Apply defaults
            applyDefaults();

            updateStatus('Ready to generate presentations', 'info');
        } catch (error) {
            console.error('Failed to load configuration:', error);
            updateStatus('Failed to load configuration. Using fallback defaults.', 'warning');

            // Use fallback defaults
            state.defaults = {
                temperature: 0.15,
                slides: 5,
                language: 'en',
                template: 'general'
            };
            state.templates = [{
                key: 'general',
                name: 'General Presentation',
                description: 'Flexible template for any topic.',
                system_prompt: 'You are a professional presentation designer.'
            }];

            populateTemplates();
            applyDefaults();
        }
    }

    /**
     * Populate template dropdown from loaded templates
     */
    function populateTemplates() {
        if (!elements.templateSelect || !state.templates.length) return;

        elements.templateSelect.innerHTML = '';

        state.templates.forEach(template => {
            const option = document.createElement('option');
            option.value = template.key;
            option.textContent = template.name;
            elements.templateSelect.appendChild(option);
        });

        // Select default template
        if (state.defaults && state.defaults.template) {
            elements.templateSelect.value = state.defaults.template;
        }

        // Update description
        updateTemplateDescription();
    }

    /**
     * Apply default values to form elements
     */
    function applyDefaults() {
        if (!state.defaults) return;

        // Slides
        if (elements.slidesInput) {
            elements.slidesInput.value = state.defaults.slides || 5;
            updateSlidesDisplay();
        }

        // Temperature
        if (elements.temperatureInput) {
            elements.temperatureInput.value = state.defaults.temperature || 0.15;
            updateTemperatureDisplay();
        }

        // System prompt from selected template
        updateSystemPromptFromTemplate();
    }

    /**
     * Update template description text
     */
    function updateTemplateDescription() {
        if (!elements.templateDescription || !elements.templateSelect) return;

        const selectedKey = elements.templateSelect.value;
        const template = state.templates.find(t => t.key === selectedKey);

        if (template) {
            elements.templateDescription.textContent = template.description;
        }
    }

    /**
     * Update system prompt textarea from selected template
     */
    function updateSystemPromptFromTemplate() {
        if (!elements.systemPromptInput || !elements.templateSelect) return;

        const selectedKey = elements.templateSelect.value;
        const template = state.templates.find(t => t.key === selectedKey);

        if (template && template.system_prompt) {
            elements.systemPromptInput.value = template.system_prompt;
            state.systemPromptModified = false;
        }
    }


    // ==========================================================================
    // Event Handlers
    // ==========================================================================

    /**
     * Handle template selection change
     */
    function handleTemplateChange() {
        updateTemplateDescription();

        // Only update system prompt if user hasn't modified it
        if (!state.systemPromptModified) {
            updateSystemPromptFromTemplate();
        }
    }

    /**
     * Handle reset to defaults button
     */
    function handleResetToDefaults() {
        applyDefaults();
        state.systemPromptModified = false;
        updateStatus('Settings reset to defaults', 'info');
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
     * Get current form values
     * @returns {Object} Form values object
     */
    function getFormValues() {
        const selectedKey = elements.templateSelect ? elements.templateSelect.value : 'general';
        const template = state.templates.find(t => t.key === selectedKey);
        const currentSystemPrompt = elements.systemPromptInput ? elements.systemPromptInput.value.trim() : '';
        const templateSystemPrompt = template ? template.system_prompt.trim() : '';

        // Only send system prompt if it differs from template default
        const systemPromptOverride = currentSystemPrompt !== templateSystemPrompt ? currentSystemPrompt : null;

        return {
            template: selectedKey,
            temperature: elements.temperatureInput ? parseFloat(elements.temperatureInput.value) : 0.15,
            slides: elements.slidesInput ? parseInt(elements.slidesInput.value, 10) : 5,
            system: systemPromptOverride
        };
    }


    // ==========================================================================
    // API Functions
    // ==========================================================================

    /**
     * Generate a presentation via the API
     * @param {string} topic - The presentation topic
     * @returns {Promise<Object>} - The API response
     */
    async function generatePresentation(topic) {
        const formValues = getFormValues();

        const requestBody = {
            topic: topic,
            language: 'en',
            template: formValues.template,
            temperature: formValues.temperature,
            slides: formValues.slides
        };

        // Add system prompt only if user customized it
        if (formValues.system) {
            requestBody.system = formValues.system;
        }

        const response = await fetch(CONFIG.ENDPOINTS.GENERATE, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData?.error?.message || `HTTP error ${response.status}`;
            throw new Error(errorMessage);
        }

        return response.json();
    }


    // ==========================================================================
    // Form Submit Handler
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
