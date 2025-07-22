// CODE ACADEMIA Frontend Logic (app.js)

// Placeholder for current user (replace with real auth flow)
const currentUser = {
  email: "student@example.com",
  username: "Your Name"
};

// List of course names (must match backend course names)
const courses = ["HTML", "CSS", "JavaScript", "Python", "General"];

/**
 * 1. Tab Navigation
 */
function showTab(tabId) {
  // hide all tabs
  document.querySelectorAll(".tab").forEach((sec) => {
    sec.classList.remove("active");
  });
  // deactivate all buttons
  document.querySelectorAll(".navbar button").forEach((btn) => {
    btn.classList.remove("active");
  });
  // activate selected
  document.getElementById(tabId).classList.add("active");
  document
    .querySelector(`.navbar button[onclick="showTab('${tabId}')"]`)
    .classList.add("active");
}

// initialize first tab
document.addEventListener("DOMContentLoaded", () => {
  showTab("dashboard");
  loadCourses();
  loadProgress();
  loadNews();
});

/**
 * 2. Load and Render Courses
 */
async function loadCourses() {
  const container = document.getElementById("courseList");
  container.innerHTML = "";

  for (let course of courses) {
    // fetch course details
    let res = await fetch(`/get_course/${course}`);
    let data = await res.json();

    // create card
    let card = document.createElement("div");
    card.className = "course-card";
    card.innerHTML = `
      <h3>${data.course}</h3>
      <p>Price: ₦${data.price}</p>
      <p>Weeks: ${data.weeks.length}</p>
      <button onclick="enterCourse('${data.course}')">Enter</button>
    `;

    container.appendChild(card);
  }
}

/**
 * 3. Enter a Course (load its weeks & lock logic)
 */
async function enterCourse(course) {
  const tab = document.getElementById("courses");
  tab.innerHTML = `<h2>${course} Curriculum</h2><div id="weekList"></div>`;
  showTab("courses");

  // fetch weeks & progress
  let [weeksRes, progRes] = await Promise.all([
    fetch(`/get_course/${course}`),
    fetch(`/progress/${currentUser.email}/${course}`),
  ]);
  let { weeks } = await weeksRes.json();
  let { progress } = await progRes.json();
  const passedWeeks = progress.filter((p) => p.passed_quiz).map((p) => p.week);

  // render weeks
  let wl = document.getElementById("weekList");
  weeks.forEach((w) => {
    let locked = w.week !== 1 && !passedWeeks.includes(w.week - 1);
    let div = document.createElement("div");
    div.className = `course-card ${locked ? "locked" : ""}`;
    div.innerHTML = `
      <h4>Week ${w.week}: ${w.title}</h4>
      <p>${locked ? "Locked 🔒" : "Unlocked ✅"}</p>
      <button ${locked ? "disabled" : ""} onclick="viewLesson('${course}',${w.week})">
        ${locked ? "Locked" : "View Lesson"}
      </button>
    `;
    wl.appendChild(div);
  });
}

/**
 * 4. View a Lesson + Quiz
 */
async function viewLesson(course, week) {
  showTab("editor"); // reuse editor tab for lesson content

  // fetch lesson text
  let courseData = await (await fetch(`/get_course/${course}`)).json();
  let lesson = courseData.weeks.find((w) => w.week === week).lesson;

  // display lesson above editor
  const editor = document.getElementById("editor");
  editor.innerHTML = `
    <h2>${course} - Week ${week}</h2>
    <div class="lesson-text">${lesson}</div>
    <button onclick="loadQuiz('${course}',${week})">Start Quiz</button>
    <div id="quizArea"></div>
    <hr/>
    <div class="editor-tabs">
      <button onclick="switchEditor('html')">HTML</button>
      <button onclick="switchEditor('css')">CSS</button>
      <button onclick="switchEditor('js')">JavaScript</button>
      <button onclick="switchEditor('python')">Python</button>
    </div>
    <textarea id="html" class="code" placeholder="Write HTML..."></textarea>
    <textarea id="css" class="code" style="display:none" placeholder="Write CSS..."></textarea>
    <textarea id="js" class="code" style="display:none" placeholder="Write JavaScript..."></textarea>
    <textarea id="python" class="code" style="display:none" placeholder="Write Python..."></textarea>
    <button class="run-btn" onclick="runCode()">▶️ Run</button>
    <iframe id="preview"></iframe>
    <pre id="pythonOutput"></pre>
  `;
}

/**
 * 5. Load & Render Quiz
 */
async function loadQuiz(course, week) {
  let res = await fetch(`/quiz/${course}/${week}`);
  let { questions } = await res.json();
  let area = document.getElementById("quizArea");
  area.innerHTML = "";

  questions.forEach((q, i) => {
    let div = document.createElement("div");
    div.className = "quiz-question";
    div.innerHTML = `<p>${i + 1}. ${q.question}</p>`;
    q.options.forEach((opt) => {
      div.innerHTML += `
        <label>
          <input type="radio" name="q${i}" value="${opt}" />
          ${opt}
        </label><br/>
      `;
    });
    area.appendChild(div);
  });

  area.innerHTML += `<button onclick="submitQuiz('${course}',${week}, ${questions.length})">Submit Quiz</button>`;
}

/**
 * 6. Submit Quiz & Record Progress
 */
async function submitQuiz(course, week, total) {
  let correct = 0;
  // gather answers & check
  let res = await fetch(`/quiz/${course}/${week}`);
  let { questions } = await res.json();

  questions.forEach((q, i) => {
    let ans = document.querySelector(`input[name="q${i}"]:checked`);
    if (ans && ans.value === q.answer) correct++;
  });

  let passed = correct / total >= 0.7; // 70% to pass
  await fetch("/progress", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      email: currentUser.email,
      course,
      week,
      passed_quiz: passed,
    }),
  });

  alert(passed ? "Quiz passed! 🎉" : "Quiz failed. Try again.");
  enterCourse(course); // refresh lock states
}

/**
 * 7. Editor Tab Switching
 */
function switchEditor(lang) {
  document.querySelectorAll(".editor-tabs button").forEach((btn) => {
    btn.classList.remove("active");
  });
  document.getElementById(lang).style.display = "block";
  document
    .querySelector(`.editor-tabs button[onclick="switchEditor('${lang}')"]`)
    .classList.add("active");

  // hide other textareas
  ["html", "css", "js", "python"].forEach((l) => {
    if (l !== lang) document.getElementById(l).style.display = "none";
  });
  // default activate first
  if (!document.querySelector(".editor-tabs button.active")) {
    switchEditor("html");
  }
}

/**
 * 8. Run Code Preview
 */
function runCode() {
  const html = document.getElementById("html").value;
  const css = document.getElementById("css").value;
  const js = document.getElementById("js").value;
  const preview = document.getElementById("preview");

  // HTML/CSS/JS in iframe
  const doc = preview.contentDocument || preview.contentWindow.document;
  doc.open();
  doc.write(`
    <style>${css}</style>
    ${html}
    <script>${js}<\/script>
  `);
  doc.close();

  // Python stub (backend not implemented)
  const pyOut = document.getElementById("pythonOutput");
  if (document.getElementById("python").style.display !== "none") {
    pyOut.textContent = "Python execution coming soon!";
  }
}

/**
 * 9. Load Progress Tracker
 */
async function loadProgress() {
  let res = await fetch(`/progress/${currentUser.email}/General`);
  let { progress } = await res.json();
  const tracker = document.getElementById("progressTracker");
  tracker.innerHTML = "";

  progress.forEach((p) => {
    let div = document.createElement("div");
    div.textContent = `Course: ${p.course || "General"}, Week ${p.week} — ${
      p.passed_quiz ? "Passed ✅" : "Failed ❌"
    }`;
    tracker.appendChild(div);
  });
}

/**
 * 10. Load What's New Feed
 */
async function loadNews() {
  // stubbed feed (replace with real endpoint)
  const news = [
    "🎉 New HTML quizzes added!",
    "🔧 Python compiler coming soon.",
    "💡 Check out the updated CSS course."
  ];
  const feed = document.getElementById("newsFeed");
  feed.innerHTML = "";
  news.forEach((msg) => {
    let div = document.createElement("div");
    div.textContent = msg;
    feed.appendChild(div);
  });
    }
