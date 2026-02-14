document.addEventListener("DOMContentLoaded", () => {
    const pwField = document.getElementById("password");
    const toggleBtn = document.querySelector(".pw_show_btn");
    const eyeIcon = document.getElementById("pw-eye-icon");

    const eyeOn = toggleBtn.dataset.eyeOn;
    const eyeOff = toggleBtn.dataset.eyeOff;

    toggleBtn.addEventListener("click", () => {
        if (pwField.type === "password") {
            pwField.type = "text";
            eyeIcon.src = eyeOn;
        } else {
            pwField.type = "password";
            eyeIcon.src = eyeOff;
        }
    });
});
