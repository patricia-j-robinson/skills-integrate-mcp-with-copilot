document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const userIcon = document.getElementById("user-icon");
  const loginModal = document.getElementById("login-modal");
  const userInfoModal = document.getElementById("user-info-modal");
  const loginForm = document.getElementById("login-form");
  const closeLoginBtn = document.getElementById("close-login-btn");
  const closeUserInfoBtn = document.getElementById("close-user-info-btn");
  const logoutBtn = document.getElementById("logout-btn");
  const userInfoDisplay = document.getElementById("user-info-display");
  const loginMessage = document.getElementById("login-message");

  // Session state
  let currentSession = null;
  let isLoggedIn = false;

  // Load session from localStorage
  function loadSession() {
    const savedSession = localStorage.getItem("teacher_session");
    if (savedSession) {
      currentSession = JSON.parse(savedSession);
      verifySession();
    }
  }

  // Verify current session is still valid
  async function verifySession() {
    if (!currentSession) return;
    
    try {
      const response = await fetch(`/verify-session?session_id=${currentSession.session_id}`);
      const result = await response.json();
      
      if (result.valid) {
        isLoggedIn = true;
        showUserLoggedIn(currentSession.username);
      } else {
        currentSession = null;
        localStorage.removeItem("teacher_session");
        isLoggedIn = false;
        showUserLoggedOut();
      }
    } catch (error) {
      console.error("Error verifying session:", error);
    }
  }

  // Show logged in state
  function showUserLoggedIn(username) {
    userIcon.textContent = "✅";
    userIcon.style.cursor = "pointer";
  }

  // Show logged out state
  function showUserLoggedOut() {
    userIcon.textContent = "👤";
    userIcon.style.cursor = "pointer";
  }

  // Handle user icon click
  userIcon.addEventListener("click", () => {
    if (isLoggedIn) {
      // Show user info modal
      userInfoDisplay.innerHTML = `<p><strong>Logged in as:</strong> ${currentSession.username}</p>`;
      logoutBtn.classList.remove("hidden");
      userInfoModal.classList.remove("hidden");
    } else {
      // Show login modal
      loginModal.classList.remove("hidden");
    }
  });

  // Close login modal
  closeLoginBtn.addEventListener("click", () => {
    loginModal.classList.add("hidden");
    loginForm.reset();
    loginMessage.classList.add("hidden");
  });

  // Close user info modal
  closeUserInfoBtn.addEventListener("click", () => {
    userInfoModal.classList.add("hidden");
  });

  // Handle login form submission
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
      const response = await fetch(`/login?username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`, {
        method: "POST"
      });

      const result = await response.json();

      if (response.ok) {
        currentSession = {
          session_id: result.session_id,
          username: result.username
        };
        localStorage.setItem("teacher_session", JSON.stringify(currentSession));
        isLoggedIn = true;
        loginMessage.textContent = "Login successful!";
        loginMessage.className = "success";
        loginMessage.classList.remove("hidden");
        
        setTimeout(() => {
          loginModal.classList.add("hidden");
          loginForm.reset();
          loginMessage.classList.add("hidden");
          showUserLoggedIn(username);
          fetchActivities();
        }, 1000);
      } else {
        loginMessage.textContent = result.detail || "Login failed";
        loginMessage.className = "error";
        loginMessage.classList.remove("hidden");
      }
    } catch (error) {
      loginMessage.textContent = "Failed to login. Please try again.";
      loginMessage.className = "error";
      loginMessage.classList.remove("hidden");
      console.error("Error logging in:", error);
    }
  });

  // Handle logout
  logoutBtn.addEventListener("click", async () => {
    try {
      await fetch(`/logout?session_id=${currentSession.session_id}`, {
        method: "POST"
      });
      
      currentSession = null;
      localStorage.removeItem("teacher_session");
      isLoggedIn = false;
      userInfoModal.classList.add("hidden");
      showUserLoggedOut();
      fetchActivities();
    } catch (error) {
      console.error("Error logging out:", error);
    }
  });

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        // Create participants HTML with delete icons only if logged in
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) =>
                      `<li><span class="participant-email">${email}</span>${
                        isLoggedIn
                          ? `<button class="delete-btn" data-activity="${name}" data-email="${email}">❌</button>`
                          : ""
                      }</li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Add event listeners to delete buttons
      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    if (!currentSession) {
      messageDiv.textContent = "You must be logged in as a teacher to remove students.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      return;
    }

    try {
      const response = await fetch(
        `/admin/unregister-student?activity_name=${encodeURIComponent(
          activity
        )}&email=${encodeURIComponent(email)}&session_id=${encodeURIComponent(currentSession.session_id)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to unregister. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  loadSession();
  fetchActivities();
});
