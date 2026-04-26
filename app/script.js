document.getElementById('jsonFileInput').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (!file) return;

    document.getElementById('fileNameDisplay').textContent = `File: ${file.name}`;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const data = JSON.parse(e.target.result);
            renderFindings(data);
            updateStats(data);
        } catch (error) {
            alert('Error parsing JSON file. Please ensure it is a valid Gemini scan log.');
        }
    };
    reader.readAsText(file);
});

function updateStats(data) {
    const findings = data.findings || [];
    const high = findings.filter(f => f.severity?.toLowerCase() === 'high').length;
    const medium = findings.filter(f => f.severity?.toLowerCase() === 'medium').length;
    
    document.getElementById('stat-total').textContent = findings.length;
    document.getElementById('stat-high').textContent = high;
    document.getElementById('stat-medium').textContent = medium;
}

function renderFindings(data) {
    const container = document.getElementById('findingsContainer');
    container.innerHTML = '';

    const findings = data.findings || [];

    if (findings.length === 0) {
        container.innerHTML = '<div style="text-align: center; padding: 2rem;">No vulnerabilities detected. System Secure.</div>';
        return;
    }

    findings.forEach((finding, index) => {
        const card = document.createElement('div');
        card.className = 'finding-card';
        
        const severityClass = `severity-${finding.severity?.toLowerCase() || 'low'}`;
        
        // Split findings string into description and code parts if possible
        // Expected format: "Description... Vulnerable Code: ... Suggested Fix: ..."
        let description = finding.findings || "No details provided.";
        let vulnerableCode = "Check original source file.";
        let suggestedFix = "Refer to best practices.";

        if (description.includes("Vulnerable Code:")) {
            const parts = description.split("Vulnerable Code:");
            description = parts[0];
            const codeParts = parts[1].split("Suggested Fix:");
            vulnerableCode = codeParts[0].trim();
            suggestedFix = codeParts[1] ? codeParts[1].trim() : "Review required.";
        }

        card.innerHTML = `
            <div class="finding-header">
                <div class="finding-title-group">
                    <div class="finding-file">${finding.file || 'Global Configuration'}</div>
                    <div class="finding-title">${finding.title || 'Security Misconfiguration'}</div>
                </div>
                <span class="severity-pill ${severityClass}">${finding.severity || 'UNKNOWN'}</span>
            </div>
            <div class="finding-body">
                <div class="finding-description">${description}</div>
                <div class="code-comparison">
                    <div class="code-pane">
                        <div class="pane-label">Detected Risk</div>
                        <pre class="vulnerable-text">${escapeHtml(vulnerableCode)}</pre>
                    </div>
                    <div class="code-pane">
                        <div class="pane-label" style="color: var(--security-low)">Gemini Suggestion</div>
                        <pre class="safe-text">${escapeHtml(suggestedFix)}</pre>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
