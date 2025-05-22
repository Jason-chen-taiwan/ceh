// Quiz JavaScript functionality
document.addEventListener("DOMContentLoaded", function () {
  const usernameDisplay = document.getElementById("username-display");
  const logoutBtn = document.getElementById("logout-btn");
  const loginLink = document.getElementById("login-link");
  const dashboardLink = document.getElementById("dashboard-link");
  const welcomeMessage = document.querySelector(".welcome-message");
  const quizBox = document.querySelector(".quiz-box");

  // 從服務器檢查登入狀態，而不是依賴localStorage
  fetch("/api/user/check-session", {
    method: "GET",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => {
      if (response.ok) {
        return response.json();
      }
      throw new Error("未登入或會話已過期");
    })
    .then((data) => {
      // 用戶已登入
      usernameDisplay.textContent = `歡迎, ${data.username}!`;
      logoutBtn.style.display = "inline-block";
      loginLink.style.display = "none";
      dashboardLink.style.display = "inline-block";

      // 將用戶信息存儲到 localStorage 以便其他頁面使用
      localStorage.setItem(
        "user",
        JSON.stringify({
          id: data.user_id,
          username: data.username,
        })
      );

      // 顯示測驗界面，隱藏歡迎信息
      if (welcomeMessage) welcomeMessage.style.display = "none";
      if (quizBox) quizBox.style.display = "block";
    })
    .catch((error) => {
      console.log("用戶未登入:", error);
      // 用戶未登入
      usernameDisplay.textContent = "訪客";
      logoutBtn.style.display = "none";
      loginLink.style.display = "inline-block";
      dashboardLink.style.display = "none"; // 隱藏測驗界面，顯示歡迎信息
      if (welcomeMessage) welcomeMessage.style.display = "block";
      if (quizBox) quizBox.style.display = "none";
    });

  // 登出功能
  logoutBtn.addEventListener("click", function () {
    fetch("/api/logout", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include", // 包含認證信息
    })
      .then((response) => response.json())
      .then((data) => {
        // 清除本地儲存的用戶資料
        localStorage.removeItem("user");
        window.location.href = data.redirect || "/"; // 使用後端返回的重定向地址或默認跳轉到首頁
      })
      .catch((error) => {
        console.error("登出失敗:", error);
        // 即使出錯也清除本地儲存並跳轉到首頁
        localStorage.removeItem("user");
        window.location.href = "/"; // 即使出錯也跳轉到首頁
      });
  });
});
