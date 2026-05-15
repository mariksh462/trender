const API_BASE = 'http://127.0.0.1:8000';

// Утилита для логування
function alertLogger(dataObj, title = "DEBUG LOG") {
    const formattedData = Object.entries(dataObj)
        .map(([key, value]) => `• ${key.toUpperCase()}: ${value}`)
        .join('\n');

    const message = `--- ${title} ---\n\n${formattedData}\n\n-----------------`;
    
    alert(message);
}

// Утилита для безпеки
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Зберегти профіль користувача
function generateData() {
    const data = {
        name: document.getElementById('userName').value,
        age: document.getElementById('userAge').value,
        target: document.getElementById('targetAudience').value,
        description: document.getElementById('businessDesc').value,
        source: document.getElementById('infoSource').value
    };

    // Відправити на бекенд
    fetch(`${API_BASE}/api/profile`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
        .then(response => {
            if (response.ok) {
                alertLogger(data, "✓ Профіль збережено");
            } else {
                alertLogger(data, "⚠ Не вдалося зберегти профіль у PostgreSQL");
            }
        })
        .catch(error => {
            console.error('Помилка:', error);
            alertLogger(data, "⚠ Помилка збереження");
        });
}

// Зберегти профіль і перейти далі
function saveProfileAndContinue() {
    const name = document.getElementById('userName').value;
    if (!name) {
        alert("⚠ Будь ласка, введіть ім'я!");
        return;
    }

    const data = {
        name: name,
        age: document.getElementById('userAge').value,
        target: document.getElementById('targetAudience').value,
        description: document.getElementById('businessDesc').value,
        source: document.getElementById('infoSource').value
    };

    // Відправити на бекенд
    fetch(`${API_BASE}/api/profile`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
        .then(response => {
            if (response.ok) {
                alert("✓ Профіль збережено!");
                window.location.href = "dashboard.html";
            } else {
                alert("⚠ Не вдалося зберегти профіль у PostgreSQL. Переходимо далі...");
                window.location.href = "dashboard.html";
            }
        })
        .catch(error => {
            console.error('Помилка:', error);
            alert("⚠ Помилка збереження профілю, але переходимо далі...");
            window.location.href = "dashboard.html";
        });
}

// Реєстрація користувача
document.addEventListener('DOMContentLoaded', function() {
    const link = document.getElementById('target_link');

    if(!link) return;

    link.addEventListener('click', function(event) {
        event.preventDefault();

        const name = document.getElementById('u_name').value;
        const login = document.getElementById('u_login').value;
        const pass = document.getElementById('u_pass').value;
        const conf = document.getElementById('u_conf').value;

        // Валідація
        if (!name || !login || !pass || !conf) {
            alert("⚠ Будь ласка, заповніть усі поля!");
            return;
        }

        if (pass !== conf) {
            alert("⚠ Паролі не збігаються!");
            return;
        }

        // Відправити на бекенд
        fetch(`${API_BASE}/api/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name,
                login: login,
                password: pass
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert("✓ Реєстрація успішна! Переходимо на dashboard...");
                    window.location.href = link.href;
                } else {
                    alert("⚠ Помилка: " + (data.error || "Невідома помилка"));
                }
            })
            .catch(error => {
                console.error('Помилка реєстрації:', error);
                alert("⚠ Помилка з'єднання з сервером");
            });
    });
});

// Ініціалізація повзунка віку
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

// Управління платформами
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
            const platforms = [];

            rows.forEach((row, index) => {
                const nameInp = row.querySelector('.platform-name');
                const linkInp = row.querySelector('.platform-link');
                
                const name = nameInp ? nameInp.value.trim() : "";
                const link = linkInp ? linkInp.value.trim() : "";
                
                if (name && link) {
                    platforms.push({ name: name, link: link });
                }
            });

            if (platforms.length === 0) {
                alert("⚠ Будь ласка, додайте принаймні одну платформу");
                return;
            }

            // Відправити на бекенд
            fetch(`${API_BASE}/api/platforms`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    platforms: platforms
                })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert("✓ Платформи збережено! Переходимо на dashboard...");
                        window.location.href = "dashboard.html";
                    } else {
                        alert("⚠ Помилка: " + (data.error || "Невідома помилка"));
                    }
                })
                .catch(error => {
                    console.error('Помилка:', error);
                    alert("⚠ Помилка з'єднання з сервером");
                });
        });
    }
}
document.addEventListener('DOMContentLoaded', () => {

    initAgeSlider();

    initPlatformsManager();
});