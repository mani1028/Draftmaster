// --- State ---
let currentDraftId = null;
let allTemplates = [];

// Configuration for Dynamic Dropdowns
const CATEGORY_SETTINGS = {
    'Email': {
        tones: ['Professional', 'Friendly', 'Urgent', 'Apologetic', 'Firm'],
        audiences: ['Client', 'Colleague', 'Manager', 'Vendor', 'General']
    },
    'Business': {
        tones: ['Professional', 'Persuasive', 'Luxury / Enterprise', 'Strategic', 'Formal'],
        audiences: ['Client', 'Investor', 'Partner', 'Internal Team', 'Executive']
    },
    'Marketing': {
        tones: ['Persuasive', 'Exciting', 'Witty', 'Urgent', 'Professional'],
        audiences: ['Target Customer', 'Social Media', 'Subscribers', 'General']
    },
    'HR': {
        tones: ['Professional', 'Empathetic', 'Direct', 'Formal', 'Encouraging'],
        audiences: ['Employee', 'Manager', 'All Staff', 'Candidate']
    },
    'Legal': {
        tones: ['Professional', 'Authoritative', 'Direct', 'Formal', 'Risk-Averse'],
        audiences: ['Client', 'Legal Counsel', 'Court', 'General Business']
    },
    'Sales': {
        tones: ['Persuasive', 'Confident', 'Urgent', 'Professional', 'Solution-Oriented'],
        audiences: ['Prospect', 'Decision Maker', 'Client', 'Gatekeeper']
    },
    'Personal': {
        tones: ['Friendly', 'Emotional', 'Sincere', 'Witty', 'Apologetic'],
        audiences: ['Friend/Family', 'Partner', 'General', 'Social Media']
    },
    'Student': {
        tones: ['Academic', 'Formal', 'Persuasive', 'Enthusiastic'],
        audiences: ['Professor', 'Admissions Committee', 'Employer', 'General']
    },
    'Letter': {
        tones: ['Formal', 'Polite', 'Sincere', 'Direct'],
        audiences: ['Official', 'HR', 'Bank', 'Embassy', 'General']
    },
    'Proposal': {
        tones: ['Persuasive', 'Confident', 'Professional', 'Detailed'],
        audiences: ['Client', 'Investor', 'Board', 'Committee']
    },
    'General': {
        tones: ['Professional', 'Friendly', 'Persuasive', 'Confident', 'Direct'],
        audiences: ['General', 'Executive', 'Client', 'Team', 'Expert']
    }
};

document.addEventListener('DOMContentLoaded', () => {
    loadTemplates();
});

// --- Layout Functions ---
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
    
    // Close config panel if open on mobile
    const configPanel = document.getElementById('configPanel');
    if(configPanel && configPanel.classList.contains('mobile-visible')) {
        configPanel.classList.remove('mobile-visible');
    }
}

function toggleConfigPanel() {
    const panel = document.getElementById('configPanel');
    panel.classList.toggle('mobile-visible');
    
    // Close sidebar if open on mobile
    const sidebar = document.getElementById('sidebar');
    if(sidebar && sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
    }
}

function switchTab(tabName, event) {
    // Hide all main views
    const views = ['generatorView', 'historyView', 'templatesView'];
    views.forEach(id => {
        const el = document.getElementById(id);
        if(el) el.classList.add('hidden');
    });

    // Show selected view
    let targetId = '';
    if(tabName === 'generator') {
        targetId = 'generatorView';
    } else if (tabName === 'history') {
        targetId = 'historyView';
        loadHistory();
    } else if (tabName === 'templates') {
        targetId = 'templatesView';
        renderTemplatesPage();
        updateTitle('Template Library');
    }
    
    if(targetId) {
        const target = document.getElementById(targetId);
        target.classList.remove('hidden');
    }
    
    // Update Sidebar Active State
    // Remove active from all nav items
    document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
    
    // Add active to clicked item if event is provided
    if(event && event.currentTarget) {
        event.currentTarget.classList.add('active');
    } else if (tabName === 'generator') {
        // Fallback for programmatic switches to generator
        const editorBtn = document.querySelector('.nav-item[onclick*="generator"]');
        if (editorBtn) editorBtn.classList.add('active');
    }
    
    if(window.innerWidth <= 1024) {
        document.getElementById('sidebar').classList.remove('open');
    }
}

function updateTitle(text) {
    const crumbActive = document.querySelector('.crumb-active');
    if(crumbActive) crumbActive.innerText = text;
}

// --- Template Functions ---
async function loadTemplates() {
    try {
        const res = await fetch('/api/templates');
        allTemplates = await res.json();
        populateCategoryDropdown();
    } catch (e) {
        console.error(e);
        showToast("Error loading templates", "error");
    }
}

function populateCategoryDropdown() {
    const select = document.getElementById('categorySelect');
    if (!select) return;
    
    const categories = [...new Set(allTemplates.map(t => t.category))].sort();
    
    select.innerHTML = '<option value="" disabled selected>Select Category...</option>';
    categories.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat;
        option.innerText = cat;
        select.appendChild(option);
    });
}

function handleCategoryChange(category) {
    const templateContainer = document.getElementById('templateContainer');
    const templateSelect = document.getElementById('templateSelect');
    
    // Enable the container
    templateContainer.classList.remove('disabled');
    
    const filteredTemplates = allTemplates.filter(t => t.category === category);
    
    templateSelect.innerHTML = '<option value="" disabled selected>Select Template...</option>';
    
    filteredTemplates.forEach((t, index) => {
        const option = document.createElement('option');
        option.value = index; 
        option.innerText = t.title;
        templateSelect.appendChild(option);
    });
    
    templateSelect.dataset.templates = JSON.stringify(filteredTemplates);
    updateFormOptions(category);
}

function handleTemplateChange(index) {
    const templateSelect = document.getElementById('templateSelect');
    const templates = JSON.parse(templateSelect.dataset.templates || '[]');
    const t = templates[index];
    
    if (t) {
        fillTemplateData(t);
    }
}

function filterTemplates(cat, event) {
    // Sidebar highlight
    document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
    if(event && event.currentTarget) event.currentTarget.classList.add('active');

    if (cat === 'All') {
        switchTab('templates'); 
    } else {
        switchTab('generator');
        
        // Auto-select category
        const categorySelect = document.getElementById('categorySelect');
        categorySelect.value = cat;
        
        handleCategoryChange(cat);
    }
    
    if(window.innerWidth <= 1024) {
        if(cat !== 'All') {
            document.getElementById('configPanel').classList.add('mobile-visible');
        }
        document.getElementById('sidebar').classList.remove('open');
    }
}

function renderTemplatesPage() {
    const container = document.getElementById('allTemplatesContainer');
    container.innerHTML = '';
    
    if (allTemplates.length === 0) {
        container.innerHTML = '<div class="empty-state">No templates found.</div>';
        return;
    }

    allTemplates.forEach(t => {
        const card = document.createElement('div');
        card.className = 'draft-card'; 
        card.innerHTML = `
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
                <div style="width: 40px; height: 40px; background: rgba(79, 70, 229, 0.1); color: var(--primary); border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                    <i class="fas fa-file-alt"></i>
                </div>
                <div>
                    <div style="font-size:0.75rem; font-weight:700; color:var(--primary); text-transform:uppercase; letter-spacing:0.05em;">${t.category}</div>
                    <div style="font-size:0.75rem; color:var(--text-muted);">${t.subcategory}</div>
                </div>
            </div>
            <div style="font-weight: 700; color: var(--text-main); font-size:1.1rem;">${t.title}</div>
            <p style="font-size: 0.9rem; color: var(--text-muted); margin-top:0.75rem; line-height:1.5; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;">
                ${t.prompt}
            </p>
        `;
        card.onclick = () => selectTemplateFromCard(t);
        container.appendChild(card);
    });
}

function selectTemplateFromCard(t) {
    // Use null for event since we are programmatically switching
    switchTab('generator', null);
    
    // Highlight "Editor" in sidebar manually
    document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
    const editorBtn = document.querySelector('.nav-item[onclick*="generator"]');
    if (editorBtn) editorBtn.classList.add('active');
    
    const categorySelect = document.getElementById('categorySelect');
    categorySelect.value = t.category;
    
    handleCategoryChange(t.category);
    
    const templateSelect = document.getElementById('templateSelect');
    const templates = JSON.parse(templateSelect.dataset.templates);
    const idx = templates.findIndex(temp => temp.title === t.title);
    if(idx !== -1) {
        templateSelect.value = idx;
    }
    
    fillTemplateData(t);
}

function fillTemplateData(t) {
    document.getElementById('docTitle').value = t.title;
    document.getElementById('userPrompt').value = t.prompt;
    document.getElementById('userPrompt').dataset.category = t.category;
    updateFormOptions(t.category);
    updateTitle(t.title);
}

function updateFormOptions(category) {
    const toneSelect = document.getElementById('toneSelect');
    const audienceSelect = document.getElementById('audienceSelect');
    
    const settings = CATEGORY_SETTINGS[category] || CATEGORY_SETTINGS['General'];
    
    const populate = (element, options) => {
        element.innerHTML = options.map(opt => `<option value="${opt}">${opt}</option>`).join('');
    };

    populate(toneSelect, settings.tones);
    populate(audienceSelect, settings.audiences);
}

// --- AI Generation ---
async function generateContent() {
    const btn = document.getElementById('genBtn');
    const editor = document.getElementById('outputEditor');
    const prompt = document.getElementById('userPrompt').value;
    
    if(!prompt) return showToast("Please enter a prompt first!", "error");

    const originalBtnText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Writing...';
    btn.disabled = true;
    editor.style.opacity = "0.5";
    
    if(window.innerWidth <= 768) {
        toggleConfigPanel(); 
    }

    const payload = {
        category: document.getElementById('userPrompt').dataset.category || 'General',
        tone: document.getElementById('toneSelect').value,
        audience: document.getElementById('audienceSelect').value,
        prompt: prompt
    };

    try {
        const res = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        if (res.ok) {
            editor.style.opacity = "1";
            editor.value = ""; 
            await typeWriterEffect(data.text, editor);
            currentDraftId = null; // New content means new ID needed
        } else {
            editor.value = "Error: " + data.text;
            showToast("Generation failed", "error");
        }
    } catch (e) {
        editor.value = "Connection Error. Please check your internet or backend.";
    } finally {
        btn.innerHTML = originalBtnText;
        btn.disabled = false;
        editor.style.opacity = "1";
    }
}

function typeWriterEffect(text, element) {
    return new Promise(resolve => {
        element.value = "";
        let i = 0;
        function type() {
            if (i < text.length) {
                // Type faster for long texts
                const chunkSize = Math.floor(Math.random() * 5) + 5; 
                const chunk = text.substring(i, i + chunkSize);
                element.value += chunk;
                element.scrollTop = element.scrollHeight; 
                i += chunkSize;
                setTimeout(type, 10);
            } else {
                resolve();
            }
        }
        type();
    });
}

// --- Rewriting & Tools ---
async function rewriteContent(mode) {
    const editor = document.getElementById('outputEditor');
    const text = editor.value;
    if (!text || text.length < 10) return showToast("Draft is too short to edit.", "error");

    const originalVal = editor.value;
    editor.style.opacity = "0.6";
    showToast(`Applying ${mode}...`, 'info');
    
    try {
        const res = await fetch('/api/rewrite', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, mode })
        });
        const data = await res.json();
        if(res.ok) {
            editor.value = "";
            await typeWriterEffect(data.text, editor);
        } else {
            showToast("Rewrite failed", "error");
            editor.value = originalVal;
        }
    } catch(e) {
        editor.value = originalVal;
        showToast("Error rewriting.", "error");
    } finally {
        editor.style.opacity = "1";
    }
}

async function continueWriting() {
    const editor = document.getElementById('outputEditor');
    const text = editor.value;
    
    if(!text) return showToast("Start writing something first!", "error");
    
    showToast("Thinking...", "info");
    
    try {
        const res = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: "Continue writing naturally.",
                context: text,
                tone: document.getElementById('toneSelect').value
            })
        });
        const data = await res.json();
        if(res.ok) {
            const newText = "\n" + data.text;
            let i = 0;
            function appendType() {
                if (i < newText.length) {
                    editor.value += newText.charAt(i);
                    editor.scrollTop = editor.scrollHeight;
                    i++;
                    setTimeout(appendType, 10);
                }
            }
            appendType();
        }
    } catch (e) {
        showToast("Failed to continue", "error");
    }
}

// --- Persistence ---
async function saveDraft() {
    const title = document.getElementById('docTitle').value || 'Untitled Document';
    const content = document.getElementById('outputEditor').value;
    const categorySelect = document.getElementById('categorySelect');
    const category = categorySelect ? categorySelect.value : 'General';

    if(!content) return showToast("Cannot save empty document.", "error");

    try {
        const res = await fetch('/api/drafts/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                id: currentDraftId, 
                title, 
                category: category, 
                content 
            })
        });
        
        const data = await res.json();
        if(res.ok) {
            currentDraftId = data.id;
            updateTitle(title);
            showToast("Draft Saved Successfully!", "success");
        } else {
            showToast("Save failed: " + (data.error || "Unknown"), "error");
        }
    } catch (e) {
        showToast("Network error saving draft", "error");
    }
}

async function loadHistory() {
    const list = document.getElementById('draftsList');
    list.innerHTML = '<div style="grid-column: 1/-1; text-align:center; color:var(--text-muted);">Loading drafts...</div>';
    
    try {
        const res = await fetch('/api/drafts');
        const drafts = await res.json();
        
        list.innerHTML = '';
        if(drafts.length === 0) {
            list.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding: 2rem; border: 2px dashed var(--border); border-radius: 8px;">No drafts found.</div>';
            return;
        }
        
        drafts.forEach((d, index) => {
            const item = document.createElement('div');
            item.className = 'draft-card'; 
            item.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:start;">
                    <div style="width: 40px; height: 40px; background: rgba(79, 70, 229, 0.1); color: var(--primary); border-radius: 8px; display: flex; align-items: center; justify-content: center;"><i class="fas fa-file-alt"></i></div>
                    <span style="font-size: 0.75rem; color: var(--text-muted);">${new Date(d.created_at).toLocaleDateString()}</span>
                </div>
                <div style="margin-top: 0.5rem;">
                    <div style="font-weight: 700; color: var(--text-main); margin-bottom: 0.25rem;">${d.title}</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">${d.category || 'General'}</div>
                </div>
            `;
            item.onclick = async () => {
                const res = await fetch(`/api/drafts/${d.id}`);
                const data = await res.json();
                currentDraftId = data.id;
                document.getElementById('docTitle').value = data.title;
                document.getElementById('outputEditor').value = data.content;
                
                // Select proper category in dropdowns if possible
                if(data.category) {
                     const catSelect = document.getElementById('categorySelect');
                     catSelect.value = data.category;
                     handleCategoryChange(data.category);
                }

                switchTab('generator', null);
                updateTitle(data.title);
                
                // Force highlight editor tab
                document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
                const editorBtn = document.querySelector('.nav-item[onclick*="generator"]');
                if (editorBtn) editorBtn.classList.add('active');
            };
            list.appendChild(item);
        });
    } catch(e) {
        list.innerHTML = 'Error loading history.';
    }
}

function exportDoc(type) {
    if(!currentDraftId) return showToast("Please save the draft first before exporting.", "error");
    window.open(`/api/export/${type}/${currentDraftId}`, '_blank');
}

function showToast(msg, type = 'info') {
    const t = document.getElementById('toast');
    t.innerHTML = msg;
    t.style.opacity = '1';
    t.style.bottom = '30px';
    t.style.transform = 'translateY(0)';
    
    if(type === 'error') t.style.background = 'rgba(239, 68, 68, 0.9)'; 
    else if(type === 'success') t.style.background = 'rgba(16, 185, 129, 0.9)'; 
    else t.style.background = 'rgba(15, 23, 42, 0.9)';

    setTimeout(() => { 
        t.style.opacity = '0';
        t.style.bottom = '-50px';
        t.style.transform = 'translateY(20px)';
    }, 3000);
}