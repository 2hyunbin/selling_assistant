// API Configuration
const API_BASE = 'http://localhost:8000';

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendButton = document.getElementById('sendButton');
const listingsGrid = document.getElementById('listingsGrid');
const emptyState = document.getElementById('emptyState');
const loadingOverlay = document.getElementById('loadingOverlay');

// State
let currentListings = [];
let chatHistory = []; // Store conversation history

// === Utility Functions ===

function addLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message loading-message';
    messageDiv.id = 'loading-message';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="loading-dots">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function removeLoadingMessage() {
    const loadingMsg = document.getElementById('loading-message');
    if (loadingMsg) {
        loadingMsg.remove();
    }
}

function formatPrice(price) {
    return new Intl.NumberFormat('ko-KR').format(price) + '원';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return '오늘';
    if (diffDays === 1) return '어제';
    if (diffDays < 7) return `${diffDays}일 전`;
    return date.toLocaleDateString('ko-KR');
}

// === API Functions ===

async function sendMessage(message, history) {
    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message,
                history: history || []
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Chat API error:', error);
        throw error;
    }
}

async function fetchListings(sortBy = 'created_at', sortOrder = 'DESC') {
    try {
        const url = `${API_BASE}/listings?sort_by=${sortBy}&sort_order=${sortOrder}`;
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Listings API error:', error);
        throw error;
    }
}

// === UI Update Functions ===

function addUserMessage(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    messageDiv.innerHTML = `
        <div class="message-content">
            <p>${escapeHtml(message)}</p>
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addBotMessage(response, listings = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';

    // Render markdown
    const markdownContent = marked.parse(response);

    let content = `<div class="markdown-content">${markdownContent}</div>`;

    // Add listing cards if provided
    if (listings && listings.length > 0) {
        content += createListingCardsHTML(listings);
    }

    messageDiv.innerHTML = `<div class="message-content">${content}</div>`;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function createListingCardsHTML(listings) {
    const cardsHTML = listings.map(listing => {
        const imageUrl = listing.image_url || 'https://via.placeholder.com/100';
        return `
            <div class="chat-listing-card" data-listing-id="${listing.id}">
                <img src="${imageUrl}" alt="${escapeHtml(listing.title)}" class="chat-listing-image" />
                <div class="chat-listing-info">
                    <div class="chat-listing-id">ID ${listing.id}</div>
                    <div class="chat-listing-title">${escapeHtml(listing.title)}</div>
                    <div class="chat-listing-price">${formatPrice(listing.price)}</div>
                    <div class="chat-listing-meta">
                        <span>📂 ${escapeHtml(listing.category)}</span>
                        <span>📍 ${escapeHtml(listing.region)}</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    return `<div class="chat-listing-cards">${cardsHTML}</div>`;
}

function renderListings(listings) {
    currentListings = listings;

    if (listings.length === 0) {
        listingsGrid.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }

    listingsGrid.style.display = 'flex';
    emptyState.style.display = 'none';
    listingsGrid.innerHTML = '';

    listings.forEach(listing => {
        const card = createListingCard(listing);
        listingsGrid.appendChild(card);
    });
}

function createListingCard(listing) {
    const card = document.createElement('div');
    card.className = 'listing-card';
    card.dataset.id = listing.id;

    const boostBadge = listing.boost_count > 0
        ? `<span class="boost-badge">🔥 끌어올림 ${listing.boost_count}회</span>`
        : '';

    const imageHTML = listing.image_url
        ? `<img src="${listing.image_url}" alt="${escapeHtml(listing.title)}" class="listing-image" onerror="this.style.display='none'" />`
        : '';

    card.innerHTML = `
        ${imageHTML}
        <div class="listing-info-wrapper">
            <div class="listing-header">
                <div class="listing-title">${escapeHtml(listing.title)}</div>
                <div class="listing-id">ID ${listing.id}</div>
            </div>
            <div class="listing-price">${formatPrice(listing.price)}</div>
            <div class="listing-meta">
                <span>📂 ${escapeHtml(listing.category)}</span>
                <span>📍 ${escapeHtml(listing.region)}</span>
            </div>
            <div class="listing-content">${escapeHtml(listing.content)}</div>
            <div class="listing-footer">
                <span>🕒 ${formatDate(listing.last_boosted_at || listing.created_at)}</span>
                ${boostBadge}
            </div>
        </div>
    `;

    return card;
}

function updateListingCard(listingId) {
    // Highlight updated listing
    const card = document.querySelector(`.listing-card[data-id="${listingId}"]`);
    if (card) {
        // Scroll to center the item first
        card.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
            inline: 'nearest'
        });

        // Apply highlight animation after scrolling
        setTimeout(() => {
            card.classList.add('updated');
            setTimeout(() => {
                card.classList.remove('updated');
            }, 3000); // Increased to 3 seconds
        }, 500); // Wait for scroll to complete
    }
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// === Event Handlers ===

async function handleSendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    // Disable input
    chatInput.disabled = true;
    sendButton.disabled = true;
    chatInput.value = '';

    // Add user message
    addUserMessage(message);

    try {
        // Show loading message in chat
        addLoadingMessage();

        // Send to API with history
        const response = await sendMessage(message, chatHistory);

        // Remove loading message
        removeLoadingMessage();

        // 🔍 DEBUG: API 응답 전체 로그
        console.log('📥 API Response:', response);
        console.log('📋 Actions Taken:', response.actions_taken);

        // Extract listings from query_listings action if exists
        let listings = null;
        if (response.actions_taken && response.actions_taken.length > 0) {
            console.log('🔎 Searching for query_listings in actions...');

            // 모든 query_listings 액션 찾기
            const allQueryActions = response.actions_taken.filter(action => action.tool === 'query_listings');
            console.log(`📊 Found ${allQueryActions.length} query_listings action(s):`, allQueryActions);

            const queryAction = response.actions_taken.find(action => action.tool === 'query_listings');
            if (queryAction && queryAction.result && queryAction.result.listings) {
                listings = queryAction.result.listings;
                console.log(`✅ Using listings from first query_listings (${listings.length} items):`, listings);
            }
        }

        // Add bot response with listings
        addBotMessage(response.response, listings);

        // Update chat history
        chatHistory.push({
            role: 'user',
            content: message
        });
        chatHistory.push({
            role: 'assistant',
            content: response.response
        });

        // Refresh listings if any were updated
        if (response.updated_listings && response.updated_listings.length > 0) {
            await loadListings();

            // Highlight updated listings
            response.updated_listings.forEach(id => {
                updateListingCard(id);
            });
        }

    } catch (error) {
        // Remove loading message
        removeLoadingMessage();

        addBotMessage('죄송합니다. 요청 처리 중 오류가 발생했습니다. 다시 시도해주세요.');
    } finally {
        chatInput.disabled = false;
        sendButton.disabled = false;
        chatInput.focus();
    }
}

async function loadListings() {
    try {
        // Sort by most recently boosted first (last_boosted_at DESC)
        const listings = await fetchListings('last_boosted_at', 'DESC');
        renderListings(listings);
    } catch (error) {
        console.error('Failed to load listings:', error);
    }
}

// === Event Listeners ===

sendButton.addEventListener('click', handleSendMessage);

chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
    }
});

// === Initialize ===

async function init() {
    console.log('🚀 Initializing JOL AI Agent...');

    // Load initial listings
    await loadListings();

    // Focus on input
    chatInput.focus();

    console.log('✅ Ready!');
}

// Start app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
