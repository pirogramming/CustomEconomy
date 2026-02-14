// level_test.js

// ✅ 현재 페이지(/.../level_test/) 기준으로 상대경로 호출하면 prefix 문제 안 생김
const API = {
  start: "start/",
  next: "next/",
  submit: "submit/",
  result: "result/",
};

const $qtype = document.getElementById("qtype");
const $question = document.getElementById("question");
const $options = document.getElementById("options");
const $nextBtn = document.getElementById("nextBtn");
const $feedback = document.getElementById("feedback");
let currentStep = 1;

let current = {
  qid: null,
  picked: null,
  payload: null,
};

function csrfHeader() {
  // 너 템플릿에 window.__CSRF__ 만들었으면 그걸 쓰고,
  // 없으면 쿠키에서 꺼내도록 해도 됨.
  const token = window.__CSRF__ || null;
  return token ? { "X-CSRFToken": token } : {};
}

async function apiStart() {
  const res = await fetch(API.start, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      ...csrfHeader(),
    },
    body: "", // 서버는 바디 없어도 OK
    credentials: "same-origin",
  });
  if (!res.ok) throw new Error(`start failed: ${res.status}`);
  return res.json();
}

async function apiNext() {
  const res = await fetch(API.next, {
    method: "GET",
    credentials: "same-origin",
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.error || `next failed: ${res.status}`);
  return data;
}

async function apiSubmit(qid, pickedIndex) {
  const body = new URLSearchParams();
  body.set("qid", qid);
  body.set("picked", String(pickedIndex));

  const res = await fetch(API.submit, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      ...csrfHeader(),
    },
    body,
    credentials: "same-origin",
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data?.error || `submit failed: ${res.status}`);
  return data;
}

function renderQuestion(payload) {
  current.payload = payload;
  current.qid = payload.qid;
  current.picked = null;

  $qtype.textContent =
    payload.type === "self"
      ? "자기진단"
      : `지식문항 (난이도 ${payload.difficulty})`;

  $question.textContent = payload.question;

  $options.innerHTML = "";
  payload.options.forEach((text, idx) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "leveltest_option_btn"; // 원하면 CSS에서 꾸미기
    btn.textContent = text;

    btn.addEventListener("click", () => {
      // 선택 표시
      [...$options.children].forEach((el) => el.classList.remove("is-selected"));
      btn.classList.add("is-selected");

      current.picked = idx;
      $nextBtn.disabled = false;
      $feedback.textContent = ""; // 선택 바꾸면 피드백 초기화
    });

    $options.appendChild(btn);
  });

  $nextBtn.disabled = true;
}

// function showFeedbackAfterSubmit(result) {
//   // self는 was_correct가 null, knowledge는 true/false
//   if (!$feedback) return;
  
//   if (result.was_correct === null) {
//     $feedback.textContent = `선택이 저장됐어요. (+${result.earned})`;
//   } else if (result.was_correct) {
//     $feedback.textContent = `정답! (+${result.earned})`;
//   } else {
//     $feedback.textContent = `오답. (${result.earned})`;
//   }
// }

async function loadNextQuestionOrFinish() {
  const payload = await apiNext();

  if (payload.done) {
    // 결과 페이지로 이동 (서버 렌더 결과 화면)
    window.location.href = API.result;
    return;
  }

  renderQuestion(payload);
}

async function init() {
  try {
    // 1) 세션 초기화
    await apiStart();
    // 2) 첫 문제 로드
    await loadNextQuestionOrFinish();
  } catch (e) {
    console.error(e);
    $feedback.textContent = "시작 중 오류가 발생했어요. 콘솔 로그를 확인해 주세요.";
  }
}

$nextBtn?.addEventListener("click", async () => {
  if (current.qid == null || current.picked == null) return;

  try {
    $nextBtn.disabled = true;
    const result = await apiSubmit(current.qid, current.picked);

    // 질문에 답하기만 했으면 진행상황 업데이트
    currentStep++;
    updateProgress(currentStep);

    if (result.done) {
      window.location.href = API.result;
      return;
    }

    // 즉시 다음 문제 로드
    await loadNextQuestionOrFinish();
  } catch (e) {
    console.error(e);
    if ($feedback) $feedback.textContent = "제출 중 오류가 발생했어요. 콘솔 로그를 확인해 주세요.";
    $nextBtn.disabled = false;
  }
});

//단계별로 체크와 선 색 변하는 함수(Prgress 부분을 변화시킴)
function updateProgress(step) {
  // step = 현재 문제 번호 (1부터 시작)

  if (step <= 1) return;

  const idx = step - 1;

  //체크 색 변하는 부분
  const check = document.getElementById(`check${idx}`);
  if (check) {
    check.src = "/static/icon/progress_checked.svg";


  check.classList.remove("pop"); // 재실행 보장
  void check.offsetWidth;        // reflow 트릭
  check.classList.add("pop");
  }

  // 선 색 변하는 부분
  const line = document.getElementById(`line${idx}-${idx + 1}`);
  if (line) {
    line.classList.add("active");
  }
}



// 페이지 로드 시 시작
document.addEventListener("DOMContentLoaded", init);
