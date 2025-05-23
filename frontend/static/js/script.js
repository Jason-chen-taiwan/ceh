// 全域變數
let currentQuestion = 1;
let selectedAnswer = null;
let correctCount = 0;
let incorrectCount = 0;
let allQuestionNumbers = [];
let currentIndex = 0;
// 添加錯誤題目追蹤
let wrongAnswers = [];
// 添加新的全域變數
let currentBatchWrongAnswers = [];
const BATCH_SIZE = 10;

const API_BASE_URL = "/api";

// 添加新的全域變數
let isReviewMode = false; // 用來標記是否在複習模式

// 基本fetch選項，包含認證
const fetchOptions = {
  credentials: "include",
  headers: {
    "Content-Type": "application/json",
  },
};

// 等待 DOM 完全載入後再執行
document.addEventListener("DOMContentLoaded", function () {
  // 取得 DOM 元素參考
  const elements = {
    questionText: document.getElementById("question-text"),
    currentNumberSpan: document.getElementById("current-number"),
    submitBtn: document.getElementById("submit-btn"),
    nextBtn: document.getElementById("next-btn"),
    feedbackDiv: document.getElementById("answer-feedback"),
    correctCountSpan: document.getElementById("correct-count"),
    incorrectCountSpan: document.getElementById("incorrect-count"),
  };

  // 更新分數顯示
  function updateScore() {
    elements.correctCountSpan.textContent = correctCount;
    elements.incorrectCountSpan.textContent = incorrectCount;
  }

  // 顯示問題
  function displayQuestion(question) {
    currentQuestion = question.question_number; // 添加這行來更新當前問題編號
    elements.currentNumberSpan.textContent = question.question_number;
    elements.questionText.textContent = question.question_text;

    // 確保選項區域是可見的
    document.querySelector(".options").style.display = "flex";

    question.choices.forEach((choice) => {
      const label = document.getElementById(`label-${choice.choice_letter}`);
      if (label) {
        label.textContent = `${choice.choice_letter}. ${choice.choice_text}`;
      }
    });

    // 重置選項選擇
    resetAnswerSelection();
    // 隱藏回饋
    elements.feedbackDiv.classList.add("hidden");
    // 禁用提交按鈕
    elements.submitBtn.disabled = true;
    // 隱藏下一題按鈕
    elements.nextBtn.classList.add("hidden");
    // 顯示提交按鈕
    elements.submitBtn.classList.remove("hidden");
  }
  // 加載問題
  async function loadQuestion(questionNumber) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/questions/${questionNumber}`,
        { ...fetchOptions, method: "GET" }
      );
      if (!response.ok) {
        if (response.status === 403) {
          // 如果問題超出用戶級別或達到每日限制
          const errorData = await response.json();

          // 清空原有内容
          elements.questionText.innerHTML = "";

          // 創建標題
          const errorTitle = document.createElement("h3");
          errorTitle.textContent = "題目訪問限制";
          errorTitle.style.color = "#e74c3c";
          errorTitle.style.marginBottom = "1rem";
          elements.questionText.appendChild(errorTitle);

          // 創建錯誤信息
          const errorMessage = document.createElement("p");
          errorMessage.textContent = errorData.message || "此問題暫時無法訪問";
          errorMessage.style.marginBottom = "1.5rem";
          elements.questionText.appendChild(errorMessage);

          // 添加升級信息
          const upgradeInfo = document.createElement("div");
          upgradeInfo.classList.add("upgrade-info");
          upgradeInfo.innerHTML = `
            <p>⚠️ 免費版用戶功能限制 ⚠️</p>
            <p>您當前正在嘗試訪問的功能或題目超出了免費用戶的限制範圍。</p>
            <p>升級到標準版或專業版即可解鎖全部題庫，並獲得更多進階功能！</p>
            <button class="upgrade-button" id="contact-admin-btn">聯繫管理員升級帳戶</button>
          `;
          elements.questionText.appendChild(upgradeInfo);

          // 為升級按鈕添加事件處理
          setTimeout(() => {
            const contactAdminBtn =
              document.getElementById("contact-admin-btn");
            if (contactAdminBtn) {
              contactAdminBtn.addEventListener("click", () => {
                alert(
                  "請發送郵件至 admin@cehquiz.com 或聯系您的管理員進行帳戶升級"
                );
              });
            }
          }, 100);

          document.querySelector(".options").style.display = "none";
          elements.submitBtn.disabled = true;
          elements.submitBtn.classList.add("hidden");

          // 顯示一個"繼續"按鈕，跳到下一題
          elements.nextBtn.textContent = "返回可用題目";
          elements.nextBtn.style.display = "block";
          elements.nextBtn.classList.remove("hidden");

          return;
        }
        throw new Error("無法加載問題");
      }
      const question = await response.json();
      displayQuestion(question);
    } catch (error) {
      console.error("加載問題失敗:", error);
      showError("無法加載問題，請稍後再試");
    }
  }

  // 提交答案
  async function submitAnswer() {
    if (!selectedAnswer) return;

    try {
      const response = await fetch(`${API_BASE_URL}/answers`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          questionNumber: currentQuestion,
          answer: selectedAnswer,
        }),
      });

      if (!response.ok) {
        throw new Error("無法提交答案");
      }

      const result = await response.json();
      showFeedback(result.correct, selectedAnswer, result.correct_answer);

      if (result.correct) {
        correctCount++;
      } else {
        incorrectCount++;
        // 添加到錯誤列表
        wrongAnswers.push({
          questionNumber: currentQuestion,
          wrongAnswer: selectedAnswer,
          correctAnswer: result.correct_answer,
        });
        // 添加到當前批次錯誤列表
        currentBatchWrongAnswers.push(currentQuestion);
      }

      // 更新分數
      updateScore();
    } catch (error) {
      console.error("提交答案失敗:", error);
      showError("無法提交答案，請稍後再試");
    }
  }

  // 顯示回饋
  function showFeedback(isCorrect, selectedAns, correctAns) {
    const feedbackDiv = elements.feedbackDiv;
    feedbackDiv.classList.remove("hidden");

    if (isCorrect) {
      feedbackDiv.textContent = "✓ 回答正確！";
      feedbackDiv.classList.add("correct");
      feedbackDiv.classList.remove("incorrect");
    } else {
      feedbackDiv.innerHTML = `✗ 回答錯誤！<br>您的答案: ${selectedAns}<br>正確答案: ${correctAns}`;
      feedbackDiv.classList.add("incorrect");
      feedbackDiv.classList.remove("correct");
    }

    // 隱藏提交按鈕
    elements.submitBtn.classList.add("hidden");
    // 顯示下一題按鈕
    elements.nextBtn.classList.remove("hidden");
  }

  // 顯示錯誤訊息
  function showError(message) {
    const errorDiv = document.createElement("div");
    errorDiv.classList.add("error-message");
    errorDiv.textContent = message;
    document.querySelector(".quiz-content").appendChild(errorDiv);
    setTimeout(() => {
      errorDiv.remove();
    }, 3000);
  }

  function getRandomQuestion() {
    // 決定是從正常題庫還是錯題集中獲取問題
    if (
      isReviewMode &&
      currentBatchWrongAnswers.length > 0 &&
      currentIndex < currentBatchWrongAnswers.length
    ) {
      // 從當前批次錯題中獲取
      return loadQuestion(currentBatchWrongAnswers[currentIndex++]);
    } else if (
      !isReviewMode &&
      allQuestionNumbers.length > 0 &&
      currentIndex < allQuestionNumbers.length
    ) {
      // 從預加載的題目中獲取
      return loadQuestion(allQuestionNumbers[currentIndex++]);
    } else {
      // 沒有更多預加載題目或錯題，重新獲取
      fetchRandomQuestion();
    }
  }

  function fetchRandomQuestion() {
    // 如果不是複習模式，隨機獲取一個新問題
    if (!isReviewMode) {
      // 如果沒有預加載題目，或者已經用完，直接從API獲取
      fetch(`${API_BASE_URL}/questions/random`, {
        ...fetchOptions,
        method: "GET",
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("無法獲取問題");
          }
          return response.json();
        })
        .then((question) => {
          displayQuestion(question);
        })
        .catch((error) => {
          console.error("獲取問題失敗:", error);
          showError("無法加載問題，請稍後再試");
        });
    } else {
      // 複習模式但沒有更多錯題，提示用戶
      if (wrongAnswers.length === 0) {
        showError("沒有錯題可複習");
        return;
      }

      // 重置當前批次和索引
      currentBatchWrongAnswers = [];
      let count = 0;
      // 最多取BATCH_SIZE個錯題
      while (count < BATCH_SIZE && count < wrongAnswers.length) {
        currentBatchWrongAnswers.push(wrongAnswers[count].questionNumber);
        count++;
      }
      currentIndex = 0;
      loadQuestion(currentBatchWrongAnswers[currentIndex++]);
    }
  }

  // 重置答案選擇
  function resetAnswerSelection() {
    selectedAnswer = null;
    document.querySelectorAll('input[name="answer"]').forEach((radio) => {
      radio.checked = false;
    });
    elements.submitBtn.disabled = true;
  }

  // 初始化題目列表
  async function initializeQuestionList() {
    try {
      const response = await fetch(`${API_BASE_URL}/questions/all`, {
        ...fetchOptions,
        method: "GET",
      });
      if (!response.ok) {
        throw new Error("無法獲取題目列表");
      }
      const questions = await response.json();
      // 從返回的所有問題中提取問題編號
      allQuestionNumbers = questions.map((q) => q.question_number);
      // 隨機排序題目
      shuffleArray(allQuestionNumbers);
      // 重置索引
      currentIndex = 0;
      // 加載第一個問題
      if (allQuestionNumbers.length > 0) {
        loadQuestion(allQuestionNumbers[currentIndex++]);
      } else {
        showError("沒有可用的題目");
      }
    } catch (error) {
      console.error("初始化題目列表失敗:", error);
      showError("無法獲取題目列表，請稍後再試");
      // 如果獲取所有題目失敗，直接獲取一個隨機題目
      fetchRandomQuestion();
    }
  }

  // 輔助函數：隨機排序數組
  function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]];
    }
  }

  // 添加事件監聽器
  function setupEventListeners() {
    // 監聽選項選擇
    document.querySelectorAll('input[name="answer"]').forEach((radio) => {
      radio.addEventListener("change", function () {
        selectedAnswer = this.value;
        elements.submitBtn.disabled = false;
      });
    });

    // 監聽提交按鈕
    elements.submitBtn.addEventListener("click", submitAnswer);

    // 監聽下一題按鈕
    elements.nextBtn.addEventListener("click", getRandomQuestion);

    // 如果需要，可以在此添加錯題複習模式的切換按鈕監聽器
    const reviewModeBtn = document.getElementById("review-mode-btn");
    if (reviewModeBtn) {
      reviewModeBtn.addEventListener("click", function () {
        isReviewMode = !isReviewMode;
        this.textContent = isReviewMode ? "返回普通模式" : "進入錯題複習";
        // 根據模式重置和載入問題
        if (isReviewMode) {
          if (wrongAnswers.length === 0) {
            showError("沒有錯題可複習");
            isReviewMode = false;
            this.textContent = "進入錯題複習";
            return;
          }
          // 重置當前批次和索引
          currentBatchWrongAnswers = [];
          let count = 0;
          // 最多取BATCH_SIZE個錯題
          while (count < BATCH_SIZE && count < wrongAnswers.length) {
            currentBatchWrongAnswers.push(wrongAnswers[count].questionNumber);
            count++;
          }
          currentIndex = 0;
          loadQuestion(currentBatchWrongAnswers[currentIndex++]);
        } else {
          // 重置索引並重新獲取題目
          currentIndex = 0;
          getRandomQuestion();
        }
      });
    }

    // 添加獲取用戶錯題集的功能
    const loadWrongQuestionsBtn = document.getElementById(
      "load-wrong-questions-btn"
    );
    if (loadWrongQuestionsBtn) {
      loadWrongQuestionsBtn.addEventListener("click", async function () {
        try {
          const response = await fetch(`${API_BASE_URL}/user/wrong-questions`, {
            ...fetchOptions,
            method: "GET",
          });
          if (!response.ok) {
            throw new Error("無法獲取錯題集");
          }
          const wrongQuestions = await response.json();
          // 清空當前錯題記錄
          wrongAnswers = [];
          currentBatchWrongAnswers = [];
          // 將服務器返回的錯題轉換為本地格式並添加到錯題列表
          wrongQuestions.forEach((wq) => {
            wrongAnswers.push({
              questionNumber: wq.question_number,
              wrongAnswer: wq.wrong_answer,
              correctAnswer: wq.correct_answer,
            });
            currentBatchWrongAnswers.push(wq.question_number);
          });
          // 切換到錯題複習模式
          isReviewMode = true;
          if (reviewModeBtn) {
            reviewModeBtn.textContent = "返回普通模式";
          }
          // 重置索引並加載第一個錯題
          currentIndex = 0;
          if (currentBatchWrongAnswers.length > 0) {
            loadQuestion(currentBatchWrongAnswers[currentIndex++]);
          } else {
            showError("沒有錯題可複習");
          }
        } catch (error) {
          console.error("獲取錯題集失敗:", error);
          showError("無法獲取錯題集，請稍後再試");
        }
      });
    }

    // 添加模擬考試功能
    const startExamBtn = document.getElementById("start-exam-btn");
    if (startExamBtn) {
      startExamBtn.addEventListener("click", function () {
        // 實現模擬考試功能...
      });
    }
  }

  // 初始化
  function initialize() {
    setupEventListeners();
    initializeQuestionList();
    updateScore();
  }

  // 啟動
  initialize();
});
