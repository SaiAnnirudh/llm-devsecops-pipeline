document.addEventListener('DOMContentLoaded', () => {
    fetchResults();
    setupFileUpload();
});

function setupFileUpload() {
    const fileInput = document.getElementById('jsonUpload');
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const data = JSON.parse(event.target.result);
                renderDashboard(data);
                document.getElementById('overall-status').innerHTML = `<div class="blob success"></div> Custom Upload Active`;
            } catch (err) {
                alert("Invalid JSON file uploaded.");
            }
        };
        reader.readAsText(file);
    });
}

async function fetchResults() {
    const grid = document.getElementById('engines-grid');
    const overallBadge = document.getElementById('overall-status');
    const blob = overallBadge.querySelector('.blob');
    
    try {
        // Fetch generated JSON from root directory in container
        const response = await fetch('llm_validation_results.json');
        
        if (!response.ok) {
            throw new Error(`HTTP Error: ${response.status}`);
        }
        
        const data = await response.json();
        renderDashboard(data);
        
        // Update Overall Status
        blob.className = 'blob success';
        overallBadge.innerHTML = `<div class="blob success"></div> Pipeline Active`;
        
    } catch (error) {
        console.error("Could not load validation results:", error);
        
        // Show Fallback UI if not found
        grid.innerHTML = `
            <div class="card" style="grid-column: 1 / -1; text-align: center;">
                <h3 style="color: var(--warning); margin-bottom: 1rem;">No Scan Results Found</h3>
                <p style="color: var(--text-secondary);">The pipeline has not completed yet, or 'llm_validation_results.json' is missing.<br>Run the Security Validation stage to generate findings.</p>
            </div>
        `;
        
        blob.className = 'blob error';
        overallBadge.innerHTML = `<div class="blob error"></div> Pipeline Offline`;
    }
}

function renderDashboard(data) {
    const grid = document.getElementById('engines-grid');
    grid.innerHTML = '';
    
    const engines = Object.keys(data);
    
    if (engines.length === 0) {
        grid.innerHTML = '<p>No engines evaluated.</p>';
        return;
    }
    
    engines.forEach(engine => {
        const result = data[engine];
        let statusObj = parseStatus(result.status);
        let findings = result.findings || "No detailed output provided by the engine.";
        
        const card = document.createElement('div');
        card.className = 'card';
        
        let findingsHTML = '';
        if (Array.isArray(findings)) {
            if (findings.length === 0) {
                findingsHTML = '<div class="findings-box" style="text-align:center;">No vulnerabilities found.</div>';
            } else {
                findings.forEach(issue => {
                    findingsHTML += `
                        <div style="margin-bottom: 1.5rem; padding-bottom: 1.5rem; border-bottom: 1px solid var(--card-border);">
                            <div class="issue-title">${escapeHTML(issue.issue_title || "Security Issue")}</div>
                            <div class="issue-desc">${escapeHTML(issue.description || "")}</div>
                            
                            <div class="diff-container">
                                <div class="diff-header">
                                    <span>${escapeHTML(issue.file_path || "Unknown File")}</span>
                                </div>
                                <div class="diff-body">
                                    <div class="diff-row">
                                        <div class="diff-old">
                                            <div style="color: #ef4444; font-weight:bold; margin-bottom: 0.5rem; border-bottom: 1px solid rgba(239,68,68,0.2);">Original Code</div>
                                            ${escapeHTML(issue.original_code || "")}
                                        </div>
                                        <div class="diff-new">
                                            <div style="color: #10b981; font-weight:bold; margin-bottom: 0.5rem; border-bottom: 1px solid rgba(16,185,129,0.2);">Suggested Fix</div>
                                            ${escapeHTML(issue.suggested_code_replacement || "")}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
            }
        } else {
            // Fallback for unstructured text
            findingsHTML = `<div class="findings-box">${escapeHTML(String(findings))}</div>`;
        }

        card.innerHTML = `
            <div class="card-header">
                <div class="engine-name">
                    ${getEngineIcon(engine)}
                    ${engine}
                </div>
                <div class="engine-status ${statusObj.cssClass}">
                    ${statusObj.text}
                </div>
            </div>
            <div class="card-body">
                ${findingsHTML}
            </div>
        `;
        
        grid.appendChild(card);
    });
}

function parseStatus(statusStr) {
    if (!statusStr) return { text: 'UNKNOWN', cssClass: 'status-skipped' };
    
    const s = statusStr.toLowerCase();
    if (s.includes('success')) {
        return { text: 'SECURE', cssClass: 'status-success' };
    }
    if (s.includes('429') || s.includes('qouta') || s.includes('billing')) {
        return { text: 'RATE LIMITED', cssClass: 'status-rate' };
    }
    if (s.includes('403') || s.includes('404') || s.includes('error')) {
        return { text: 'CONNECTION ERROR', cssClass: 'status-error' };
    }
    if (s.includes('skipped')) {
        return { text: 'SKIPPED', cssClass: 'status-skipped' };
    }
    
    return { text: statusStr.toUpperCase(), cssClass: 'status-skipped' };
}

function getEngineIcon(name) {
    const n = name.toLowerCase();
    if (n.includes('openai')) return '🤖';
    if (n.includes('gemini')) return '✨';
    if (n.includes('groq')) return '⚡';
    return '🔍';
}

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag])
    );
}
