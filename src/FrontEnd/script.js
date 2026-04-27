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

    link.addEventListener('click', function(event) {
        // Зупиняємо перехід, щоб встигнути показати alert
        event.preventDefault();

        // Беремо дані з твоїх інпутів за ID
        const name = document.getElementById('u_name').value;
        const login = document.getElementById('u_login').value;
        const pass = document.getElementById('u_pass').value;
        const conf = document.getElementById('u_conf').value;

        // Виводимо все в alert
        alert("Введена інформація:\n" + 
              "Username: " + name + "\n" + 
              "Login: " + login + "\n" + 
              "Password: " + pass + "\n" + 
              "Confirm: " + conf);

        // Після натискання "ОК" переходимо за твоїм посиланням
        window.location.href = link.href;
    });
});