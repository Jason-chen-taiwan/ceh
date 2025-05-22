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
  }

  // 重置問題狀態
  function resetQuestionState() {
    // 重置選項狀態
    document.querySelectorAll('input[name="answer"]').forEach((radio) => {
      radio.checked = false;
      radio.disabled = false; // 重新啟用 radio buttons
    });

    // 重置選項的視覺樣式
    document.querySelectorAll(".option").forEach((option) => {
      option.style.cursor = "pointer"; // 恢復滑鼠指標
      option.style.opacity = "1"; // 恢復完整不透明度
    });

    // 重置按鈕狀態
    elements.submitBtn.disabled = true;
    elements.submitBtn.style.display = "block"; // 確保提交按鈕顯示
    elements.nextBtn.style.display = "none"; // 隱藏下一題按鈕
    elements.nextBtn.classList.add("hidden");
    elements.feedbackDiv.classList.add("hidden");

    selectedAnswer = null;
  }

  // 載入問題
  async function loadQuestion(questionNumber) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/questions/${questionNumber}`,
        {
          method: "GET",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch question");
      }

      const data = await response.json();
      displayQuestion(data);
      resetQuestionState();
    } catch (error) {
      console.error("Error:", error);
      elements.questionText.textContent = "載入問題時發生錯誤";
    }
  }

  // 檢查答案
  async function checkAnswer() {
    if (!selectedAnswer) return;

    try {
      const response = await fetch(`${API_BASE_URL}/answers`, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          questionNumber: currentQuestion,
          answer: selectedAnswer,
        }),
      });

      const data = await response.json();
      showFeedback(data);
    } catch (error) {
      console.error("Error:", error);
      elements.feedbackDiv.textContent = "檢查答案時發生錯誤";
      elements.feedbackDiv.classList.remove("hidden");
    }
  }

  // 顯示答案反饋
  function showFeedback(result) {
    elements.feedbackDiv.classList.remove("hidden", "correct", "incorrect");

    if (result.correct) {
      elements.feedbackDiv.classList.add("correct");
      elements.feedbackDiv.textContent = "答對了！";
      if (!isReviewMode) correctCount++; // 只在非複習模式下計分
    } else {
      elements.feedbackDiv.classList.add("incorrect");
      elements.feedbackDiv.textContent = `答錯了！正確答案是: ${result.correct_answer}`;
      if (!isReviewMode) {
        // 只在非複習模式下記錄錯誤
        incorrectCount++;
        wrongAnswers.push({
          questionNumber: currentQuestion,
          questionText: elements.questionText.textContent,
          userAnswer: selectedAnswer,
          correctAnswer: result.correct_answer,
        });
        currentBatchWrongAnswers.push({
          questionNumber: currentQuestion,
          questionText: elements.questionText.textContent,
          userAnswer: selectedAnswer,
          correctAnswer: result.correct_answer,
        });
      }
    }

    // 禁用所有選項
    document.querySelectorAll('input[name="answer"]').forEach((radio) => {
      radio.disabled = true;
    });

    // 禁用標籤的點擊事件
    document.querySelectorAll(".option").forEach((option) => {
      option.style.cursor = "not-allowed";
      option.style.opacity = "0.7";
    });

    // 更新按鈕狀態
    elements.submitBtn.style.display = "none"; // 隱藏提交按鈕
    elements.nextBtn.style.display = "block"; // 顯示下一題按鈕
    elements.nextBtn.classList.remove("hidden");

    updateScore();
  }

  // 向伺服器提交答案
  function submitAnswer(answer) {
    const API_URL = `${API_BASE_URL}/answers`;

    fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include", // 確保發送會話Cookie
      body: JSON.stringify({
        questionNumber: currentQuestion,
        answer: answer,
      }),
    })
      .then((response) => response.json())
      .then((result) => {
        // 顯示反饋
        elements.feedbackDiv.classList.remove("hidden");
        if (result.correct) {
          elements.feedbackDiv.innerHTML = `<span class="correct">正確!</span>`;
          elements.feedbackDiv.className = "feedback correct";
          correctCount++;
        } else {
          elements.feedbackDiv.innerHTML = `<span class="wrong">錯誤!</span> 正確答案是: ${result.correct_answer}`;
          elements.feedbackDiv.className = "feedback wrong";
          incorrectCount++;

          // 儲存錯題記錄
          if (!isReviewMode) {
            wrongAnswers.push({
              questionNumber: currentQuestion,
              questionText: elements.questionText.textContent,
              userAnswer: selectedAnswer,
              correctAnswer: result.correct_answer,
            });
          }
          // 添加到當前批次的錯題
          currentBatchWrongAnswers.push({
            questionNumber: currentQuestion,
            questionText: elements.questionText.textContent,
            userAnswer: selectedAnswer,
            correctAnswer: result.correct_answer,
          });
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        elements.feedbackDiv.innerHTML = `<span class="wrong">提交答案時發生錯誤，請稍後再試。</span>`;
        elements.feedbackDiv.className = "feedback wrong";
      });
  }

  // 綁定事件監聽器
  document.querySelectorAll('input[name="answer"]').forEach((radio) => {
    radio.addEventListener("change", () => {
      selectedAnswer = radio.value;
      elements.submitBtn.disabled = false;
    });
  });

  // 將原本的下一題處理函數抽離出來
  function handleNormalNext() {
    currentIndex++;
    if (
      currentIndex % BATCH_SIZE === 0 &&
      currentBatchWrongAnswers.length > 0
    ) {
      showBatchReview();
    } else if (currentIndex < allQuestionNumbers.length) {
      loadQuestion(allQuestionNumbers[currentIndex]);
    } else {
      showQuizComplete();
    }
  }

  elements.submitBtn.addEventListener("click", checkAnswer);
  elements.nextBtn.addEventListener("click", handleNormalNext);

  // 獲取所有題目編號並打亂順序
  async function initializeQuestions() {
    try {
      const response = await fetch(`${API_BASE_URL}/questions/all`);
      if (!response.ok) throw new Error("Failed to fetch questions");

      const questions = await response.json();
      allQuestionNumbers = questions.map((q) => q.question_number);
      // 使用 Fisher-Yates 演算法打亂題目順序
      for (let i = allQuestionNumbers.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [allQuestionNumbers[i], allQuestionNumbers[j]] = [
          allQuestionNumbers[j],
          allQuestionNumbers[i],
        ];
      }

      currentIndex = 0;
      // 載入第一題
      loadQuestion(allQuestionNumbers[currentIndex]);
    } catch (error) {
      console.error("Error initializing questions:", error);
      elements.questionText.textContent = "初始化題目時發生錯誤";
    }
  }

  // 修改完成測驗的處理
  function showQuizComplete() {
    elements.questionText.textContent = "測驗完成！";

    // 隱藏選項和按鈕
    document.querySelector(".options").style.display = "none";
    elements.submitBtn.style.display = "none";
    elements.nextBtn.style.display = "none";

    const totalQuestions = allQuestionNumbers.length;
    const accuracy = Math.round((correctCount / totalQuestions) * 100);

    // 生成錯誤題目列表的 HTML
    let wrongAnswersHtml = "";
    if (wrongAnswers.length > 0) {
      wrongAnswersHtml = `
        <div class="wrong-answers-list">
          <h3>錯誤題目列表：</h3>
          <ul>
            ${wrongAnswers
              .map(
                (wrong) => `
              <li>
                <strong>題號 ${wrong.questionNumber}</strong><br>
                問題：${wrong.questionText}<br>
                你的答案：${wrong.userAnswer}<br>
                正確答案：${wrong.correctAnswer}
              </li>
            `
              )
              .join("")}
          </ul>
        </div>
      `;
    }

    elements.feedbackDiv.classList.remove("hidden", "correct", "incorrect");
    elements.feedbackDiv.classList.add("complete");
    elements.feedbackDiv.innerHTML = `
      <div class="quiz-summary">
        <h3>測驗結果：</h3>
        <p>總題數: ${totalQuestions}</p>
        <p>正確: ${correctCount}</p>
        <p>錯誤: ${incorrectCount}</p>
        <p>正確率: ${accuracy}%</p>
      </div>
      ${wrongAnswersHtml}
    `;
  }

  // 修改 showBatchReview 函數，添加選項顯示
  async function showBatchReview() {
    elements.questionText.textContent = "複習時間！";
    document.querySelector(".options").style.display = "none";
    elements.submitBtn.style.display = "none";
    elements.nextBtn.style.display = "none";

    elements.feedbackDiv.classList.remove("hidden", "correct", "incorrect");
    elements.feedbackDiv.classList.add("complete");

    // 取得所有錯誤題目的詳細資訊
    const wrongQuestionsDetails = await Promise.all(
      currentBatchWrongAnswers.map(async (wrong) => {
        const response = await fetch(
          `${API_BASE_URL}/questions/${wrong.questionNumber}`
        );
        const questionData = await response.json();
        return {
          ...wrong,
          choices: questionData.choices,
        };
      })
    );

    const reviewHtml = `
      <div class="quiz-summary">
        <h3>本批次複習（${BATCH_SIZE}題中的錯誤題目）：</h3>
        <p>錯誤題數: ${currentBatchWrongAnswers.length}</p>
      </div>
      <div class="wrong-answers-list">
        <ul>
          ${wrongQuestionsDetails
            .map(
              (wrong) => `
            <li>
              <strong>題號 ${wrong.questionNumber}</strong><br>
              問題：${wrong.questionText}<br>
              <div class="choices-list">
                ${wrong.choices
                  .map(
                    (choice) => `
                  <div class="review-choice ${
                    choice.choice_letter === wrong.correctAnswer
                      ? "correct"
                      : ""
                  } ${
                      choice.choice_letter === wrong.userAnswer ? "wrong" : ""
                    }">
                    ${choice.choice_letter}. ${choice.choice_text}
                  </div>
                `
                  )
                  .join("")}
              </div>
              <div class="answer-info">
                你的答案：${wrong.userAnswer}<br>
                正確答案：${wrong.correctAnswer}
              </div>
            </li>
          `
            )
            .join("")}
        </ul>
      </div>
      <button id="retry-btn" class="btn" style="background-color: #e74c3c; margin-top: 20px;">重新作答這些題目</button>
    `;

    elements.feedbackDiv.innerHTML = reviewHtml;

    document.getElementById("retry-btn").addEventListener("click", () => {
      const retryQuestions = currentBatchWrongAnswers.map(
        (q) => q.questionNumber
      );
      startRetryQuestions(retryQuestions);
    });
  }

  // 修改 startRetryQuestions 函數，將事件處理器定義為可重用的函數
  function startRetryQuestions(retryQuestions) {
    // 設置複習模式
    isReviewMode = true;

    // 暫存當前進度和題目
    const originalQuestions = allQuestionNumbers.slice(currentIndex);

    // 設置重試題目
    allQuestionNumbers = retryQuestions;
    currentIndex = 0;

    // 清空當前批次錯誤題目
    currentBatchWrongAnswers = [];

    // 清除舊的事件處理
    const oldSubmitBtn = elements.submitBtn;
    const oldNextBtn = elements.nextBtn;

    const newSubmitBtn = oldSubmitBtn.cloneNode(true);
    const newNextBtn = oldNextBtn.cloneNode(true);

    oldSubmitBtn.parentNode.replaceChild(newSubmitBtn, oldSubmitBtn);
    oldNextBtn.parentNode.replaceChild(newNextBtn, oldNextBtn);

    elements.submitBtn = newSubmitBtn;
    elements.nextBtn = newNextBtn;

    // 重新綁定事件
    elements.submitBtn.onclick = checkAnswer;
    elements.nextBtn.onclick = () => {
      currentIndex++;
      if (currentIndex < allQuestionNumbers.length) {
        // 重置介面狀態
        document.querySelector(".options").style.display = "flex";
        elements.submitBtn.style.display = "block";
        elements.nextBtn.style.display = "none";
        elements.feedbackDiv.classList.add("hidden");

        loadQuestion(allQuestionNumbers[currentIndex]);
      } else {
        isReviewMode = false;
        allQuestionNumbers = originalQuestions;
        currentIndex = 0;

        if (allQuestionNumbers.length > 0) {
          loadQuestion(allQuestionNumbers[currentIndex]);
          elements.submitBtn.onclick = checkAnswer;
          elements.nextBtn.onclick = handleNormalNext;
        } else {
          showQuizComplete();
        }
      }
    };

    // 重置介面
    document.querySelector(".options").style.display = "flex";
    elements.submitBtn.style.display = "block";
    elements.nextBtn.style.display = "none";
    elements.feedbackDiv.classList.add("hidden");

    // 載入第一題重試題目
    loadQuestion(allQuestionNumbers[0]);
  }

  // 初始化
  updateScore();
  initializeQuestions();
});
