function checkStrength(password) {
  const strengthBar = document.getElementById('strengthLevel');
  const strengthText = document.getElementById('strengthText');
  let strength = 0;

  if (password.length > 5) strength++;
  if (password.length > 8) strength++;
  if (/[A-Z]/.test(password)) strength++;
  if (/[0-9]/.test(password)) strength++;
  if (/[^A-Za-z0-9]/.test(password)) strength++;

  const colors = ["red", "orange", "yellow", "lightgreen", "green"];
  const labels = ["Sehr schwach", "Schwach", "Okay", "Gut", "Stark"];

  strengthBar.style.width = (strength * 20) + "%";
  strengthBar.style.backgroundColor = colors[strength - 1] || "red";
  strengthText.textContent = "Passwortstärke: " + (labels[strength - 1] || "Sehr schwach");
}