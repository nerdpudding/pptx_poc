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
            HEALTH: '/health',
            CHAT_START: '/api/v1/chat/start',
            CHAT_MESSAGE: '/api/v1/chat',  // + /{session_id}/message
            CHAT_DRAFT: '/api/v1/chat',    // + /{session_id}/draft
            CHAT_GENERATE: '/api/v1/chat'  // + /{session_id}/generate
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
        resetBtn: null,
        // Mode toggle
        quickModeBtn: null,
        guidedModeBtn: null,
        // Chat elements
        chatContainer: null,
        chatTemplate: null,
        chatTemplateDescription: null,
        chatStartSection: null,
        startSessionBtn: null,
        chatMessages: null,
        chatInputArea: null,
        chatInput: null,
        sendBtn: null,
        chatActions: null,
        createDraftBtn: null,
        generateFromDraftBtn: null,
        draftPreviewSection: null,
        draftPreviewContent: null
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
        systemPromptModified: false,
        // Chat/Guided mode state
        chatMode: false,
        sessionId: null,
        chatMessages: [],
        isReadyForDraft: false,
        hasDraft: false,
        isSending: false
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

        // Mode toggle elements
        elements.quickModeBtn = document.getElementById('quickModeBtn');
        elements.guidedModeBtn = document.getElementById('guidedModeBtn');

        // Chat elements
        elements.chatContainer = document.getElementById('chatContainer');
        elements.chatTemplate = document.getElementById('chatTemplate');
        elements.chatTemplateDescription = document.getElementById('chatTemplateDescription');
        elements.chatStartSection = document.getElementById('chatStartSection');
        elements.startSessionBtn = document.getElementById('startSessionBtn');
        elements.chatMessages = document.getElementById('chatMessages');
        elements.chatInputArea = document.getElementById('chatInputArea');
        elements.chatInput = document.getElementById('chatInput');
        elements.sendBtn = document.getElementById('sendBtn');
        elements.chatActions = document.getElementById('chatActions');
        elements.createDraftBtn = document.getElementById('createDraftBtn');
        elements.generateFromDraftBtn = document.getElementById('generateFromDraftBtn');
        elements.draftPreviewSection = document.getElementById('draftPreviewSection');
        elements.draftPreviewContent = document.getElementById('draftPreviewContent');

        // Mode toggle listeners
        if (elements.quickModeBtn) {
            elements.quickModeBtn.addEventListener('click', () => switchMode(false));
        }
        if (elements.guidedModeBtn) {
            elements.guidedModeBtn.addEventListener('click', () => switchMode(true));
        }

        // Chat event listeners
        if (elements.startSessionBtn) {
            elements.startSessionBtn.addEventListener('click', startGuidedSession);
        }
        if (elements.sendBtn) {
            elements.sendBtn.addEventListener('click', sendChatMessage);
        }
        if (elements.chatInput) {
            elements.chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendChatMessage();
                }
            });
        }
        if (elements.createDraftBtn) {
            elements.createDraftBtn.addEventListener('click', createDraft);
        }
        if (elements.generateFromDraftBtn) {
            elements.generateFromDraftBtn.addEventListener('click', generateFromDraft);
        }
        if (elements.chatTemplate) {
            elements.chatTemplate.addEventListener('change', handleChatTemplateChange);
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
    // Mode Switching
    // ==========================================================================

    /**
     * Switch between Quick Mode and Guided Mode
     * @param {boolean} guided - True for guided mode, false for quick mode
     */
    function switchMode(guided) {
        state.chatMode = guided;

        // Update button states
        if (elements.quickModeBtn) {
            elements.quickModeBtn.classList.toggle('active', !guided);
        }
        if (elements.guidedModeBtn) {
            elements.guidedModeBtn.classList.toggle('active', guided);
        }

        // Toggle visibility
        if (elements.form) {
            elements.form.classList.toggle('hidden', guided);
        }
        if (elements.downloadSection) {
            elements.downloadSection.classList.add('hidden');
        }
        if (elements.previewSection) {
            elements.previewSection.classList.add('hidden');
        }
        if (elements.chatContainer) {
            elements.chatContainer.classList.toggle('hidden', !guided);
        }

        // Reset chat state when switching modes
        if (guided) {
            resetChatState();
            populateChatTemplates();
            updateStatus('Select a template and start a guided session', 'info');
        } else {
            updateStatus('Ready to generate presentations', 'info');
        }
    }

    /**
     * Reset chat state for a new session
     */
    function resetChatState() {
        state.sessionId = null;
        state.chatMessages = [];
        state.isReadyForDraft = false;
        state.hasDraft = false;
        state.isSending = false;

        // Reset UI
        if (elements.chatMessages) {
            elements.chatMessages.innerHTML = '';
            elements.chatMessages.classList.add('hidden');
        }
        if (elements.chatInputArea) {
            elements.chatInputArea.classList.add('hidden');
        }
        if (elements.chatActions) {
            elements.chatActions.classList.add('hidden');
        }
        if (elements.chatStartSection) {
            elements.chatStartSection.classList.remove('hidden');
        }
        if (elements.createDraftBtn) {
            elements.createDraftBtn.disabled = true;
            elements.createDraftBtn.classList.remove('ready-highlight');
        }
        if (elements.generateFromDraftBtn) {
            elements.generateFromDraftBtn.disabled = true;
        }
        if (elements.draftPreviewSection) {
            elements.draftPreviewSection.classList.add('hidden');
        }
        if (elements.chatInput) {
            elements.chatInput.value = '';
        }
    }


    // ==========================================================================
    // Chat Template Functions
    // ==========================================================================

    /**
     * Populate chat template dropdown with guided-mode enabled templates
     */
    function populateChatTemplates() {
        if (!elements.chatTemplate || !state.templates.length) return;

        elements.chatTemplate.innerHTML = '';

        // Filter templates that have guided mode enabled
        const guidedTemplates = state.templates.filter(t => t.guided_mode_enabled);

        if (guidedTemplates.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No guided templates available';
            elements.chatTemplate.appendChild(option);
            if (elements.startSessionBtn) {
                elements.startSessionBtn.disabled = true;
            }
            return;
        }

        guidedTemplates.forEach(template => {
            const option = document.createElement('option');
            option.value = template.key;
            option.textContent = template.name;
            elements.chatTemplate.appendChild(option);
        });

        if (elements.startSessionBtn) {
            elements.startSessionBtn.disabled = false;
        }

        updateChatTemplateDescription();
    }

    /**
     * Handle chat template selection change
     */
    function handleChatTemplateChange() {
        updateChatTemplateDescription();
    }

    /**
     * Update chat template description
     */
    function updateChatTemplateDescription() {
        if (!elements.chatTemplateDescription || !elements.chatTemplate) return;

        const selectedKey = elements.chatTemplate.value;
        const template = state.templates.find(t => t.key === selectedKey);

        if (template) {
            elements.chatTemplateDescription.textContent = template.description;
        }
    }


    // ==========================================================================
    // Chat Session Functions
    // ==========================================================================

    /**
     * Start a new guided chat session
     */
    async function startGuidedSession() {
        const template = elements.chatTemplate ? elements.chatTemplate.value : '';

        if (!template) {
            updateStatus('Please select a template', 'error');
            return;
        }

        updateStatus('Starting guided session...', 'info');

        try {
            const response = await fetch(CONFIG.ENDPOINTS.CHAT_START, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ template })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail?.error?.message || 'Failed to start session');
            }

            const data = await response.json();
            state.sessionId = data.session_id;

            // Hide start section, show chat interface
            if (elements.chatStartSection) {
                elements.chatStartSection.classList.add('hidden');
            }
            if (elements.chatMessages) {
                elements.chatMessages.classList.remove('hidden');
            }
            if (elements.chatInputArea) {
                elements.chatInputArea.classList.remove('hidden');
            }
            if (elements.chatActions) {
                elements.chatActions.classList.remove('hidden');
            }

            // Display greeting message
            addChatMessage('assistant', data.message);

            updateStatus('Session started. Describe your idea!', 'success');

            // Focus input
            if (elements.chatInput) {
                elements.chatInput.focus();
            }

        } catch (error) {
            console.error('Failed to start session:', error);
            updateStatus(error.message, 'error');
        }
    }

    /**
     * Send a chat message
     */
    async function sendChatMessage() {
        if (state.isSending || !state.sessionId) return;

        const message = elements.chatInput ? elements.chatInput.value.trim() : '';
        if (!message) return;

        state.isSending = true;
        if (elements.sendBtn) elements.sendBtn.disabled = true;
        if (elements.chatInput) elements.chatInput.value = '';

        // Add user message to chat
        addChatMessage('user', message);

        // Create placeholder for streaming response
        const assistantBubble = addChatMessage('assistant', '', true);

        try {
            const response = await fetch(
                `${CONFIG.ENDPOINTS.CHAT_MESSAGE}/${state.sessionId}/message`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message })
                }
            );

            if (!response.ok) {
                throw new Error('Failed to send message');
            }

            // Read SSE stream
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullContent = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            fullContent += data.content || '';
                            updateChatBubble(assistantBubble, fullContent);

                            if (data.done) {
                                if (data.is_ready_for_draft) {
                                    state.isReadyForDraft = true;
                                    if (elements.createDraftBtn) {
                                        elements.createDraftBtn.disabled = false;
                                        elements.createDraftBtn.classList.add('ready-highlight');
                                    }
                                    updateStatus('Ready to create draft! Click the highlighted button below.', 'success');
                                }
                            }
                        } catch (e) {
                            // Ignore parse errors for incomplete chunks
                        }
                    }
                }
            }

            // Remove streaming indicator
            assistantBubble.classList.remove('streaming');

        } catch (error) {
            console.error('Failed to send message:', error);
            updateChatBubble(assistantBubble, 'Error: Failed to get response. Please try again.');
            assistantBubble.classList.remove('streaming');
        } finally {
            state.isSending = false;
            if (elements.sendBtn) elements.sendBtn.disabled = false;
            if (elements.chatInput) elements.chatInput.focus();
        }
    }

    /**
     * Add a message to the chat display
     * @param {string} role - 'user' or 'assistant'
     * @param {string} content - Message content
     * @param {boolean} streaming - Whether this is a streaming message
     * @returns {HTMLElement} - The chat bubble element
     */
    function addChatMessage(role, content, streaming = false) {
        if (!elements.chatMessages) return null;

        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}`;

        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble' + (streaming ? ' streaming' : '');
        bubble.textContent = content;

        messageDiv.appendChild(bubble);
        elements.chatMessages.appendChild(messageDiv);

        // Scroll to bottom
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

        return bubble;
    }

    /**
     * Update a chat bubble's content
     * @param {HTMLElement} bubble - The bubble element
     * @param {string} content - New content
     */
    function updateChatBubble(bubble, content) {
        if (bubble) {
            bubble.textContent = content;
            // Scroll to bottom
            if (elements.chatMessages) {
                elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
            }
        }
    }


    // ==========================================================================
    // Draft Functions
    // ==========================================================================

    /**
     * Create draft from conversation
     */
    async function createDraft() {
        if (!state.sessionId) return;

        updateStatus('Creating draft...', 'info');
        if (elements.createDraftBtn) {
            elements.createDraftBtn.disabled = true;
            elements.createDraftBtn.classList.remove('ready-highlight');
        }

        try {
            const response = await fetch(
                `${CONFIG.ENDPOINTS.CHAT_DRAFT}/${state.sessionId}/draft`,
                { method: 'POST' }
            );

            if (!response.ok) {
                throw new Error('Failed to create draft');
            }

            const data = await response.json();
            state.hasDraft = true;

            // Show draft preview
            showDraftPreview(data.draft);

            // Enable generate button
            if (elements.generateFromDraftBtn) {
                elements.generateFromDraftBtn.disabled = false;
            }

            updateStatus('Draft created! Review and generate when ready.', 'success');

        } catch (error) {
            console.error('Failed to create draft:', error);
            updateStatus('Failed to create draft. Please try again.', 'error');
            if (elements.createDraftBtn) elements.createDraftBtn.disabled = false;
        }
    }

    /**
     * Show draft preview
     * @param {Object} draft - Draft data
     */
    function showDraftPreview(draft) {
        if (!elements.draftPreviewSection || !elements.draftPreviewContent || !draft) return;

        elements.draftPreviewContent.innerHTML = '';

        if (draft.slides && Array.isArray(draft.slides)) {
            draft.slides.forEach((slide, index) => {
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

                elements.draftPreviewContent.appendChild(slideDiv);
            });
        }

        elements.draftPreviewSection.classList.remove('hidden');
    }

    /**
     * Generate final presentation from draft
     */
    async function generateFromDraft() {
        if (!state.sessionId || !state.hasDraft) return;

        updateStatus('Generating presentation...', 'info');
        if (elements.generateFromDraftBtn) elements.generateFromDraftBtn.disabled = true;

        try {
            const response = await fetch(
                `${CONFIG.ENDPOINTS.CHAT_GENERATE}/${state.sessionId}/generate`,
                { method: 'POST' }
            );

            if (!response.ok) {
                throw new Error('Failed to generate presentation');
            }

            const data = await response.json();

            if (data.success) {
                updateStatus('Presentation generated!', 'success');
                showDownloadSection(data.downloadUrl);
            } else {
                throw new Error(data.error?.message || 'Generation failed');
            }

        } catch (error) {
            console.error('Failed to generate:', error);
            updateStatus('Failed to generate presentation. Please try again.', 'error');
            if (elements.generateFromDraftBtn) elements.generateFromDraftBtn.disabled = false;
        }
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
