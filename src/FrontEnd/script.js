function alertLogger(dataObj, title = "DEBUG LOG") {
    const formattedData = Object.entries(dataObj)
        .map(([key, value]) => `• ${key.toUpperCase()}: ${value}`)
        .join('\n');

    const message = `--- ${title} ---\n\n${formattedData}\n\n-----------------`;
    
    alert(message);
}

function generateData() {
    const data = {
        name: document.getElementById('userName').value,
        age: document.getElementById('userAge').value,
        target: document.getElementById('targetAudience').value,
        description: document.getElementById('businessDesc').value,
        source: document.getElementById('infoSource').value
    };

    alertLogger(data);
}

document.addEventListener('DOMContentLoaded', function() {
    const link = document.getElementById('target_link');

    if(!link) return;

    link.addEventListener('click', function(event) {
        event.preventDefault();

        const name = document.getElementById('u_name').value;
        const login = document.getElementById('u_login').value;
        const pass = document.getElementById('u_pass').value;
        const conf = document.getElementById('u_conf').value;

        alert("Введена інформація:\n" + 
              "Username: " + name + "\n" + 
              "Login: " + login + "\n" + 
              "Password: " + pass + "\n" + 
              "Confirm: " + conf);

        window.location.href = link.href;
    });
});

function initAgeSlider() {
    const userAgeSlider = document.getElementById('userAge');
    const userAgeOutput = document.getElementById('ageValue');

    if (userAgeSlider && userAgeOutput) {
            function updateAgeDisplay() {
                userAgeOutput.innerHTML = userAgeSlider.value;
            }

            userAgeSlider.oninput = updateAgeDisplay;
            
            updateAgeDisplay();
        }
}

function initPlatformsManager() {
    const addBtn = document.getElementById('addPlatformBtn');
    const container = document.getElementById('platformsContainer');
    const continueBtn = document.querySelector('.generate-btn');

    if (!addBtn || !container) return;

    function createPlatformRow() {
        const row = document.createElement('div');
        row.className = 'platform-row';
        row.innerHTML = `
            <div class="input-wrapper name-box">
                <label class="green-label">Platform name</label>
                <input type="text" class="input-transparent platform-name" placeholder="Enter name...">
            </div>
            <div class="input-wrapper link-box">
                <label class="green-label">Link to the platform</label>
                <input type="url" class="input-transparent platform-link" placeholder="https://...">
            </div>
        `;
        return row;
    }

    addBtn.addEventListener('click', () => {
        const currentRows = container.querySelectorAll('.platform-row').length;
        if (currentRows < 5) {
            const newRow = createPlatformRow();
            container.appendChild(newRow);
            newRow.style.opacity = '0';
            newRow.style.transition = 'opacity 0.3s ease';
            setTimeout(() => newRow.style.opacity = '1', 10);

            if (container.querySelectorAll('.platform-row').length === 5) {
                addBtn.style.display = 'none';
            }
        }
    });

    if (continueBtn) {
        continueBtn.addEventListener('click', () => {
            const rows = container.querySelectorAll('.platform-row');
            let summary = "Введені дані:\n";

            rows.forEach((row, index) => {
                const nameInp = row.querySelector('.platform-name');
                const linkInp = row.querySelector('.platform-link');
                
                const name = nameInp ? nameInp.value.trim() || "—" : "—";
                const link = linkInp ? linkInp.value.trim() || "—" : "—";
                
                summary += `\n${index + 1}. ${name}: ${link}`;
            });

            alert(rows.length > 0 ? summary : "Список порожній");
        });
    }
}
document.addEventListener('DOMContentLoaded', () => {

    initAgeSlider();

    initPlatformsManager();
});