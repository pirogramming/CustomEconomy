// static/level_test/test.js
const progressEl = document.getElementById("progress");
const qtypeEl = document.getElementById("qtype");
const questionEl = document.getElementById("question");
const optionsEl = document.getElementById("options");
const feedbackEl = document.getElementById("feedback");
const nextBtn = document.getElementById("nextBtn");
const restartBtn = document.getElementById("restartBtn");

let currentQid = null;
let pickedIndex = null;

function setLoading(isLoading) {
  nextBtn.disabled = isLoading || pickedIndex === null;
}

function renderQuestion(data) {
  currentQid = data.qid;
  pickedIndex = null;
  nextBtn.disabled = true;
  feedbackEl.textContent = "";

  // progress
  if (data.progress?.phase === "self") {
    progressEl.textContent = `설문 ${data.progress.self.current} / ${data.progress.self.total}`;
    qtypeEl.textContent = "SELF (설문)";
  } else {
    progressEl.textContent = `지식 ${data.progress.knowledge.current} / ${data.progress.knowledge.total}`;
    qtypeEl.textContent = `KNOWLEDGE (난이도 ${data.difficulty})`;
  }

  questionEl.textContent = data.question;

  optionsEl.innerHTML = "";
  data.options.forEach((t, idx) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = t;
    btn.style.padding = "10px";
    btn.style.border = "1px solid #ccc";
    btn.style.borderRadius = "10px";
    btn.style.textAlign = "left";
    btn.addEventListener("click", () => {
      pickedIndex = idx;
      // 선택 표시(아주 단순)
      [...optionsEl.children].forEach(x => x.style.borderColor = "#ccc");
      btn.style.borderColor = "#14213E";
      nextBtn.disabled = false;
    });
    optionsEl.appendChild(btn);
  });
}

async function startTest() {
  await fetch("/api/accounts/level_test/start/", {
    method: "POST",
    headers: { "X-CSRFToken": window.__CSRF__ },
  });
  await loadNext();
}

async function loadNext() {
  const res = await fetch("/api/accounts/level_test/next/");
  const data = await res.json();

  if (data.done) {
    // 결과 페이지로 이동
    window.location.href = "/api/accounts/level_test/result/";
    return;
  }
  renderQuestion(data);
}

async function submitAnswer() {
  if (currentQid == null || pickedIndex == null) return;

  setLoading(true);

  const form = new FormData();
  form.append("qid", currentQid);
  form.append("picked", String(pickedIndex));

  const res = await fetch("/api/accounts/level_test/submit/", {
    method: "POST",
    headers: { "X-CSRFToken": window.__CSRF__ },
    body: form,
  });

  const data = await res.json();

  if (data.done) {
    window.location.href = "/api/accounts/level_test/result/";
    return;
  }

  // knowledge만 피드백(원하면 self에도 표시 가능)
  if (data.was_correct === true) feedbackEl.textContent = "✅ 정답!";
  else if (data.was_correct === false) feedbackEl.textContent = "❌ 오답!";
  else feedbackEl.textContent = "저장 완료!";

  // 바로 다음 문제로 넘어가도록(UX 빠르게)
  await loadNext();
  setLoading(false);
}

nextBtn.addEventListener("click", submitAnswer);
restartBtn.addEventListener("click", startTest);

startTest();
